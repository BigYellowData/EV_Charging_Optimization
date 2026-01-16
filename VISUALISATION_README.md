# Visualisation du Front de Pareto

Ce document explique comment générer et analyser les graphiques du front de Pareto pour l'optimisation de la recharge des véhicules électriques.

## Fichiers disponibles

### Scripts de visualisation

1. **`visualize_pareto.py`** - Script Python en ligne de commande
2. **`visualize_pareto.ipynb`** - Notebook Jupyter interactif (recommandé)

## Utilisation

### Option 1: Script Python (ligne de commande)

Le script génère automatiquement les graphiques à partir du fichier Pareto le plus récent:

```bash
# Utiliser le fichier Pareto le plus récent
python visualize_pareto.py

# Spécifier un fichier Pareto spécifique
python visualize_pareto.py --file results/pareto_front_20260113_210811.csv

# Sauvegarder sans afficher les graphiques
python visualize_pareto.py --no-show

# Spécifier le répertoire de sortie
python visualize_pareto.py --output-dir results/my_plots
```

**Chemins Python sous Windows:**
```bash
"C:\Users\Utilisateur\AppData\Local\Programs\Python\Python39\python.exe" visualize_pareto.py
```

### Option 2: Notebook Jupyter (recommandé)

Ouvrez `visualize_pareto.ipynb` dans:
- **Jupyter Notebook**: `jupyter notebook visualize_pareto.ipynb`
- **VSCode**: Ouvrir le fichier directement et exécuter les cellules
- **Jupyter Lab**: `jupyter lab visualize_pareto.ipynb`

Avantages du notebook:
- Visualisation interactive
- Analyse étape par étape
- Possibilité de modifier les graphiques en temps réel
- Statistiques détaillées affichées dans le notebook

## Graphiques générés

Les scripts génèrent automatiquement 4 types de visualisations:

### 1. Graphique 3D du Front de Pareto
**Fichier**: `pareto_3d_YYYYMMDD_HHMMSS.png`

Affiche les 3 objectifs simultanément:
- Axe X: Coût (€)
- Axe Y: Insatisfaction
- Axe Z: Puissance de pointe (kW)
- Couleur: Gradient basé sur l'insatisfaction

### 2. Projections 2D
**Fichier**: `pareto_2d_YYYYMMDD_HHMMSS.png`

3 graphiques montrant les compromis entre paires d'objectifs:
- Coût vs Insatisfaction
- Coût vs Puissance de pointe
- Insatisfaction vs Puissance de pointe

### 3. Distributions (notebook uniquement)
**Fichier**: `pareto_distributions_YYYYMMDD_HHMMSS.png`

Histogrammes montrant la distribution des solutions pour chaque objectif:
- Distribution du coût
- Distribution de l'insatisfaction
- Distribution de la puissance de pointe

### 4. Matrice de corrélation (notebook uniquement)
**Fichier**: `pareto_correlations_YYYYMMDD_HHMMSS.png`

Heatmap montrant les corrélations entre les objectifs.

## Statistiques affichées

Les scripts affichent automatiquement:

```
STATISTIQUES DU FRONT DE PARETO
- Nombre de solutions Pareto
- Pour chaque objectif (Coût, Insatisfaction, Puissance):
  - Minimum
  - Maximum
  - Moyenne
  - Médiane
- Solutions optimales par objectif:
  - Meilleur coût
  - Meilleure insatisfaction
  - Meilleure puissance de pointe
```

## Interprétation des résultats

### Front de Pareto

Le front de Pareto représente l'ensemble des solutions **non-dominées**. Une solution est non-dominée si aucune autre solution n'est meilleure sur tous les objectifs simultanément.

### Compromis (Trade-offs)

- **Coût bas ↔ Insatisfaction élevée**: Recharger aux heures creuses (moins cher) peut ne pas satisfaire tous les besoins
- **Puissance faible ↔ Coût élevé**: Lisser la charge réduit le pic mais peut coûter plus cher
- **Insatisfaction faible ↔ Puissance élevée**: Charger rapidement pour satisfaire tout le monde augmente le pic

### Choix de solution

Selon les priorités de l'opérateur:

1. **Priorité: Minimiser les coûts**
   - Choisir la solution avec le coût minimal
   - Accepter plus d'insatisfaction et un pic potentiellement plus élevé

2. **Priorité: Satisfaction des utilisateurs**
   - Choisir la solution avec insatisfaction minimale
   - Coûts et pics seront plus élevés

3. **Priorité: Stabilité du réseau**
   - Choisir la solution avec puissance de pointe minimale
   - Compromis sur coût et satisfaction

4. **Approche équilibrée**
   - Choisir une solution au centre du front de Pareto
   - Compromis raisonnable sur tous les objectifs

## Exemple de sortie

```bash
$ python visualize_pareto.py

Using latest Pareto front file: results/pareto_front_20260113_210811.csv

[OK] Loaded 100 Pareto solutions from results/pareto_front_20260113_210811.csv

============================================================
STATISTIQUES DU FRONT DE PARETO
============================================================
Nombre de solutions: 100

--- Coût (€) ---
  Min:    -0.98
  Max:    54.86
  Moyenne: 21.74
  Médiane: 19.89

--- Insatisfaction ---
  Min:    2.8826
  Max:    6.2303
  Moyenne: 4.0621
  Médiane: 3.8362

--- Puissance de pointe (kW) ---
  Min:    13.34
  Max:    46.96
  Moyenne: 27.55
  Médiane: 26.30

--- Solutions optimales par objectif ---
  Meilleur coût: Solution #2
    Coût: -0.98 €
    Insatisfaction: 5.6190
    Puissance: 31.68 kW

  Meilleure insatisfaction: Solution #1
    Coût: 54.86 €
    Insatisfaction: 2.8826
    Puissance: 46.96 kW

  Meilleure puissance de pointe: Solution #0
    Coût: 5.56 €
    Insatisfaction: 5.9776
    Puissance: 13.34 kW
============================================================

Generating visualizations...
[OK] 3D plot saved to results/plots/pareto_3d_20260115_231336.png
[OK] 2D projections saved to results/plots/pareto_2d_20260115_231336.png

[OK] All visualizations completed!
```

## Dépendances Python

Les scripts nécessitent les bibliothèques suivantes:

```bash
pip install pandas numpy matplotlib
```

Ces bibliothèques sont déjà incluses dans `requirements.txt` du projet principal.

## Résolution de problèmes

### Erreur: "No Pareto front files found"
- Vérifiez que vous avez exécuté une optimisation auparavant
- Les fichiers doivent être dans `results/pareto_front_*.csv`

### Erreur: "Module not found"
```bash
pip install pandas numpy matplotlib
```

### Les graphiques ne s'affichent pas
- Utilisez l'option `--no-show` pour sauvegarder uniquement
- Vérifiez que votre environnement supporte l'affichage graphique
- Utilisez le notebook Jupyter dans VSCode pour une meilleure expérience

### Problèmes d'encodage sous Windows
- Le script a été mis à jour pour éviter les caractères Unicode spéciaux
- Si le problème persiste, utilisez le notebook Jupyter

## Contact et support

Pour toute question ou problème, consultez la documentation principale du projet ou créez une issue sur GitHub.
