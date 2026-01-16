# Optimisation Multi-Objectifs de la Charge de Véhicules Électriques

**Métaheuristique MODE - Données réelles Caltech**

**Date :** 17 Janvier 2026
**Auteur :** [Votre Nom]

---

## 1. Le Problème

### 1.1 Qu'est-ce qu'on veut faire ?

Optimiser la charge de **30 véhicules électriques** en considérant **3 objectifs contradictoires** :

1. **Minimiser le coût** d'électricité (ou même générer des revenus avec V2G)
2. **Minimiser l'insatisfaction** des utilisateurs (atteindre le SoC cible)
3. **Minimiser le pic de puissance** (impact sur le réseau électrique)

### 1.2 Pourquoi c'est compliqué ?

Ces trois objectifs sont **contradictoires** :
- Charger vite pour satisfaire → Coûte cher + Crée des pics
- Charger peu cher (la nuit) → Insatisfait ceux qui partent tôt
- Décharger pour gagner de l'argent (V2G) → Crée des pics

**Conclusion :** Il n'existe pas UNE solution optimale, mais un **ensemble de solutions** (front de Pareto).

---

## 2. Les Données

### 2.1 Source
- **Caltech ACN-Data** : Données réelles de charge de VE
- **Date :** 15 juillet 2019 (un lundi normal)
- **Véhicules :** 30 sessions de charge réelles

### 2.2 Tarif électricité (TOU - Time of Use)

Le prix varie selon l'heure :
- **Heures creuses** (0h-6h, 22h-24h) : 0.12 $/kWh
- **Heures moyennes** (6h-16h) : 0.18 $/kWh
- **Heures de pointe** (16h-22h) : 0.30 $/kWh (×2.5 plus cher !)

**Impact :** L'algorithme va naturellement privilégier la charge la nuit et la décharge (V2G) aux heures de pointe.

---

## 3. Le Modèle Mathématique

### 3.1 Variable de décision

**P[i,t]** = Puissance de charge du véhicule i à l'heure t (en kW)

- **i** : véhicule (1 à 30)
- **t** : heure (0 à 23)
- **Total :** 30 × 24 = **720 variables**

**Valeurs possibles :**
- P > 0 : Charge (réseau → batterie)
- P < 0 : Décharge V2G (batterie → réseau)
- P = 0 : Rien

**Limites :** -6 kW ≤ P ≤ +30 kW

### 3.2 Les 3 objectifs à minimiser

**1. Coût (€) :**
```
Coût = Σ [Puissance_totale(heure) × Tarif(heure) × 1h]
```
- Si négatif → Profit (V2G)
- Si positif → Coût

**2. Insatisfaction :**
```
Insatisfaction = Σ max(0, SoC_voulu - SoC_obtenu)
```
- Mesure l'écart entre ce que veut l'utilisateur et ce qu'il obtient

**3. Pic de puissance (kW) :**
```
Pic = maximum de |Puissance_totale(heure)|
```
- Impact sur le réseau électrique

### 3.3 Contraintes

1. **SoC batterie** : Entre 0% et 100%
2. **Puissance site** : Maximum 60 kW au total
3. **Disponibilité** : On ne peut charger que si le véhicule est branché

---

## 4. L'Algorithme MODE

### 4.1 C'est quoi MODE ?

**MODE** = Multi-Objective Differential Evolution

C'est un algorithme **évolutionnaire** : il fait évoluer une population de solutions comme dans la nature.

**Principe :**
1. **Départ** : 100 solutions aléatoires
2. **Itération** (1500 fois) :
   - Créer de nouvelles solutions par mutation/croisement
   - Garder les meilleures (celles non-dominées)
3. **Résultat** : Front de Pareto = ensemble des meilleures solutions

### 4.2 Paramètres utilisés

| Paramètre | Valeur | Signification |
|-----------|--------|---------------|
| Population | 100 | Nombre de solutions à chaque génération |
| Générations | 1500 | Nombre d'itérations |
| F (mutation) | 0.5 | Ampleur des variations |
| CR (croisement) | 0.9 | Fréquence d'échange de gènes |

### 4.3 Pourquoi MODE pour ce problème ?

