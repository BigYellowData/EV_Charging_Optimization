"""
Optimize charging use case - orchestrates the optimization workflow.
"""
from datetime import date, timedelta
from typing import Optional
from pathlib import Path

from ...core.interfaces.optimizer import IOptimizer
from ...core.interfaces.data_source import IDataSource, ISyntheticDataSource
from ...core.interfaces.cache import ICache
from ...core.models.optimization_result import OptimizationResult
from ...core.entities.scenario import Scenario
from ...config.logging_config import get_logger

logger = get_logger(__name__)


class OptimizeChargingUseCase:
    """
    Use case for optimizing EV charging schedules.
    Coordinates data fetching, scenario building, and optimization.
    """
    
    def __init__(
        self,
        optimizer: IOptimizer,
        real_data_source: Optional[IDataSource] = None,
        synthetic_data_source: Optional[ISyntheticDataSource] = None,
        cache: Optional[ICache] = None
    ):
        """
        Initialize use case.
        
        Args:
            optimizer: Optimization engine
            real_data_source: Real data repository (Caltech)
            synthetic_data_source: Synthetic data generator
            cache: Cache implementation
        """
        self.optimizer = optimizer
        self.real_data_source = real_data_source
        self.synthetic_data_source = synthetic_data_source
        self.cache = cache
    
    def execute_real_data(
        self,
        start_date: date,
        site: str = "caltech",
        site_max_power: float = 60.0,
        limit: Optional[int] = None,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> OptimizationResult:
        """
        Execute optimization with real Caltech data.
        
        Args:
            start_date: Date to fetch data for
            site: Site identifier
            site_max_power: Maximum site power
            limit: Limit number of vehicles
            save_results: Whether to save results to files
            output_dir: Directory for output files
            
        Returns:
            Optimization result
        """
        if not self.real_data_source:
            raise ValueError("Real data source not configured")
        
        logger.info(f"Executing optimization with real data: {site} - {start_date}")
        
        # Check cache
        cache_key = f"scenario_{site}_{start_date}_{limit or 'all'}"
        scenario = None
        
        if self.cache:
            cached_scenario = self.cache.get(cache_key)
            if cached_scenario:
                logger.info("Using cached scenario")
                scenario = cached_scenario
        
        # Fetch and build scenario if not cached
        if scenario is None:
            # Fetch sessions
            sessions = self.real_data_source.fetch_sessions(
                start_date=start_date,
                site=site,
                limit=limit
            )
            
            # Build scenario
            scenario = self.real_data_source.build_scenario(
                sessions=sessions,
                site_max_power=site_max_power
            )
            
            # Cache scenario
            if self.cache:
                self.cache.set(cache_key, scenario, ttl=timedelta(hours=24))
        
        # Optimize
        result = self.optimizer.optimize(scenario)
        
        # Save results
        if save_results:
            self._save_results(result, output_dir or Path("results"))
        
        return result
    
    def execute_synthetic(
        self,
        n_vehicles: int = 30,
        time_horizon: int = 24,
        site_max_power: float = 60.0,
        seed: Optional[int] = 42,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> OptimizationResult:
        """
        Execute optimization with synthetic data.
        
        Args:
            n_vehicles: Number of vehicles
            time_horizon: Planning horizon
            site_max_power: Maximum site power
            seed: Random seed
            save_results: Whether to save results
            output_dir: Directory for output files
            
        Returns:
            Optimization result
        """
        if not self.synthetic_data_source:
            raise ValueError("Synthetic data source not configured")
        
        logger.info(f"Executing optimization with synthetic data: {n_vehicles} vehicles")
        
        # Generate scenario
        scenario = self.synthetic_data_source.generate_scenario(
            n_vehicles=n_vehicles,
            time_horizon=time_horizon,
            site_max_power=site_max_power,
            seed=seed
        )
        
        # Optimize
        result = self.optimizer.optimize(scenario)
        
        # Save results
        if save_results:
            self._save_results(result, output_dir or Path("results"))
        
        return result
    
    def _save_results(self, result: OptimizationResult, output_dir: Path):
        """Save optimization results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON summary
        json_path = output_dir / f"result_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        result.to_json(str(json_path))
        logger.info(f"Saved result to {json_path}")
        
        # Save schedule CSV
        csv_path = output_dir / f"schedule_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
        result.save_schedule_csv(str(csv_path))
        logger.info(f"Saved schedule to {csv_path}")
        
        # Save Pareto front if available
        if result.pareto_front is not None:
            pareto_path = output_dir / f"pareto_front_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            result.save_pareto_front_csv(str(pareto_path))
            logger.info(f"Saved Pareto front ({len(result.pareto_front)} solutions) to {pareto_path}")

        # Save performance metrics
        if result.performance_metrics:
            metrics_dir = output_dir / "metrics"
            metrics_dir.mkdir(exist_ok=True)
            
            metrics_path = metrics_dir / f"metrics_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(metrics_path, 'w') as f:
                import json
                json.dump(result.performance_metrics, f, indent=2)
            logger.info(f"Saved metrics to {metrics_path}")
            
            # Print summary to console
            try:
                from ...services.metrics_calculator import MetricsCalculator
                MetricsCalculator().print_summary(result.performance_metrics)
            except ImportError:
                pass
