import numpy as np

# --- PARAMÈTRES GLOBAUX ---
# Note : Pour tester rapidement, vous pouvez réduire N_VEHICLES à 5
N_VEHICLES = 30           # Nombre de véhicules (Réduit à 10 pour l'exemple, 30 dans le doc)
T_HORIZON = 24            # Horizon temporel (24h)
DT = 1.0                  # Pas de temps (1h)

# --- CARACTÉRISTIQUES PHYSIQUES ---
C_BATTERY = 30.0          # Capacité batterie (30 kWh)
EFFICIENCY = 0.98         # Rendement (simplifié ici à 1.0 dans les calculs pour l'instant)
P_MAX_SITE = 60.0        # Puissance max du transformateur du site (kW)

# --- BORNES DE PUISSANCE (Variables de décision) ---
# Autorise la décharge (V2G) si valeur négative
P_MIN_EV = -0.2 * C_BATTERY  # Ex: -6 kW (Décharge)
P_MAX_EV = 1.0 * C_BATTERY   # Ex: 30 kW (Charge rapide)