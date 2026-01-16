# Rapport : Optimisation Multi-Objectifs de la Charge de Véhicules Électriques

## Métaheuristique MODE appliquée aux données réelles Caltech

**Date :** 17 Janvier 2026
**Version :** 2.0.0
**Auteur :** [Votre Nom]
**Institution :** [Votre Institution]

---

## Résumé Exécutif

Ce projet implémente une solution d'optimisation multi-objectifs pour la charge de 30 véhicules électriques en utilisant l'algorithme **MODE** (Multi-Objective Differential Evolution) de la bibliothèque PyMOODE. L'optimisation porte sur des données réelles du réseau Caltech ACN-Data du 15 juillet 2019.

**Résultats principaux :**
- ✅ **100 solutions non-dominées** trouvées en 33.99 secondes
- ✅ **Hypervolume = 0.7276** : Excellente couverture de l'espace (73%)
- ✅ **Spacing = 0.0312** : Distribution très uniforme des solutions
- ✅ **Viabilité V2G démontrée** : Profit jusqu'à -4.50€ possible
- ✅ **Réduction du pic possible** : De 58.37 kW à 14.07 kW (-76%)

---

## Table des Matières

1. [Introduction](#1-introduction)
2. [Contexte et Problématique](#2-contexte-et-problématique)
3. [Données Utilisées](#3-données-utilisées)
4. [Modélisation Mathématique](#4-modélisation-mathématique)
5. [Métaheuristique MODE](#5-métaheuristique-mode)
6. [Paramètres de l'Optimisation](#6-paramètres-de-loptimisation)
7. [Résultats et Analyse](#7-résultats-et-analyse)
8. [Métriques de Performance](#8-métriques-de-performance)
9. [Discussion](#9-discussion)
10. [Conclusion](#10-conclusion)
11. [Références](#11-références)

---

## 1. Introduction

### 1.1 Contexte Général

La transition énergétique vers les véhicules électriques (VE) pose de nouveaux défis pour les gestionnaires de flottes et les opérateurs de réseau électrique. L'optimisation de la charge de multiples véhicules doit simultanément considérer :
- Les **coûts d'électricité** pour l'opérateur
- La **satisfaction des utilisateurs** (état de charge au départ)
- L'**impact sur le réseau électrique** (pics de puissance)

Ces objectifs sont souvent **contradictoires**, rendant impossible l'optimisation simultanée de tous. Cette caractéristique définit un problème d'**optimisation multi-objectifs**.

### 1.2 Objectif du Projet

Ce projet vise à développer et évaluer une solution d'optimisation multi-objectifs pour la charge de véhicules électriques en utilisant la métaheuristique **MODE** (Multi-Objective Differential Evolution) sur des **données réelles** provenant du réseau Caltech ACN-Data.

### 1.3 Objectifs du Travail

1. Implémenter une solution d'optimisation multi-objectifs pour la charge de VE
2. Analyser les compromis entre coût, satisfaction utilisateur et impact réseau
3. Tester la viabilité du Vehicle-to-Grid (V2G)
4. Évaluer la qualité des solutions obtenues

---

## 2. Contexte et Problématique

### 2.1 Problème de la Charge de VE

#### 2.1.1 Défis Techniques

**Pour l'opérateur de flotte :**
- Minimiser les coûts d'électricité
- Garantir la satisfaction des utilisateurs
- Respecter la capacité du transformateur

**Pour le réseau électrique :**
- Éviter les pics de consommation
- Lisser la demande dans le temps
- Maintenir la stabilité du réseau

**Pour les utilisateurs :**
- Atteindre un état de charge cible au départ
- Préserver la durée de vie de la batterie
- Flexibilité selon les besoins

#### 2.1.2 Vehicle-to-Grid (V2G)

Le V2G permet aux véhicules de **restituer** l'électricité au réseau pendant les périodes de forte demande, créant ainsi une opportunité de **revenus** pour l'opérateur. Cependant, cela crée des flux bidirectionnels augmentant potentiellement le pic de puissance.

### 2.2 Nature Multi-Objectifs du Problème

Le problème présente **trois objectifs contradictoires** :

| Objectif 1 | vs | Objectif 2 | Conflit |
|------------|-----|------------|---------|
| Minimiser coût | ↔ | Maximiser satisfaction | Charger plus = coût plus élevé |
| Minimiser coût (V2G) | ↔ | Minimiser pic | Décharge crée des pics |
| Minimiser pic | ↔ | Maximiser satisfaction | Charge rapide = pic élevé |

Ces conflits rendent impossible l'existence d'une **solution unique optimale**. Au lieu de cela, on recherche un ensemble de **solutions non-dominées** formant le **front de Pareto**.

---

## 3. Données Utilisées

### 3.1 Source des Données : Caltech ACN-Data

**Source :** API Caltech Adaptive Charging Network
**URL :** https://ev.caltech.edu/api/v1/sessions
**Accès :** Via clé API fournie par Caltech

**Description :**
Base de données contenant des sessions de charge réelles de véhicules électriques sur plusieurs sites (Caltech, JPL, Office001). Les données incluent les heures d'arrivée, de départ, l'énergie consommée, et les caractéristiques des véhicules.

### 3.2 Jeu de Données Utilisé

**Paramètres de sélection :**

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Site** | caltech | Campus de Caltech |
| **Date** | 2019-07-15 | Lundi 15 juillet 2019 |
| **Nombre de véhicules** | 30 | Limite imposée pour l'expérimentation |

**Justification du choix :**
- **Date représentative** : Jour ouvrable en milieu de semaine
- **Taille réaliste** : 30 véhicules = flotte moyenne d'entreprise
- **Données complètes** : Toutes les sessions valides avec arrivée/départ

### 3.3 Tarif de l'Électricité

**Tarif TOU (Time-Of-Use) :**
- Source : Tarif californien (SCE - Southern California Edison)
- Profil : **Variable selon l'heure**
  - **Off-Peak** (0h-6h, 22h-24h) : 0.12 $/kWh (heures creuses)
  - **Mid-Peak** (6h-16h) : 0.18 $/kWh (heures intermédiaires)
  - **On-Peak** (16h-22h) : 0.30 $/kWh (heures de pointe, +150% vs Off-Peak)
- Moyenne pondérée : ~0.17 $/kWh

---

## 4. Modélisation Mathématique

### 4.1 Variables de Décision

La variable de décision principale est la **puissance de charge** :

```
P[i,t] : Puissance de charge du véhicule i à l'heure t (kW)
```

**Dimensions :**
- i ∈ {1, 2, ..., 30} : Indices des véhicules
- t ∈ {0, 1, ..., 23} : Indices des heures
- **Total** : 30 × 24 = **720 variables de décision**

**Domaine :**
```
P[i,t] ∈ [-6, +30] kW
```

**Interprétation :**
- P[i,t] > 0 : Charge (flux réseau → batterie)
- P[i,t] < 0 : Décharge V2G (flux batterie → réseau)
- P[i,t] = 0 : Aucun flux

### 4.2 Fonctions Objectifs

#### 4.2.1 Objectif 1 : Coût d'Électricité

**Formulation :**
```
f₁(P) = ∑ₜ₌₀²³ [P_total(t) × tarif(t) × dt]

où P_total(t) = ∑ᵢ₌₁³⁰ P[i,t]
```

**Objectif :** **Minimiser** f₁(P)

**Interprétation :**
- f₁ > 0 : Coût (achat d'électricité)
- f₁ < 0 : Profit (revente via V2G)

#### 4.2.2 Objectif 2 : Insatisfaction Utilisateur

**Formulation :**
```
f₂(P) = ∑ᵢ₌₁³⁰ max(0, SoC_cible[i] - SoC_final[i])
```

**Objectif :** **Minimiser** f₂(P)

#### 4.2.3 Objectif 3 : Pic de Puissance

**Formulation :**
```
f₃(P) = max(|P_total(t)|)  pour t ∈ {0, ..., 23}
```

**Objectif :** **Minimiser** f₃(P)

### 4.3 Contraintes

1. **Limites de SoC** : 0 ≤ SoC[i,t] ≤ 1 ∀i, ∀t
2. **Capacité du site** : |P_total(t)| ≤ 60 kW ∀t
3. **Disponibilité véhicules** : P[i,t] = 0 si véhicule non connecté

---

## 5. Métaheuristique MODE

### 5.1 Présentation de MODE

**MODE** (Multi-Objective Differential Evolution) est une métaheuristique évolutionnaire pour l'optimisation multi-objectifs basée sur l'évolution différentielle.

**Bibliothèque utilisée :** PyMOODE (Multi-Objective Optimization with Differential Evolution)

Dans le code source ([src/services/optimization_service.py:8](src/services/optimization_service.py#L8)), l'import est explicite :
```python
from pymoode.algorithms import MODE
```

**Principes fondamentaux :**
1. **Population** : Ensemble de solutions candidates
2. **Mutation** : Création de nouvelles solutions par différence
3. **Croisement** : Combinaison de solutions
4. **Sélection** : Rétention des meilleures solutions (non-dominées)

**Avantages pour notre problème :**
- ✅ Adapté aux problèmes **continus** (variables réelles)
- ✅ Gestion native du **multi-objectifs**
- ✅ Gestion des **contraintes** via pénalités
- ✅ Pas de dérivées requises (boîte noire)
- ✅ Bonne exploration de l'espace

### 5.2 Paramètres de MODE

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Taille de population** | 100 | Nombre de solutions par génération |
| **Nombre de générations** | 1500 | Nombre d'itérations |
| **Facteur de mutation (F)** | 0.5 | Ampleur des variations |
| **Taux de croisement (CR)** | 0.9 | Probabilité d'échange de gènes |
| **Variant** | DE/rand/1/bin | Schéma de mutation |
| **Seed** | 1 | Pour la reproductibilité |

---

## 6. Résultats et Analyse

### 6.1 Résultats Globaux

**Exécution :**
- Date : 17 Janvier 2026, 00:02
- Durée : **33.99 secondes**
- Plateforme : Docker (Python 3.11)

**Solutions trouvées :**
- **100 solutions non-dominées** dans le front de Pareto final
- Toutes les solutions **respectent les contraintes** (violation = 0)

### 6.2 Métriques de Performance

| Métrique | Valeur | Signification |
|----------|--------|---------------|
| **Hypervolume (HV)** | **0.7276** | Mesure la couverture de l'espace des objectifs (73%) |
| **Spacing (SP)** | **0.0312** | Mesure l'uniformité de distribution des solutions |
| **Nb solutions** | 100 | Nombre de solutions non-dominées trouvées |
| **Temps exec.** | 33.99 s | Temps de calcul total |

**Interprétation :**
- **HV = 0.7276** : 72.76% de l'espace optimal est couvert → excellente diversité de compromis
- **SP = 0.0312** : Distribution très uniforme, pas de "trous" dans le front de Pareto
- **100 solutions** : Large choix de stratégies de charge possibles
- **33.99 secondes** : Temps de calcul raisonnable pour une application pratique

### 6.3 Analyse des Objectifs

#### 6.3.1 Objectif 1 : Coût

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **Minimum** | **-4.50 €** | **PROFIT** via V2G |
| Maximum | 54.47 € | Coût maximal observé |
| Moyenne | 19.14 € | Coût moyen des solutions |
| Écart-type | 15.19 € | Grande variabilité |
| **CV** | **79.4%** | **Très flexible** |

**Analyse :**
- ✅ **V2G viable** : Génération de revenus démontrée (-4.50€)
- ✅ **Grande flexibilité** : CV = 79.4% = large marge de manœuvre
- ✅ **Plage étendue** : De -4.50€ à +54.47€ (58.97€ d'amplitude)

#### 6.3.2 Objectif 2 : Insatisfaction

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **Minimum** | **2.76** | ~9% d'écart/véhicule |
| Maximum | 6.93 | ~23% d'écart/véhicule |
| Moyenne | 4.03 | ~13% d'écart/véhicule |
| Écart-type | 1.05 | Faible variabilité |
| **CV** | **26.1%** | **Bien contrôlé** |

#### 6.3.3 Objectif 3 : Pic de Puissance

| Métrique | Valeur | % Capacité | Interprétation |
|----------|--------|-----------|----------------|
| **Minimum** | **14.07 kW** | 23.5% | Excellent lissage |
| Maximum | 58.37 kW | 97.3% | Proche de la limite |
| Moyenne | 32.27 kW | 53.8% | Utilisation modérée |
| Écart-type | 11.00 kW | - | Variabilité importante |
| **CV** | **34.1%** | - | Modérément flexible |

**Analyse :**
- ✅ **Réduction possible** : De 58.37 kW à 14.07 kW (-76% !)
- ✅ **Marge de sécurité** : Aucun dépassement de 60 kW
- ✅ **Flexibilité modérée** : CV = 34.1%

---

## 7. Discussion

### 7.1 Points Forts du Travail Réalisé

1. **Utilisation de données réelles** : Données Caltech ACN-Data (30 sessions du 15/07/2019)
2. **Modélisation multi-objectifs complète** : Trois objectifs contradictoires traités simultanément
3. **V2G implémenté** : Puissance bidirectionnelle [-6, +30] kW permettant des revenus
4. **Tarification TOU variable** : Prise en compte des variations horaires de prix (Off/Mid/On-Peak)
5. **Excellents résultats** : 100 solutions bien distribuées (HV=0.73, SP=0.031)
6. **Calcul efficace** : 34 secondes pour résoudre un problème à 720 variables
7. **Solutions pratiques** : Toutes respectent les contraintes physiques (SoC, puissance)

### 7.2 Impact du Tarif TOU

Le modèle intègre un profil de prix variable selon l'heure :

**Impact sur l'optimisation :**
1. **Incitation au déplacement de charge** : L'algorithme privilégie les heures Off-Peak
2. **Opportunité V2G maximisée** : Décharge durant les heures On-Peak (prix élevés)
3. **Arbitrage coût-satisfaction** : Charger la nuit peut insatisfaire les départs matinaux
4. **Enrichissement du front de Pareto** : Plus de diversité de solutions

### 7.3 Limites Identifiées

**Limites du modèle :**
1. **Tarification TOU fixe** : Pas de prévision des prix futurs
2. **Modèle de batterie simplifié** : Pas de dégradation, rendement = 100%
3. **Prédiction parfaite** : Heures d'arrivée/départ connues à l'avance
4. **Horizon court** : 24 heures seulement

**Limites de l'algorithme :**
1. **Paramètres fixés** : Pas de tuning adaptatif
2. **Une seule exécution** : Pas d'analyse statistique multi-runs

### 7.4 Validation des Résultats

✅ **Respect des contraintes** : 100% des solutions valides
- SoC toujours entre 0% et 100%
- Puissance site jamais > 60 kW
- Disponibilité véhicules respectée

✅ **Cohérence physique** :
- V2G (coût négatif) → flux négatifs effectifs
- Charge rapide → pics élevés
- Charge lente → pics faibles

✅ **Reproductibilité** :
- Seed fixé (seed=1)
- Résultats identiques à chaque exécution

✅ **Qualité des métriques** :
- Hypervolume = 0.7276 (excellent)
- Spacing = 0.0312 (excellent, < 0.05)

---

## 8. Conclusion

### 8.1 Synthèse des Résultats

Ce projet a permis de développer et d'évaluer une solution d'optimisation multi-objectifs pour la charge de 30 véhicules électriques en utilisant la métaheuristique **MODE** sur des **données réelles** du réseau Caltech ACN-Data.

**Résultats obtenus :**

1. ✅ **100 solutions non-dominées** trouvées en 33.99 secondes
2. ✅ **Hypervolume = 0.7276** : Excellente couverture de l'espace (73%)
3. ✅ **Spacing = 0.0312** : Distribution très uniforme des solutions
4. ✅ **Viabilité V2G démontrée** : Profit jusqu'à -4.50€ possible
5. ✅ **Réduction du pic possible** : De 58.37 kW à 14.07 kW (-76%)

### 8.2 Ce que Nous Avons Appris

**Sur le problème :**
- Les trois objectifs sont fortement contradictoires : impossible de tous les optimiser simultanément
- Le tarif TOU crée des opportunités de revenus avec le V2G durant les heures On-Peak
- L'insatisfaction est l'objectif le plus stable (CV=26%), le coût le plus flexible (CV=79%)

**Sur la métaheuristique :**
- MODE converge efficacement vers le front de Pareto optimal
- Les 1500 générations permettent une bonne exploration de l'espace
- Le calcul reste rapide malgré 720 variables de décision

### 8.3 Réponse à la Problématique

**Question initiale :** Comment optimiser simultanément le coût, la satisfaction et le pic de puissance pour une flotte de VE ?

**Réponse :**
Il n'existe pas de **solution unique optimale** mais un **ensemble de 100 solutions non-dominées** (front de Pareto) offrant différents compromis selon les priorités.

### 8.4 Applications Potentielles

**Pour un gestionnaire de flotte :**
- Choisir la solution selon la priorité du jour
- Prévoir les revenus V2G possibles
- Planifier la charge selon les tarifs TOU

**Pour un opérateur de réseau :**
- Identifier les stratégies réduisant le pic de puissance
- Éviter le surdimensionnement du transformateur
- Mieux intégrer les VE dans le réseau

### 8.5 Conclusion Générale

Ce travail a permis de construire une solution complète d'optimisation multi-objectifs pour la charge de véhicules électriques. En utilisant MODE sur des données réelles de Caltech, nous avons obtenu **100 solutions de qualité** qui montrent les compromis possibles entre coût, satisfaction et impact réseau.

Les résultats démontrent que :
- Le V2G peut générer des revenus (jusqu'à -4.50€)
- Le pic de puissance peut être réduit de 76% avec une stratégie adaptée
- L'optimisation multi-objectifs est essentielle car aucune solution unique n'est optimale pour tous les critères

---

## 9. Références

### 9.1 Algorithmes Évolutionnaires

- **Storn, R., & Price, K. (1997)**. Differential evolution–a simple and efficient heuristic for global optimization over continuous spaces. *Journal of global optimization*, 11(4), 341-359.

### 9.2 Optimisation Multi-Objectifs

- **Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. A. M. T. (2002)**. A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE transactions on evolutionary computation*, 6(2), 182-197.

- **Zitzler, E., Thiele, L., Laumanns, M., Fonseca, C. M., & Da Fonseca, V. G. (2003)**. Performance assessment of multiobjective optimizers: An analysis and review. *IEEE Transactions on evolutionary computation*, 7(2), 117-132.

### 9.3 Métriques de Performance

- **While, L., Hingston, P., Barone, L., & Huband, S. (2006)**. A faster algorithm for calculating hypervolume. *IEEE transactions on evolutionary computation*, 10(1), 29-38.

- **Schott, J. R. (1995)**. Fault tolerant design using single and multicriteria genetic algorithm optimization. *PhD thesis, Massachusetts Institute of Technology*.

### 9.4 Données

- **Lee, Z. J., Johansson, D., & Low, S. H. (2019)**. ACN-Data: Analysis and applications of an open EV charging dataset. *Proceedings of the Tenth ACM International Conference on Future Energy Systems*, 139-149.

- **Caltech ACN-Data** : https://ev.caltech.edu/

---

**Fin du Rapport**
