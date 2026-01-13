"""
GDE3 Optimization Service implementing IOptimizer.
"""
import numpy as np
from typing import Optional, Dict, Any
from time import time
from pymoo.core.problem import ElementwiseProblem
from pymoode.algorithms import GDE3
from pymoo.optimize import minimize
from pymoo.config import Config

from ..core.interfaces.optimizer import IOptimizer
from ..core.entities.scenario import Scenario
from ..core.models.optimization_result import OptimizationResult, OptimizationMetrics
from ..core.exceptions import OptimizationError
from ..config.logging_config import get_logger
from ..config.settings import settings
from .metrics_calculator import MetricsCalculator

# Disable pymoo compilation warnings
Config.warnings['not_compiled'] = False

logger = get_logger(__name__)


class EVChargingProblem(ElementwiseProblem):
    """
    Multi-objective optimization problem for EV charging.
    
    Objectives:
        1. Minimize cost (electricity cost)
        2. Minimize dissatisfaction (unmet charging needs)
        3. Minimize peak power (grid stress)
    
    Constraints:
        1. Battery SoC must stay between 0% and 100%
        2. Site total power must not exceed maximum
    """
    
    def __init__(self, scenario: Scenario):
        """
        Initialize optimization problem.
        
        Args:
            scenario: Charging scenario
        """
        self.scenario = scenario
        n_vars = len(scenario.vehicles) * scenario.time_horizon
        
        # Power bounds
        xl = settings.charging_power_min
        xu = settings.charging_power_max
        
        super().__init__(
            n_var=n_vars,
            n_obj=3,  # cost, dissatisfaction, peak
            n_ieq_constr=2,  # SoC bounds, site power
            xl=xl,
            xu=xu
        )
        
        logger.debug(f"Initialized problem with {n_vars} variables")
    
    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate objectives and constraints for solution x."""
        # Reshape to matrix (vehicles x hours)
        n_vehicles = len(self.scenario.vehicles)
        t_horizon = self.scenario.time_horizon
        power_matrix = x.reshape((n_vehicles, t_horizon))
        
        # Apply availability mask
        mask = self.scenario.get_availability_mask()
        power_matrix = power_matrix * mask
        
        # Calculate SoC trajectory
        soc_profiles = self._calculate_soc_profiles(power_matrix)
        
        # Objectives
        cost = self._calculate_cost(power_matrix)
        dissatisfaction = self._calculate_dissatisfaction(soc_profiles)
        peak_power = self._calculate_peak_power(power_matrix)
        
        # Constraints
        soc_violation = self._calculate_soc_violation(soc_profiles)
        power_violation = self._calculate_power_violation(power_matrix)
        
        out["F"] = [cost, dissatisfaction, peak_power]
        out["G"] = [soc_violation, power_violation]
    
    def _calculate_soc_profiles(self, power_matrix: np.ndarray) -> np.ndarray:
        """Calculate SoC evolution for all vehicles."""
        battery_capacities = self.scenario.get_battery_capacities()
        soc_initial = self.scenario.get_initial_soc_vector()
        
        # Energy per time step
        energy_step = (power_matrix * settings.dt) / battery_capacities[:, np.newaxis]
        
        # Cumulative SoC
        soc_profiles = np.cumsum(energy_step, axis=1) + soc_initial[:, np.newaxis]
        
        return soc_profiles
    
    def _calculate_cost(self, power_matrix: np.ndarray) -> float:
        """Calculate total electricity cost."""
        total_power = np.sum(power_matrix, axis=0)
        cost = np.sum(total_power * self.scenario.price_profile * settings.dt)
        return float(cost)
    
    def _calculate_dissatisfaction(self, soc_profiles: np.ndarray) -> float:
        """Calculate dissatisfaction (unmet charging needs)."""
        departure_times = self.scenario.get_departure_times()
        target_socs = self.scenario.get_target_soc_vector()
        
        final_socs = np.array([
            soc_profiles[i, min(int(t), self.scenario.time_horizon - 1)]
            for i, t in enumerate(departure_times)
        ])
        
        # Penalize vehicles not reaching target
        shortfall = np.maximum(0, target_socs - final_socs)
        dissatisfaction = np.sum(shortfall)
        
        return float(dissatisfaction)
    
    def _calculate_peak_power(self, power_matrix: np.ndarray) -> float:
        """Calculate peak total power."""
        total_power = np.sum(power_matrix, axis=0)
        peak = np.max(np.abs(total_power))
        return float(peak)
    
    def _calculate_soc_violation(self, soc_profiles: np.ndarray) -> float:
        """Calculate SoC constraint violation."""
        below_zero = np.sum(np.maximum(0, -soc_profiles))
        above_one = np.sum(np.maximum(0, soc_profiles - 1.0))
        return float(below_zero + above_one)
    
    def _calculate_power_violation(self, power_matrix: np.ndarray) -> float:
        """Calculate site power constraint violation."""
        total_power = np.sum(power_matrix, axis=0)
        violation = np.max(np.maximum(0, np.abs(total_power) - self.scenario.site_max_power))
        return float(violation)


class GDE3OptimizerService(IOptimizer):
    """Optimization service using GDE3 algorithm."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize optimizer.
        
        Args:
            config: Optional configuration overrides
        """
        self.config = config or settings.get_optimizer_config()
        logger.info(f"Initialized GDE3 optimizer: {self.config}")
    
    def optimize(
        self,
        scenario: Scenario,
        config: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Optimize charging schedule for scenario.
        
        Args:
            scenario: Charging scenario
            config: Optional config overrides
            
        Returns:
            Optimization result
            
        Raises:
            OptimizationError: If optimization fails
        """
        # Validate scenario
        self.validate_scenario(scenario)
        
        # Use provided config or default
        opt_config = config or self.config
        
        logger.info(f"Starting optimization for scenario: {scenario.name}")
        start_time = time()
        
        try:
            # Create problem
            problem = EVChargingProblem(scenario)
            
            # Create algorithm
            algorithm = GDE3(
                pop_size=opt_config['pop_size'],
                variant=opt_config['variant'],
                CR=opt_config['CR'],
                F=opt_config['F']
            )
            
            # Run optimization
            res = minimize(
                problem,
                algorithm,
                ('n_gen', opt_config['n_gen']),
                seed=1,
                verbose=False
            )
            
            execution_time = time() - start_time
            
            # Check if solutions found
            if res.F is None or len(res.F) == 0:
                raise OptimizationError("No valid solutions found")
            
            # Extract best solution (minimum cost)
            if res.F.ndim > 1:
                best_idx = np.argmin(res.F[:, 0])
                best_objectives = res.F[best_idx]
                best_schedule = res.X[best_idx]
            else:
                best_objectives = res.F
                best_schedule = res.X
            
            # Reshape schedule
            schedule = best_schedule.reshape((len(scenario.vehicles), scenario.time_horizon))
            
            # Create metrics
            metrics = OptimizationMetrics(
                cost=float(best_objectives[0]),
                dissatisfaction=float(best_objectives[1]),
                peak_power=float(best_objectives[2])
            )
            
            # Calculate global metrics
            perf_metrics = {}
            if res.F.ndim > 1:
                try:
                    calculator = MetricsCalculator()
                    perf_metrics = calculator.calculate_all(res.F)
                except Exception as e:
                    logger.warning(f"Could not calculate metrics: {e}")

            # Create result
            result = OptimizationResult(
                metrics=metrics,
                charging_schedule=schedule,
                n_vehicles=len(scenario.vehicles),
                n_hours=scenario.time_horizon,
                solutions_found=len(res.F) if res.F.ndim > 1 else 1,
                execution_time=execution_time,
                converged=True,
                pareto_front=res.F if res.F.ndim > 1 else None,  # Save all Pareto solutions
                performance_metrics=perf_metrics,
                metadata={
                    'algorithm': self.get_algorithm_name(),
                    'config': opt_config,
                    'scenario_name': scenario.name
                }
            )
            
            logger.info(
                f"Optimization completed in {execution_time:.2f}s - "
                f"Cost: {metrics.cost:.2f}, Peak: {metrics.peak_power:.2f}kW"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise OptimizationError(f"Optimization failed: {e}")
    
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        return "GDE3"
    
    def validate_scenario(self, scenario: Scenario) -> bool:
        """Validate scenario."""
        if not scenario.is_feasible():
            raise ValueError("Scenario is not feasible - some vehicles cannot be charged in time")
        
        if not scenario.vehicles:
            raise ValueError("Scenario must have at least one vehicle")
        
        return True
