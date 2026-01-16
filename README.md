# 🚗 EV Charging Optimizer

Optimiseur de charge pour véhicules électriques utilisant l'algorithme **MODE** (Multi-Objective Differential Evolution) pour optimiser simultanément :
1. **Coût de l'électricité** (Profit V2G)
2. **Satisfaction utilisateur** (État de charge au départ)
3. **Pic de puissance** (Stress sur le réseau)

## 📚 Contexte Académique

Ce projet implémente la **même modélisation mathématique** que l'article de [Qian et al. (2023)](https://arxiv.org/abs/2308.08792) sur le contrôle de charge V2G/G2V, mais utilise une **métaheuristique différente** :

- **Article original** : FedSAC (Federated Soft Actor-Critic) - apprentissage par renforcement
- **Notre approche** : MODE (Multi-Objective Differential Evolution) - algorithme évolutionnaire

Cette adaptation permet d'obtenir un **front de Pareto complet** avec 100 solutions non-dominées.

## ✨ Fonctionnalités

- **Données Réelles** : Intégration complète avec l'API Caltech ACN-Data
- **Optimisation Multi-Objectifs** : Utilisation de MODE pour trouver le front de Pareto optimal
- **Docker-Only** : Aucune installation locale requise (sauf Docker)
- **Mode Interactif** : Menu convivial pour explorer les dates et configurer l'optimisation
- **Métriques Automatiques** : Calcul d'Hypervolume et Spacing (métriques de qualité)
- **Configuration Flexible** : Tout est paramétrable via `.env`
- **V2G Support** : Support bidirectionnel (charge et décharge)

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose

### 1. Configuration
Copiez le fichier d'exemple et ajoutez votre clé API Caltech (si vous en avez une) :
```bash
cp .env.example .env
# Éditez .env avec votre clé API
```

### 2. Mode Interactif (Recommandé)
Le moyen le plus simple de lancer une optimisation :
```bash
docker-compose run --rm optimizer-interactive
```
- 📅 Visualisez les dates disponibles
- 🚙 Choisissez le nombre de véhicules
- ⚙️ Configurez la puissance du site
- 🔧 Ajustez les paramètres MODE

### 3. Mode Automatique (Production)
Pour des exécutions répétées avec les paramètres du `.env` :
```bash
docker-compose --profile prod up optimizer-real
```

## 📊 Résultats

Les résultats sont sauvegardés dans le dossier `results/` :

- **`result_*.json`** : Résumé de la meilleure solution et métadonnées
- **`schedule_*.csv`** : Planning de charge détaillé (Véhicule x Heure)
- **`pareto_front_*.csv`** : Les 100 solutions du front de Pareto
- **`metrics/metrics_*.json`** : Métriques de performance (Hypervolume, Spacing)

### Exemple de Résultats (Caltech 2019-07-15, 30 véhicules)
```
======================================================================
  📊 PERFORMANCE METRICS
======================================================================
  Hypervolume (HV):     0.7276    (73% de couverture - Excellent)
  Spacing (SP):         0.0312    (Distribution uniforme - Excellent)
  Solutions in Pareto:  100

  Best Objectives:
    Cost:               -4.50 €   (Profit V2G !)
    Dissatisfaction:     2.76     (~9% d'écart par véhicule)
    Peak Power:         14.07 kW  (23% de la capacité site)

  Execution Time:       30.71 s
======================================================================
```

## ⚙️ Configuration (.env)

Tous les paramètres sont ajustables dans le fichier `.env` :

### Données
| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `CALTECH_SITE` | Site ACN-Data (caltech, jpl, office001) | caltech |
| `CALTECH_DATE` | Date d'optimisation (YYYY-MM-DD) | 2019-07-15 |
| `CALTECH_LIMIT` | Nombre max de véhicules | 30 |

### Contraintes physiques
| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `SITE_MAX_POWER` | Puissance max du transformateur (kW) | 60.0 |
| `BATTERY_CAPACITY` | Capacité batterie par défaut (kWh) | 30.0 |
| `CHARGING_POWER_MIN` | Puissance min V2G (kW) | -6.0 |
| `CHARGING_POWER_MAX` | Puissance max charge (kW) | 30.0 |

### Algorithme MODE
| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `MODE_N_GEN` | Nombre de générations | 1500 |
| `MODE_POP_SIZE` | Taille de la population | 100 |
| `MODE_VARIANT` | Variante DE | DE/rand/1/bin |
| `MODE_CR` | Taux de croisement | 0.9 |
| `MODE_F` | Facteur de mutation | 0.5 |

## 🛠️ Développement

Pour reconstruire l'image Docker après modification du code :
```bash
docker-compose build
```

## 📁 Structure du Projet

```
.
├── docker-compose.yml      # Orchestration Docker
├── Dockerfile              # Environnement Python
├── .env                    # Configuration (API, Paramètres)
├── RAPPORT_COMPLET.tex     # Rapport LaTeX complet
├── src/                    # Code source
│   ├── cli/                # Interface ligne de commande & Interactive
│   ├── core/               # Modèles et Logique métier
│   ├── services/           # Algorithme MODE & Métriques
│   └── infrastructure/     # API Caltech & Cache
├── results/                # Résultats d'optimisation
│   ├── *.json              # Fichiers de résultats
│   ├── *.csv               # Plannings et front de Pareto
│   └── metrics/            # Métriques de performance
└── analysis_output/        # Visualisations (PNG)
```

## 📖 Références

- **Qian, J., et al. (2023)** - Federated Reinforcement Learning for Electric Vehicles Charging Control on Distribution Networks. [arXiv:2308.08792](https://arxiv.org/abs/2308.08792)
- **Storn, R., & Price, K. (1997)** - Differential evolution. Journal of global optimization, 11(4), 341-359.
- **Caltech ACN-Data** - https://ev.caltech.edu/

## 📈 Métriques de Qualité

### Hypervolume (HV)
Mesure le volume de l'espace des objectifs dominé par le front de Pareto. Plus élevé = meilleure couverture.

### Spacing (SP)
Mesure l'uniformité de la distribution des solutions. Plus faible = distribution plus uniforme.

## 🎓 Utilisation Académique

Ce projet a été développé dans un cadre académique. Le rapport complet est disponible dans `RAPPORT_COMPLET.tex` avec :
- Formulation mathématique détaillée
- Analyse des résultats
- Interprétation des métriques HV et SP
- Comparaison avec l'approche FedSAC

---

**License** : MIT
**Author** : [Votre Nom]
**Version** : 2.0.0
