"""
Performance metrics calculator for multi-objective optimization.
"""
import numpy as np
from typing import Dict, Optional
from pymoo.indicators.hv import HV
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """Calculate performance metrics for multi-objective optimization."""

    def __init__(self, reference_point: Optional[np.ndarray] = None, margin: float = 0.1, normalize: bool = True):
        """
        Initialize metrics calculator.

        Args:
            reference_point: Reference point for hypervolume (worst case)
            margin: Fraction to add above the Pareto front maxima if reference_point is None
            normalize: Whether to normalize objectives to [0,1] before HV and spacing
        """
        self.margin = margin
        self.normalize = normalize
        self.reference_point = reference_point  # Can be None, will compute dynamically if needed
        logger.debug(f"Initialized MetricsCalculator with ref_point={self.reference_point}")

    def _spacing(self, pareto_front: np.ndarray) -> float:
        """Calculate spacing metric manually."""
        N = len(pareto_front)
        if N <= 1:
            return 0.0
        distances = []
        for i in range(N):
            others = np.delete(pareto_front, i, axis=0)
            d = np.min(np.linalg.norm(others - pareto_front[i], axis=1))
            distances.append(d)
        distances = np.array(distances)
        s = np.sqrt(np.mean((distances - np.mean(distances)) ** 2))
        return s

    def _compute_reference_point(self, pareto_front: np.ndarray) -> np.ndarray:
        """Compute a safe reference point above the Pareto front maxima."""
        max_values = np.max(pareto_front, axis=0)
        reference_point = max_values * (1 + self.margin)
        logger.debug(f"Computed dynamic reference point: {reference_point}")
        return reference_point

    def _normalize(self, pareto_front: np.ndarray) -> np.ndarray:
        """Normalize Pareto front to [0,1] for each objective."""
        min_vals = np.min(pareto_front, axis=0)
        max_vals = np.max(pareto_front, axis=0)
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1.0  # éviter division par zéro
        normalized_pf = (pareto_front - min_vals) / range_vals
        logger.debug(f"Normalized Pareto front with min {min_vals} and max {max_vals}")
        return normalized_pf

    def calculate_all(self, pareto_front: np.ndarray) -> Dict[str, float]:
        """Calculate all performance metrics."""
        if pareto_front is None or len(pareto_front) == 0:
            logger.warning("Empty Pareto front, cannot calculate metrics")
            return {}

        metrics = {}

        # Normalisation si activée
        pf_for_metrics = self._normalize(pareto_front) if self.normalize else pareto_front

        # Hypervolume
        try:
            if self.reference_point is None:
                ref_point = np.ones(pareto_front.shape[1]) if self.normalize else self._compute_reference_point(pareto_front)
            else:
                ref_point = self.reference_point

            hv_indicator = HV(ref_point=ref_point)
            metrics['hypervolume'] = float(hv_indicator(pf_for_metrics))
            metrics['reference_point'] = ref_point.tolist()
            logger.debug(f"Hypervolume: {metrics['hypervolume']:.4f}")
        except Exception as e:
            logger.warning(f"Failed to calculate Hypervolume: {e}")
            metrics['hypervolume'] = None
            metrics['reference_point'] = None

        # Spacing
        try:
            metrics['spacing'] = self._spacing(pf_for_metrics)
            logger.debug(f"Spacing: {metrics['spacing']:.4f}")
        except Exception as e:
            logger.warning(f"Failed to calculate Spacing: {e}")
            metrics['spacing'] = None

        # Nombre de solutions
        metrics['n_solutions'] = len(pareto_front)

        # Best objectives
        metrics['best_objectives'] = {
            'cost': float(np.min(pareto_front[:, 0])),
            'dissatisfaction': float(np.min(pareto_front[:, 1])),
            'peak_power': float(np.min(pareto_front[:, 2]))
        }

        # Worst objectives
        metrics['worst_objectives'] = {
            'cost': float(np.max(pareto_front[:, 0])),
            'dissatisfaction': float(np.max(pareto_front[:, 1])),
            'peak_power': float(np.max(pareto_front[:, 2]))
        }

        # Mean objectives
        metrics['mean_objectives'] = {
            'cost': float(np.mean(pareto_front[:, 0])),
            'dissatisfaction': float(np.mean(pareto_front[:, 1])),
            'peak_power': float(np.mean(pareto_front[:, 2]))
        }

        # Std objectives
        metrics['std_objectives'] = {
            'cost': float(np.std(pareto_front[:, 0])),
            'dissatisfaction': float(np.std(pareto_front[:, 1])),
            'peak_power': float(np.std(pareto_front[:, 2]))
        }

        return metrics

    def print_summary(self, metrics: Dict[str, float]):
        """Print metrics summary to console."""
        print("\n" + "=" * 70)
        print("  📊 PERFORMANCE METRICS")
        print("=" * 70)

        if metrics.get('hypervolume') is not None:
            print(f"\n  Hypervolume (HV):     {metrics['hypervolume']:.6f}")
        if metrics.get('spacing') is not None:
            print(f"  Spacing (SP):         {metrics['spacing']:.6f}")

        print(f"\n  Solutions in Pareto:  {metrics['n_solutions']}")

        # Best objectives
        print("\n  Best Objectives:")
        for k, v in metrics['best_objectives'].items():
            unit = "€" if k == "cost" else "kW" if k == "peak_power" else ""
            print(f"    {k.replace('_',' ').capitalize():>15}: {v:>8.2f} {unit}")

        # Mean ± Std
        print("\n  Mean ± Std:")
        for k in metrics['mean_objectives']:
            unit = "€" if k == "cost" else "kW" if k == "peak_power" else ""
            print(f"    {k.replace('_',' ').capitalize():>15}: {metrics['mean_objectives'][k]:>8.2f} ± {metrics['std_objectives'][k]:.2f} {unit}")

        print("=" * 70 + "\n")

    def to_dict(self, metrics: Dict[str, float]) -> Dict:
        """Convert metrics to serializable dictionary."""
        return metrics
