# main.py
import numpy as np
import matplotlib.pyplot as plt
from pymoode.algorithms import GDE3
from pymoo.optimize import minimize
from pymoo.config import Config

# Désactive le warning de compilation pour Docker
Config.warnings['not_compiled'] = False

import config as cfg
from ev_problem import EVChargingProblem

def generate_scenario():
    """Génère un scénario aléatoire cohérent."""
    np.random.seed(42)
    
    # Prix (courbe type : cher le matin/soir, moins cher la nuit)
    hours = np.arange(cfg.T_HORIZON)
    prices = 0.15 + 0.10 * np.sin((hours - 6) * np.pi / 12)**2
    
    # Horaires
    t_arrival = np.random.randint(6, 10, cfg.N_VEHICLES)   # Arrivée 06h-10h
    t_departure = np.random.randint(17, 22, cfg.N_VEHICLES)# Départ 17h-22h
    
    # Batteries
    soc_initial = np.random.uniform(0.1, 0.4, cfg.N_VEHICLES) # Arrivent à vide
    soc_target = np.random.uniform(0.8, 1.0, cfg.N_VEHICLES)  # Veulent repartir pleins
    
    # Masque
    mask = np.zeros((cfg.N_VEHICLES, cfg.T_HORIZON))
    for i in range(cfg.N_VEHICLES):
        mask[i, t_arrival[i]:t_departure[i]] = 1
        
    return prices, mask, soc_initial, soc_target, t_departure

if __name__ == "__main__":
    print(f"--- Configuration : {cfg.N_VEHICLES} véhicules sur {cfg.T_HORIZON}h ---")
    prices, mask, soc_init, soc_req, t_dep = generate_scenario()

    # Instanciation
    problem = EVChargingProblem(prices, mask, soc_init, soc_req, t_dep)

    # Algorithme GDE3 (Evolution Différentielle Multi-obj)
    algorithm = GDE3(pop_size=100, variant="DE/rand/1/bin", CR=0.9, F=0.5)

    print("Lancement de l'optimisation (Cela peut prendre quelques secondes)...")
    res = minimize(problem,
                   algorithm,
                   ('n_gen', 1500), # 500 générations pour assurer la convergence
                   seed=1,
                   verbose=True)

    # --- AFFICHAGE ROBUSTE ---
    if res.F is not None:
        print(f"\n✅ SUCCÈS ! {len(res.F)} solutions valides trouvées.")
        
        # Récupération de la meilleure solution (compromis coût)
        best_idx = 0
        if res.F.ndim > 1:
            best_idx = np.argmin(res.F[:, 0]) # Index du coût min
            best_F = res.F[best_idx]
            best_X = res.X[best_idx]
        else:
            best_F = res.F
            best_X = res.X

        print("\n" + "="*60)
        print("🔍 SOLUTION OPTIMALE (Priorité Coût)")
        print(f"   Coût : {best_F[0]:.2f} € | Insatisfaction : {best_F[1]:.2f} | Pic : {best_F[2]:.2f} kW")
        print("="*60)

        # Affichage Matriciel du Planning
        schedule = best_X.reshape((cfg.N_VEHICLES, cfg.T_HORIZON))
        print("\n📋 PLANNING DE CHARGE (kW) : [Positif=Charge, Négatif=V2G]")
        header = "Vh/H | " + " ".join([f"{h:02d}" for h in range(cfg.T_HORIZON)])
        print(header)
        print("-" * len(header))
        
        # Affiche max 10 véhicules
        limit = min(cfg.N_VEHICLES, 10)
        for i in range(limit):
            row = "".join([f"{val:3.0f}" for val in schedule[i]])
            print(f"V#{i+1:02d} |{row}")
            
    else:
        print("\n❌ ÉCHEC : Aucune solution respectant les contraintes n'a été trouvée.")
        print("Conseil : Augmentez n_gen ou réduisez le nombre de véhicules.")