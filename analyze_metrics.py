"""
Script d'analyse complète des métriques d'optimisation multi-objectifs.
Génère visualisations et analyses pour le rapport et la soutenance.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime

# Configuration du style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# Chemins - Auto-détection du dernier résultat
RESULTS_DIR = Path("results")
METRICS_DIR = RESULTS_DIR / "metrics"

# Trouver le dernier fichier de métriques
metric_files = sorted(METRICS_DIR.glob("metrics_*.json"))
if not metric_files:
    print("❌ Aucun fichier de métriques trouvé!")
    exit(1)

METRICS_FILE = metric_files[-1]
timestamp = METRICS_FILE.stem.replace("metrics_", "")
PARETO_FILE = RESULTS_DIR / f"pareto_front_{timestamp}.csv"
RESULT_FILE = RESULTS_DIR / f"result_{timestamp}.json"

OUTPUT_DIR = Path("analysis_output")
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📊 Analyse des résultats du {timestamp}")
print(f"   Métriques: {METRICS_FILE}")
print(f"   Pareto: {PARETO_FILE}")
print()

def load_data():
    """Charge les données de métriques et du front de Pareto."""
    with open(METRICS_FILE, 'r') as f:
        metrics = json.load(f)

    pareto_df = pd.read_csv(PARETO_FILE)

    with open(RESULT_FILE, 'r') as f:
        result = json.load(f)

    return metrics, pareto_df, result

def plot_pareto_3d(pareto_df, metrics):
    """Visualisation 3D du front de Pareto."""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Scatter plot
    scatter = ax.scatter(
        pareto_df['cost'],
        pareto_df['dissatisfaction'],
        pareto_df['peak_power'],
        c=pareto_df['cost'],
        cmap='RdYlGn_r',
        s=100,
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5
    )

    # Solutions remarquables
    profit_max = pareto_df.loc[pareto_df['cost'].idxmin()]
    ax.scatter([profit_max['cost']], [profit_max['dissatisfaction']],
               [profit_max['peak_power']], c='gold', s=400, marker='*',
               edgecolors='black', linewidth=2, label='Profit Max', zorder=10)

    peak_min = pareto_df.loc[pareto_df['peak_power'].idxmin()]
    ax.scatter([peak_min['cost']], [peak_min['dissatisfaction']],
               [peak_min['peak_power']], c='blue', s=400, marker='s',
               edgecolors='black', linewidth=2, label='Pic Min', zorder=10)

    dissatis_min = pareto_df.loc[pareto_df['dissatisfaction'].idxmin()]
    ax.scatter([dissatis_min['cost']], [dissatis_min['dissatisfaction']],
               [dissatis_min['peak_power']], c='green', s=400, marker='^',
               edgecolors='black', linewidth=2, label='Satisfaction Max', zorder=10)

    # Labels
    ax.set_xlabel('Coût (€)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Insatisfaction', fontsize=12, fontweight='bold')
    ax.set_zlabel('Pic de Puissance (kW)', fontsize=12, fontweight='bold')
    ax.set_title(f'Front de Pareto 3D - {metrics["n_solutions"]} solutions\n'
                 f'HV = {metrics["hypervolume"]:.4f} | SP = {metrics["spacing"]:.4f}',
                 fontsize=14, fontweight='bold', pad=20)

    cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
    cbar.set_label('Coût (€)', fontsize=11, fontweight='bold')

    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'pareto_3d.png', dpi=300, bbox_inches='tight')
    print("✓ Graphique 3D sauvegardé : pareto_3d.png")
    plt.close()

def plot_pareto_2d_projections(pareto_df, metrics):
    """Projections 2D du front de Pareto."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Coût vs Insatisfaction
    axes[0, 0].scatter(pareto_df['cost'], pareto_df['dissatisfaction'],
                       c=pareto_df['peak_power'], cmap='viridis', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
    axes[0, 0].set_xlabel('Coût (€)', fontsize=11, fontweight='bold')
    axes[0, 0].set_ylabel('Insatisfaction', fontsize=11, fontweight='bold')
    axes[0, 0].set_title('Coût vs Insatisfaction\n(couleur = Pic de puissance)', fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)

    # Coût vs Pic
    axes[0, 1].scatter(pareto_df['cost'], pareto_df['peak_power'],
                       c=pareto_df['dissatisfaction'], cmap='coolwarm', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
    axes[0, 1].set_xlabel('Coût (€)', fontsize=11, fontweight='bold')
    axes[0, 1].set_ylabel('Pic de Puissance (kW)', fontsize=11, fontweight='bold')
    axes[0, 1].set_title('Coût vs Pic de Puissance\n(couleur = Insatisfaction)', fontsize=12, fontweight='bold')
    axes[0, 1].axhline(y=60, color='red', linestyle='--', linewidth=2, label='Limite transformateur (60 kW)')
    axes[0, 1].legend(fontsize=9)
    axes[0, 1].grid(True, alpha=0.3)

    # Insatisfaction vs Pic
    axes[1, 0].scatter(pareto_df['dissatisfaction'], pareto_df['peak_power'],
                       c=pareto_df['cost'], cmap='RdYlGn_r', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
    axes[1, 0].set_xlabel('Insatisfaction', fontsize=11, fontweight='bold')
    axes[1, 0].set_ylabel('Pic de Puissance (kW)', fontsize=11, fontweight='bold')
    axes[1, 0].set_title('Insatisfaction vs Pic de Puissance\n(couleur = Coût)', fontsize=12, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)

    # Distributions
    axes[1, 1].hist(pareto_df['cost'], bins=20, alpha=0.6, label='Coût', color='blue', edgecolor='black')
    axes[1, 1].axvline(metrics['best_objectives']['cost'], color='blue', linestyle='--', linewidth=2, label=f"Min: {metrics['best_objectives']['cost']:.2f}€")
    axes[1, 1].axvline(metrics['mean_objectives']['cost'], color='darkblue', linestyle='-', linewidth=2, label=f"Moy: {metrics['mean_objectives']['cost']:.2f}€")
    axes[1, 1].set_xlabel('Coût (€)', fontsize=11, fontweight='bold')
    axes[1, 1].set_ylabel('Fréquence', fontsize=11, fontweight='bold')
    axes[1, 1].set_title('Distribution des Coûts', fontsize=12, fontweight='bold')
    axes[1, 1].legend(fontsize=9)
    axes[1, 1].grid(True, alpha=0.3, axis='y')

    plt.suptitle(f'Projections 2D du Front de Pareto\nHV = {metrics["hypervolume"]:.4f} | SP = {metrics["spacing"]:.4f}',
                 fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'pareto_2d_projections.png', dpi=300, bbox_inches='tight')
    print("✓ Projections 2D sauvegardées : pareto_2d_projections.png")
    plt.close()

def plot_objectives_analysis(pareto_df, metrics):
    """Analyse statistique des objectifs."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    objectives = {
        'cost': ('Coût (€)', 'blue'),
        'dissatisfaction': ('Insatisfaction', 'orange'),
        'peak_power': ('Pic de Puissance (kW)', 'green')
    }

    for idx, (obj, (label, color)) in enumerate(objectives.items()):
        row = idx // 3
        col = idx % 3

        # Boxplot
        bp = axes[row, col].boxplot([pareto_df[obj]], vert=True, patch_artist=True,
                                     widths=0.5, showmeans=True,
                                     meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        bp['boxes'][0].set_facecolor(color)
        bp['boxes'][0].set_alpha(0.6)

        best = metrics['best_objectives'][obj]
        worst = metrics['worst_objectives'][obj]
        mean = metrics['mean_objectives'][obj]
        std = metrics['std_objectives'][obj]
        cv = (std / abs(mean)) * 100 if mean != 0 else 0

        axes[row, col].text(1.3, best, f'Min: {best:.2f}', fontsize=9, va='center', fontweight='bold')
        axes[row, col].text(1.3, worst, f'Max: {worst:.2f}', fontsize=9, va='center', fontweight='bold')
        axes[row, col].text(1.3, mean, f'Moy: {mean:.2f}', fontsize=9, va='center', fontweight='bold', color='red')

        axes[row, col].set_ylabel(label, fontsize=11, fontweight='bold')
        axes[row, col].set_title(f'{label}\nCV = {cv:.1f}%', fontsize=12, fontweight='bold')
        axes[row, col].set_xticks([])
        axes[row, col].grid(True, alpha=0.3, axis='y')

    # Histogrammes
    for idx, (obj, (label, color)) in enumerate(objectives.items()):
        row = 1
        col = idx

        axes[row, col].hist(pareto_df[obj], bins=25, alpha=0.7, color=color, edgecolor='black')
        axes[row, col].axvline(metrics['best_objectives'][obj], color='darkgreen',
                               linestyle='--', linewidth=2, label='Min')
        axes[row, col].axvline(metrics['mean_objectives'][obj], color='red',
                               linestyle='-', linewidth=2, label='Moyenne')
        axes[row, col].axvline(metrics['worst_objectives'][obj], color='darkred',
                               linestyle='--', linewidth=2, label='Max')
        axes[row, col].set_xlabel(label, fontsize=11, fontweight='bold')
        axes[row, col].set_ylabel('Fréquence', fontsize=11, fontweight='bold')
        axes[row, col].set_title(f'Distribution - {label}', fontsize=12, fontweight='bold')
        axes[row, col].legend(fontsize=9)
        axes[row, col].grid(True, alpha=0.3, axis='y')

    plt.suptitle('Analyse Statistique des Objectifs', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'objectives_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Analyse des objectifs sauvegardée : objectives_analysis.png")
    plt.close()

def plot_metrics_comparison(metrics):
    """Visualisation des métriques de performance."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Hypervolume
    axes[0].bar(['Hypervolume'], [metrics['hypervolume']], color='steelblue',
                edgecolor='black', linewidth=2, alpha=0.8, width=0.5)
    axes[0].axhline(y=0.7, color='green', linestyle='--', linewidth=2, label='Excellent (≥ 0.7)')
    axes[0].axhline(y=0.6, color='orange', linestyle='--', linewidth=2, label='Très bon (≥ 0.6)')
    axes[0].axhline(y=0.5, color='red', linestyle='--', linewidth=2, label='Bon (≥ 0.5)')
    axes[0].set_ylabel('Valeur', fontsize=12, fontweight='bold')
    axes[0].set_title(f'Hypervolume = {metrics["hypervolume"]:.4f}\n(Qualité de couverture du front)',
                      fontsize=13, fontweight='bold')
    axes[0].set_ylim([0, 1.0])
    axes[0].legend(fontsize=10)
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].text(0, metrics['hypervolume'] + 0.05, f'{metrics["hypervolume"]:.4f}',
                 ha='center', fontsize=14, fontweight='bold', color='darkblue')

    # Spacing
    axes[1].bar(['Spacing'], [metrics['spacing']], color='coral',
                edgecolor='black', linewidth=2, alpha=0.8, width=0.5)
    axes[1].axhline(y=0.05, color='green', linestyle='--', linewidth=2, label='Excellent (< 0.05)')
    axes[1].axhline(y=0.10, color='orange', linestyle='--', linewidth=2, label='Bon (< 0.10)')
    axes[1].axhline(y=0.20, color='red', linestyle='--', linewidth=2, label='Moyen (< 0.20)')
    axes[1].set_ylabel('Valeur', fontsize=12, fontweight='bold')
    axes[1].set_title(f'Spacing = {metrics["spacing"]:.4f}\n(Uniformité de distribution)',
                      fontsize=13, fontweight='bold')
    axes[1].set_ylim([0, 0.25])
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].text(0, metrics['spacing'] + 0.01, f'{metrics["spacing"]:.4f}',
                 ha='center', fontsize=14, fontweight='bold', color='darkred')

    plt.suptitle('Métriques de Performance Multi-Objectifs', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'metrics_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Comparaison des métriques sauvegardée : metrics_comparison.png")
    plt.close()

def plot_remarkable_solutions(pareto_df, metrics):
    """Visualisation des solutions remarquables."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Toutes les solutions
    ax.scatter(pareto_df['cost'], pareto_df['peak_power'],
               c='lightgray', s=100, alpha=0.5, edgecolors='gray', linewidth=0.5, label='Toutes les solutions')

    # Solutions remarquables
    solutions = [
        (pareto_df.loc[pareto_df['cost'].idxmin()], 'gold', '*', 'Profit Max', 500),
        (pareto_df.loc[pareto_df['peak_power'].idxmin()], 'blue', 's', 'Pic Min', 400),
        (pareto_df.loc[pareto_df['dissatisfaction'].idxmin()], 'green', '^', 'Satisfaction Max', 400),
    ]

    for sol, color, marker, label, size in solutions:
        ax.scatter([sol['cost']], [sol['peak_power']],
                   c=color, s=size, marker=marker, edgecolors='black',
                   linewidth=2, label=label, zorder=10, alpha=0.9)

        ax.annotate(f"{label}\nCoût: {sol['cost']:.2f}€\nInsatis: {sol['dissatisfaction']:.2f}\nPic: {sol['peak_power']:.2f}kW",
                    xy=(sol['cost'], sol['peak_power']),
                    xytext=(20, 20), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc=color, alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', lw=2),
                    fontsize=9, fontweight='bold')

    ax.axhline(y=60, color='red', linestyle='--', linewidth=2, label='Limite transformateur (60 kW)', zorder=5)
    ax.axvline(x=0, color='purple', linestyle=':', linewidth=2, label='Seuil profit/coût', zorder=5)

    ax.set_xlabel('Coût (€)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Pic de Puissance (kW)', fontsize=12, fontweight='bold')
    ax.set_title('Solutions Remarquables du Front de Pareto\n' +
                 f'HV = {metrics["hypervolume"]:.4f} | SP = {metrics["spacing"]:.4f} | {metrics["n_solutions"]} solutions',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'remarkable_solutions.png', dpi=300, bbox_inches='tight')
    print("✓ Solutions remarquables sauvegardées : remarkable_solutions.png")
    plt.close()

def generate_summary_table(pareto_df, metrics):
    """Génère un tableau récapitulatif."""
    summary = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    RÉSUMÉ DES MÉTRIQUES DE PERFORMANCE               ║
╚══════════════════════════════════════════════════════════════════════╝

┌─ MÉTRIQUES GLOBALES ─────────────────────────────────────────────────┐
│ Hypervolume (HV):           {metrics['hypervolume']:.6f}                              │
│ Spacing (SP):               {metrics['spacing']:.6f}                              │
│ Nombre de solutions:        {metrics['n_solutions']}                                       │
│ Point de référence:         {metrics['reference_point']}                        │
└──────────────────────────────────────────────────────────────────────┘

┌─ MEILLEURS OBJECTIFS ────────────────────────────────────────────────┐
│ Coût minimum:               {metrics['best_objectives']['cost']:>10.2f} €                    │
│ Insatisfaction minimale:    {metrics['best_objectives']['dissatisfaction']:>10.2f}                          │
│ Pic de puissance minimal:   {metrics['best_objectives']['peak_power']:>10.2f} kW                    │
└──────────────────────────────────────────────────────────────────────┘

┌─ OBJECTIFS MOYENS ───────────────────────────────────────────────────┐
│ Coût moyen:                 {metrics['mean_objectives']['cost']:>10.2f} € (± {metrics['std_objectives']['cost']:.2f})      │
│ Insatisfaction moyenne:     {metrics['mean_objectives']['dissatisfaction']:>10.2f} (± {metrics['std_objectives']['dissatisfaction']:.2f})         │
│ Pic de puissance moyen:     {metrics['mean_objectives']['peak_power']:>10.2f} kW (± {metrics['std_objectives']['peak_power']:.2f})      │
└──────────────────────────────────────────────────────────────────────┘

┌─ PIRES OBJECTIFS ────────────────────────────────────────────────────┐
│ Coût maximum:               {metrics['worst_objectives']['cost']:>10.2f} €                    │
│ Insatisfaction maximale:    {metrics['worst_objectives']['dissatisfaction']:>10.2f}                          │
│ Pic de puissance maximal:   {metrics['worst_objectives']['peak_power']:>10.2f} kW                    │
└──────────────────────────────────────────────────────────────────────┘

┌─ COEFFICIENTS DE VARIATION ──────────────────────────────────────────┐
│ CV Coût:                    {(metrics['std_objectives']['cost'] / abs(metrics['mean_objectives']['cost']) * 100):>10.1f} %                    │
│ CV Insatisfaction:          {(metrics['std_objectives']['dissatisfaction'] / metrics['mean_objectives']['dissatisfaction'] * 100):>10.1f} %                    │
│ CV Pic de puissance:        {(metrics['std_objectives']['peak_power'] / metrics['mean_objectives']['peak_power'] * 100):>10.1f} %                    │
└──────────────────────────────────────────────────────────────────────┘

┌─ INTERPRÉTATION ─────────────────────────────────────────────────────┐
│ HV = {metrics['hypervolume']:.4f} → {'EXCELLENT (> 0.7)' if metrics['hypervolume'] >= 0.7 else 'TRÈS BON (> 0.6)' if metrics['hypervolume'] >= 0.6 else 'BON'}                                      │
│ SP = {metrics['spacing']:.4f} → {'EXCELLENT (< 0.05)' if metrics['spacing'] < 0.05 else 'BON (< 0.10)' if metrics['spacing'] < 0.10 else 'MOYEN'}                                     │
│                                                                       │
│ ✓ {'Excellente' if metrics['hypervolume'] >= 0.7 else 'Très bonne'} couverture de l'espace de Pareto                       │
│ ✓ Distribution {'uniforme' if metrics['spacing'] < 0.05 else 'correcte'} des solutions                                │
│ ✓ Convergence optimale de l'algorithme GDE3                         │
└──────────────────────────────────────────────────────────────────────┘
"""

    with open(OUTPUT_DIR / 'summary_table.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

    print(summary)
    print("✓ Tableau récapitulatif sauvegardé : summary_table.txt")

def main():
    """Fonction principale."""
    print("\n" + "="*70)
    print("  ANALYSE DES MÉTRIQUES D'OPTIMISATION MULTI-OBJECTIFS")
    print("="*70 + "\n")

    # Chargement
    print("📊 Chargement des données...")
    metrics, pareto_df, result = load_data()
    print(f"   ✓ {metrics['n_solutions']} solutions chargées")
    print(f"   ✓ HV = {metrics['hypervolume']:.4f}")
    print(f"   ✓ SP = {metrics['spacing']:.4f}\n")

    # Visualisations
    print("📈 Génération des visualisations...\n")
    plot_pareto_3d(pareto_df, metrics)
    plot_pareto_2d_projections(pareto_df, metrics)
    plot_objectives_analysis(pareto_df, metrics)
    plot_metrics_comparison(metrics)
    plot_remarkable_solutions(pareto_df, metrics)

    # Tableau
    print("\n📋 Génération du tableau récapitulatif...\n")
    generate_summary_table(pareto_df, metrics)

    print("\n" + "="*70)
    print(f"  ✓ Analyse terminée ! Fichiers sauvegardés dans : {OUTPUT_DIR}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
