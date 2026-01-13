"""
Performance metrics calculator for multi-objective optimization.
"""
import numpy as np
from typing import Dict, Optional
from pymoo.indicators.hv import HV
# from pymoo.indicators.spacing import Spacing  # Removed due to import error
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """Calculate performance metrics for multi-objective optimization."""
    
    def __init__(self, reference_point: Optional[np.ndarray] = None):
        """
        Initialize metrics calculator.
        
        Args:
            reference_point: Reference point for hypervolume (worst case)
                           Default: [100.0, 10.0, 100.0] for [cost, dissatisfaction, peak]
        """
        if reference_point is None:
            # Default reference point (worst case scenario)
            self.reference_point = np.array([100.0, 10.0, 100.0])
        else:
            self.reference_point = reference_point
        
        logger.debug(f"Initialized MetricsCalculator with ref_point={self.reference_point}")
    
    def calculate_all(self, pareto_front: np.ndarray) -> Dict[str, float]:
        """
        Calculate all performance metrics.
        
        Args:
            pareto_front: Pareto front objectives (N x 3: cost, dissatisfaction, peak_power)
            
        Returns:
            Dictionary with all metrics
        """
        if pareto_front is None or len(pareto_front) == 0:
            logger.warning("Empty Pareto front, cannot calculate metrics")
            return {}
        
        metrics = {}
        
        # 1. Hypervolume
        try:
            hv_indicator = HV(ref_point=self.reference_point)
            metrics['hypervolume'] = float(hv_indicator(pareto_front))
            logger.debug(f"Hypervolume: {metrics['hypervolume']:.4f}")
        except Exception as e:
            logger.warning(f"Failed to calculate Hypervolume: {e}")
            metrics['hypervolume'] = None
        
        # 2. Spacing (Disabled)
        metrics['spacing'] = None
        
        # 3. Number of solutions
        metrics['n_solutions'] = len(pareto_front)
        
        # 4. Best objectives
        metrics['best_cost'] = float(np.min(pareto_front[:, 0]))
        metrics['best_dissatisfaction'] = float(np.min(pareto_front[:, 1]))
        metrics['best_peak_power'] = float(np.min(pareto_front[:, 2]))
        
        # 5. Worst objectives
        metrics['worst_cost'] = float(np.max(pareto_front[:, 0]))
        metrics['worst_dissatisfaction'] = float(np.max(pareto_front[:, 1]))
        metrics['worst_peak_power'] = float(np.max(pareto_front[:, 2]))
        
        # 6. Mean objectives
        metrics['mean_cost'] = float(np.mean(pareto_front[:, 0]))
        metrics['mean_dissatisfaction'] = float(np.mean(pareto_front[:, 1]))
        metrics['mean_peak_power'] = float(np.mean(pareto_front[:, 2]))
        
        # 7. Standard deviation
        metrics['std_cost'] = float(np.std(pareto_front[:, 0]))
        metrics['std_dissatisfaction'] = float(np.std(pareto_front[:, 1]))
        metrics['std_peak_power'] = float(np.std(pareto_front[:, 2]))
        
        return metrics
    
    def print_summary(self, metrics: Dict[str, float]):
        """
        Print metrics summary to console.
        
        Args:
            metrics: Dictionary of calculated metrics
        """
        print("\n" + "="*70)
        print("  📊 PERFORMANCE METRICS")
        print("="*70)
        
        # Main indicators
        if metrics.get('hypervolume') is not None:
            print(f"\n  Hypervolume (HV):     {metrics['hypervolume']:.6f}")
        if metrics.get('spacing') is not None:
            print(f"  Spacing (SP):         {metrics['spacing']:.6f}")
        
        print(f"\n  Solutions in Pareto:  {metrics['n_solutions']}")
        
        # Best objectives
        print("\n  Best Objectives:")
        print(f"    Cost:               {metrics['best_cost']:>8.2f} €")
        print(f"    Dissatisfaction:    {metrics['best_dissatisfaction']:>8.4f}")
        print(f"    Peak Power:         {metrics['best_peak_power']:>8.2f} kW")
        
        # Statistics
        print("\n  Mean ± Std:")
        print(f"    Cost:               {metrics['mean_cost']:>8.2f} ± {metrics['std_cost']:.2f}")
        print(f"    Dissatisfaction:    {metrics['mean_dissatisfaction']:>8.4f} ± {metrics['std_dissatisfaction']:.4f}")
        print(f"    Peak Power:         {metrics['mean_peak_power']:>8.2f} ± {metrics['std_peak_power']:.2f}")
        
        print("="*70 + "\n")
    
    def to_dict(self, metrics: Dict[str, float]) -> Dict:
        """
        Convert metrics to serializable dictionary.
        
        Args:
            metrics: Raw metrics
            
        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            'hypervolume': metrics.get('hypervolume'),
            'spacing': metrics.get('spacing'),
            'n_solutions': metrics.get('n_solutions'),
            'best_objectives': {
                'cost': metrics.get('best_cost'),
                'dissatisfaction': metrics.get('best_dissatisfaction'),
                'peak_power': metrics.get('best_peak_power')
            },
            'worst_objectives': {
                'cost': metrics.get('worst_cost'),
                'dissatisfaction': metrics.get('worst_dissatisfaction'),
                'peak_power': metrics.get('worst_peak_power')
            },
            'mean_objectives': {
                'cost': metrics.get('mean_cost'),
                'dissatisfaction': metrics.get('mean_dissatisfaction'),
                'peak_power': metrics.get('mean_peak_power')
            },
            'std_objectives': {
                'cost': metrics.get('std_cost'),
                'dissatisfaction': metrics.get('std_dissatisfaction'),
                'peak_power': metrics.get('std_peak_power')
            },
            'reference_point': self.reference_point.tolist()
        }
