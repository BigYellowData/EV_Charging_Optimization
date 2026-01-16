"""
Script to visualize Pareto front from optimization results.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import argparse


def load_pareto_front(csv_path: str) -> pd.DataFrame:
    """Load Pareto front data from CSV file."""
    df = pd.read_csv(csv_path)
    print(f"[OK] Loaded {len(df)} Pareto solutions from {csv_path}")
    return df


def plot_pareto_3d(df: pd.DataFrame, save_path: str = None):
    """
    Create 3D scatter plot of Pareto front.

    Args:
        df: DataFrame with columns 'cost', 'dissatisfaction', 'peak_power'
        save_path: Optional path to save the figure
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Extract objectives
    cost = df['cost'].values
    dissatisfaction = df['dissatisfaction'].values
    peak_power = df['peak_power'].values

    # Create color map based on dissatisfaction (gradient)
    colors = plt.cm.viridis(dissatisfaction / dissatisfaction.max())

    # 3D scatter plot
    scatter = ax.scatter(
        cost,
        dissatisfaction,
        peak_power,
        c=dissatisfaction,
        cmap='viridis',
        s=100,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )

    # Labels and title
    ax.set_xlabel('Coût (€)', fontsize=12, labelpad=10)
    ax.set_ylabel('Insatisfaction', fontsize=12, labelpad=10)
    ax.set_zlabel('Puissance de pointe (kW)', fontsize=12, labelpad=10)
    ax.set_title('Front de Pareto - Optimisation de la Recharge des VE',
                 fontsize=14, fontweight='bold', pad=20)

    # Color bar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, aspect=10)
    cbar.set_label('Insatisfaction', fontsize=11)

    # Grid
    ax.grid(True, alpha=0.3)

    # Adjust viewing angle
    ax.view_init(elev=20, azim=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] 3D plot saved to {save_path}")

    plt.show()