✅ Gère **plusieurs objectifs** simultanément
✅ Fonctionne avec des **variables continues** (puissances réelles)
✅ Gère les **contraintes** (SoC, puissance site)
✅ Pas besoin de dérivées (problème complexe)
✅ Trouve un **ensemble de solutions** (pas qu'une seule)

---

## 5. Résultats Obtenus

### 5.1 Chiffres clés

**Exécution :**
- Temps : **34 secondes**
- Solutions trouvées : **100 solutions non-dominées**
- **Toutes** respectent les contraintes

**Qualité des solutions :**
- **Hypervolume = 0.73** → Couvre 73% de l'espace optimal (excellent)
- **Spacing = 0.031** → Distribution très uniforme (excellent)

### 5.2 Analyse des 3 objectifs

#### Objectif 1 : Coût

| | Valeur | Signification |
|---|--------|---------------|
| **Meilleur** | **-4.50 €** | **Profit !** (V2G marche) |
| Pire | 54.47 € | Coût maximum |
| Moyen | 19.14 € | Coût moyen |
| Variabilité (CV) | 79% | Très flexible |

**Ce qu'on comprend :**
- On peut **gagner de l'argent** avec le V2G (-4.50€)
- Grande flexibilité : selon la priorité, le coût varie beaucoup

#### Objectif 2 : Insatisfaction

| | Valeur | Signification |
|---|--------|---------------|
| **Meilleure** | **2.76** | ~9% d'écart par véhicule |
| Pire | 6.93 | ~23% d'écart par véhicule |
| Moyenne | 4.03 | ~13% d'écart par véhicule |
| Variabilité (CV) | 26% | Bien contrôlé |

**Ce qu'on comprend :**
- Même dans le pire cas, l'insatisfaction reste acceptable
- Objectif le plus "stable" (varie peu)

#### Objectif 3 : Pic de puissance

| | Valeur | % du max site |
|---|--------|---------------|
| **Meilleur** | **14.07 kW** | 23% | Excellent lissage |
| Pire | 58.37 kW | 97% | Proche de la limite |
| Moyen | 32.27 kW | 54% | Utilisation modérée |
| Variabilité (CV) | 34% | Flexible |

**Ce qu'on comprend :**
- On peut **réduire le pic de 76%** (de 58 à 14 kW !)
- Aucune solution ne dépasse la limite de 60 kW

---

## 6. Ce qu'on a compris

### 6.1 Sur le problème multi-objectifs

**Constat principal :** Les 3 objectifs sont **vraiment contradictoires**

Exemples :
- Pour gagner de l'argent (coût -4.50€) → Il faut utiliser le V2G → Ça crée des pics
- Pour avoir un petit pic (14 kW) → Il faut charger lentement → Ça insatisfait les utilisateurs
- Pour satisfaire tout le monde → Il faut charger vite → Ça coûte cher et crée des pics

**Conclusion :** C'est normal qu'il n'y ait pas UNE solution optimale. On doit **choisir selon la priorité**.

### 6.2 Sur le tarif TOU

Le prix qui varie selon l'heure change beaucoup les choses :

1. **Incitation naturelle** : MODE privilégie les heures creuses pour charger
2. **V2G rentable** : Décharger aux heures de pointe (0.30 $/kWh) génère des revenus
3. **Compromis nécessaire** : Charger uniquement la nuit insatisfait ceux qui partent tôt le matin

### 6.3 Sur MODE

**Ce qu'on observe :**
- MODE **converge bien** : HV = 0.73 (excellent)
- Les solutions sont **bien réparties** : SP = 0.031 (très uniforme)
- C'est **rapide** : 34 secondes pour 720 variables
- **1500 générations** suffisent pour explorer correctement l'espace

### 6.4 Validation

**Pourquoi on peut faire confiance aux résultats :**

✅ **Contraintes respectées** : 100% des solutions sont valides
- SoC toujours entre 0% et 100%
- Puissance site jamais > 60 kW
- Respect de la disponibilité des véhicules

✅ **Cohérence physique** :
- Quand coût < 0 → On voit bien des flux négatifs (V2G)
- Charge rapide → Pics élevés
- Charge lente → Pics faibles

✅ **Reproductible** :
- Avec le même seed (seed=1), on obtient toujours les mêmes résultats

---

## 7. Limites et Améliorations Possibles

### 7.1 Ce qu'on n'a pas fait (limites)

**Sur le modèle :**
- Tarifs TOU fixes (pas de prévision de prix futurs)
- Batterie simplifiée (pas de dégradation, rendement 100%)
- On suppose qu'on connaît les heures d'arrivée/départ à l'avance
- Optimisation sur 24h seulement (pas multi-jours)

**Sur l'algorithme :**
- Paramètres F et CR fixés manuellement
- Une seule exécution (pas de statistiques sur plusieurs runs)

### 7.2 Ce qu'on pourrait améliorer

**Court terme :**
- Tester différentes valeurs de F et CR
- Faire plusieurs exécutions et calculer les moyennes
- Ajouter un modèle de dégradation de batterie

**Long terme :**
- Prévoir les prix futurs de l'électricité
- Optimiser sur plusieurs jours
- Prendre en compte l'incertitude sur les arrivées/départs

---

## 8. Conclusion

### 8.1 Ce qu'on a réalisé

✅ Implémenté MODE pour optimiser 720 variables
✅ Utilisé des **données réelles** (Caltech, 30 véhicules)
✅ Obtenu **100 solutions de qualité** (HV=0.73, SP=0.031)
✅ Prouvé la **viabilité du V2G** (jusqu'à -4.50€ de profit)
✅ Montré qu'on peut **réduire le pic de 76%** (de 58 à 14 kW)

### 8.2 Réponse à la question initiale

**Question :** Comment optimiser le coût, la satisfaction et le pic simultanément ?

**Réponse :**
On **ne peut pas** avoir UNE solution qui optimise tout. Mais on peut trouver **100 solutions non-dominées** qui offrent différents compromis :

| Priorité | Choix de solution | Résultat |
|----------|-------------------|----------|
| **Gagner de l'argent** | Solution à coût minimal | -4.50€ (profit V2G) |
| **Satisfaire les clients** | Solution à insatisfaction minimale | Écart de 9% seulement |
| **Protéger le réseau** | Solution à pic minimal | 14 kW (au lieu de 58) |

**Le gestionnaire choisit selon sa priorité du moment.**

### 8.3 Ce qu'on a appris

**Sur le multi-objectifs :**
- Les conflits entre objectifs sont réels et inévitables
- C'est normal de ne pas pouvoir tout optimiser
- Le front de Pareto donne le **choix** au décideur

**Sur MODE :**
- Efficace pour ce type de problème (73% de l'espace couvert)
- Converge rapidement (34 secondes)
- Produit des solutions bien distribuées

**Sur le V2G :**
- C'est rentable avec un tarif TOU
- Maximiser le profit crée des pics
- Il faut trouver le bon équilibre

---

## Références Principales

- **Storn & Price (1997)** : Differential Evolution (base de MODE)
- **Deb et al. (2002)** : NSGA-II (référence en multi-objectifs)
- **Caltech ACN-Data** : https://ev.caltech.edu/

---

**Fin du Rapport**
