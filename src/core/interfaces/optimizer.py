"""
Optimizer interface for different optimization strategies.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..entities.scenario import Scenario
from ..models.optimization_result import OptimizationResult


class IOptimizer(ABC):
    """Interface for optimization algorithms."""
    
    @abstractmethod
    def optimize(
        self,
        scenario: Scenario,
        config: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Optimize charging schedule for given scenario.
        
        Args:
            scenario: Charging scenario to optimize
            config: Optional optimizer configuration
            
        Returns:
            Optimization result with schedule and metrics
            
        Raises:
            OptimizationError: If optimization fails
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Get name of the optimization algorithm."""
        pass
    
    @abstractmethod
    def validate_scenario(self, scenario: Scenario) -> bool:
        """
        Validate that scenario is compatible with this optimizer.
        
        Args:
            scenario: Scenario to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If scenario is invalid
        """
        pass
