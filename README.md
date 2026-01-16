# 🚗 EV Charging Optimizer

Optimiseur de charge pour véhicules électriques utilisant l'algorithme génétique GDE3 (Generalized Differential Evolution 3) pour optimiser simultanément :
1. **Coût de l'électricité** (Profit V2G)
2. **Satisfaction utilisateur** (État de charge au départ)
3. **Pic de puissance** (Stress sur le réseau)

## ✨ Fonctionnalités

- **Données Réelles** : Intégration complète avec l'API Caltech ACN-Data.
- **Optimisation Multi-Objectifs** : Utilisation de GDE3 pour trouver le front de Pareto optimal.
- **Docker-Only** : Aucune installation locale requise (sauf Docker).
- **Mode Interactif** : Menu convivial pour explorer les dates et configurer l'optimisation.
- **Métriques Automatiques** : Calcul d'Hypervolume et statistiques de performance.
- **Configuration Flexible** : Tout est paramétrable via `.env`.

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

### 3. Mode Automatique (Production)
Pour des exécutions répétées avec les paramètres du `.env` :
```bash
docker-compose --profile prod up optimizer-real
```

## 📊 Résultats

Les résultats sont sauvegardés dans le dossier `results/` :

- **`result_*.json`** : Résumé de la meilleure solution et métadonnées.
- **`schedule_*.csv`** : Planning de charge détaillé (Véhicule x Heure).
- **`pareto_front_*.csv`** : Les solutions du front de Pareto (pour analyse).
- **`metrics/metrics_*.json`** : Métriques de performance (Hypervolume, Spacing).

### Exemple de Métriques (Terminal)
```
======================================================================
  📊 PERFORMANCE METRICS
======================================================================
  Hypervolume (HV):     0.854321
  Solutions in Pareto:  100

  Best Objectives:
    Cost:               -18.81 €
    Dissatisfaction:    5.5339
    Peak Power:         26.84 kW
```

## ⚙️ Configuration (.env)

Tous les paramètres sont ajustables dans le fichier `.env` :

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `CALTECH_SITE` | Site ACN-Data (caltech, jpl, office001) | caltech |
| `CALTECH_DATE` | Date d'optimisation (YYYY-MM-DD) | 2019-07-15 |
| `CALTECH_LIMIT` | Nombre max de véhicules | 30 |
| `SITE_MAX_POWER` | Puissance max du transformateur (kW) | 60.0 |
| `GDE3_N_GEN` | Nombre de générations | 1500 |
| `GDE3_POP_SIZE` | Taille de la population | 100 |

## 🛠️ Développement

Pour reconstruire l'image Docker après modification du code :
```bash
docker-compose build
```

## 📁 Structure du Projet

```
.
├── docker-compose.yml   # Orchestration Docker
├── Dockerfile           # Environnement Python
├── .env                 # Configuration (API, Paramètres)
├── src/                 # Code source
│   ├── cli/             # Interface ligne de commande & Interactive
│   ├── core/            # Modèles et Logique métier
│   ├── services/        # Algorithme GDE3 & Métriques
│   └── infrastructure/  # API Caltech & Cache
└── results/             # Sorties (JSON, CSV)
```