def plot_pareto_2d_projections(df: pd.DataFrame, save_path: str = None):
    """
    Create 2D projections of Pareto front (3 subplots).

    Args:
        df: DataFrame with columns 'cost', 'dissatisfaction', 'peak_power'
        save_path: Optional path to save the figure
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    cost = df['cost'].values
    dissatisfaction = df['dissatisfaction'].values
    peak_power = df['peak_power'].values

    # Plot 1: Cost vs Dissatisfaction
    axes[0].scatter(cost, dissatisfaction, c='steelblue', s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    axes[0].set_xlabel('Coût (€)', fontsize=11)
    axes[0].set_ylabel('Insatisfaction', fontsize=11)
    axes[0].set_title('Coût vs Insatisfaction', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Cost vs Peak Power
    axes[1].scatter(cost, peak_power, c='coral', s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    axes[1].set_xlabel('Coût (€)', fontsize=11)
    axes[1].set_ylabel('Puissance de pointe (kW)', fontsize=11)
    axes[1].set_title('Coût vs Puissance de pointe', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Dissatisfaction vs Peak Power
    axes[2].scatter(dissatisfaction, peak_power, c='mediumseagreen', s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    axes[2].set_xlabel('Insatisfaction', fontsize=11)
    axes[2].set_ylabel('Puissance de pointe (kW)', fontsize=11)
    axes[2].set_title('Insatisfaction vs Puissance de pointe', fontsize=12, fontweight='bold')
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('Projections 2D du Front de Pareto', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] 2D projections saved to {save_path}")

    plt.show()


def print_pareto_statistics(df: pd.DataFrame):
    """Print statistics about the Pareto front."""
    print("\n" + "="*60)
    print("STATISTIQUES DU FRONT DE PARETO")
    print("="*60)
    print(f"Nombre de solutions: {len(df)}")
    print("\n--- Coût (€) ---")
    print(f"  Min:    {df['cost'].min():.2f}")
    print(f"  Max:    {df['cost'].max():.2f}")
    print(f"  Moyenne: {df['cost'].mean():.2f}")
    print(f"  Médiane: {df['cost'].median():.2f}")

    print("\n--- Insatisfaction ---")
    print(f"  Min:    {df['dissatisfaction'].min():.4f}")
    print(f"  Max:    {df['dissatisfaction'].max():.4f}")
    print(f"  Moyenne: {df['dissatisfaction'].mean():.4f}")
    print(f"  Médiane: {df['dissatisfaction'].median():.4f}")

    print("\n--- Puissance de pointe (kW) ---")
    print(f"  Min:    {df['peak_power'].min():.2f}")
    print(f"  Max:    {df['peak_power'].max():.2f}")
    print(f"  Moyenne: {df['peak_power'].mean():.2f}")
    print(f"  Médiane: {df['peak_power'].median():.2f}")

    # Best solutions for each objective
    print("\n--- Solutions optimales par objectif ---")
    best_cost_idx = df['cost'].idxmin()
    print(f"  Meilleur coût: Solution #{best_cost_idx}")
    print(f"    Coût: {df.loc[best_cost_idx, 'cost']:.2f} €")
    print(f"    Insatisfaction: {df.loc[best_cost_idx, 'dissatisfaction']:.4f}")
    print(f"    Puissance: {df.loc[best_cost_idx, 'peak_power']:.2f} kW")

    best_dissatisfaction_idx = df['dissatisfaction'].idxmin()
    print(f"\n  Meilleure insatisfaction: Solution #{best_dissatisfaction_idx}")
    print(f"    Coût: {df.loc[best_dissatisfaction_idx, 'cost']:.2f} €")
    print(f"    Insatisfaction: {df.loc[best_dissatisfaction_idx, 'dissatisfaction']:.4f}")
    print(f"    Puissance: {df.loc[best_dissatisfaction_idx, 'peak_power']:.2f} kW")

    best_peak_idx = df['peak_power'].idxmin()
    print(f"\n  Meilleure puissance de pointe: Solution #{best_peak_idx}")
    print(f"    Coût: {df.loc[best_peak_idx, 'cost']:.2f} €")
    print(f"    Insatisfaction: {df.loc[best_peak_idx, 'dissatisfaction']:.4f}")
    print(f"    Puissance: {df.loc[best_peak_idx, 'peak_power']:.2f} kW")

    print("="*60 + "\n")


def find_latest_pareto_file(results_dir: str = "results") -> str:
    """Find the most recent Pareto front CSV file."""
    results_path = Path(results_dir)
    pareto_files = list(results_path.glob("pareto_front_*.csv"))

    if not pareto_files:
        raise FileNotFoundError(f"No Pareto front files found in {results_dir}/")

    # Sort by modification time
    latest_file = max(pareto_files, key=lambda p: p.stat().st_mtime)
    return str(latest_file)


def main():
    """Main visualization script."""
    parser = argparse.ArgumentParser(
        description="Visualize Pareto front from EV charging optimization"
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to Pareto front CSV file (default: latest in results/)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/plots',
        help='Directory to save plots (default: results/plots/)'
    )
    parser.add_argument(
        '--no-show',
        action='store_true',
        help='Do not display plots (only save them)'
    )

    args = parser.parse_args()

    # Find input file
    if args.file:
        csv_path = args.file
    else:
        csv_path = find_latest_pareto_file()
        print(f"Using latest Pareto front file: {csv_path}\n")

    # Load data
    df = load_pareto_front(csv_path)

    # Print statistics
    print_pareto_statistics(df)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for output files
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create plots
    print("Generating visualizations...")

    # 3D plot
    plot_3d_path = output_dir / f"pareto_3d_{timestamp}.png"
    if args.no_show:
        # Save without showing
        import matplotlib
        matplotlib.use('Agg')

    plot_pareto_3d(df, save_path=str(plot_3d_path))

    # 2D projections
    plot_2d_path = output_dir / f"pareto_2d_{timestamp}.png"
    plot_pareto_2d_projections(df, save_path=str(plot_2d_path))

    print(f"\n[OK] All visualizations completed!")


if __name__ == "__main__":
    main()
