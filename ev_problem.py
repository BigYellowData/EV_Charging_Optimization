import numpy as np
from pymoo.core.problem import ElementwiseProblem
import config as cfg

class EVChargingProblem(ElementwiseProblem):
    def __init__(self, prices, availability_mask, soc_initial, soc_target, departure_times):
        """
        Définition du problème d'optimisation multi-objectifs sous contraintes.
        """
        # Variables : N véhicules * T heures
        super().__init__(n_var=cfg.N_VEHICLES * cfg.T_HORIZON,
                         n_obj=3,          # Coût, Insatisfaction, Stress
                         n_ieq_constr=2,   # 2 Types de contraintes (SoC et Puissance Site)
                         xl=cfg.P_MIN_EV,  # Borne inf (V2G autorisé) [cite: 1]
                         xu=cfg.P_MAX_EV)  # Borne sup
        
        # Données du scénario
        self.prices = prices
        self.availability_mask = availability_mask
        self.soc_initial = soc_initial
        self.soc_target = soc_target
        self.departure_times = departure_times

    def _evaluate(self, x, out, *args, **kwargs):
        # 1. Transformation Vecteur -> Matrice (Véhicules x Heures)
        A_matrix = x.reshape((cfg.N_VEHICLES, cfg.T_HORIZON))
        
        # [cite_start]2. Masquage (Force 0 si le véhicule n'est pas là) [cite: 1]
        A_matrix = A_matrix * self.availability_mask
        
        # [cite_start]3. Calcul de la dynamique de batterie (SoC) [cite: 1]
        # SoC(t+1) = SoC(t) + (Puissance * Dt) / Capacité
        energy_step = (A_matrix * cfg.DT) / cfg.C_BATTERY
        soc_profile = np.cumsum(energy_step, axis=1) + self.soc_initial[:, None]
        
        # --- CALCUL DES CONTRAINTES (G <= 0) ---
        
        # Contrainte 1 : SoC borné entre 0 et 1 (0% et 100%)
        # g = val - max <= 0  OU  g = min - val <= 0
        g1_min = -soc_profile       # Devient positif si SoC < 0
        g1_max = soc_profile - 1    # Devient positif si SoC > 1
        soc_violation = np.sum(np.maximum(0, g1_min)) + np.sum(np.maximum(0, g1_max))
        
        # [cite_start]Contrainte 2 : Puissance totale site <= P_MAX [cite: 1]
        total_power_t = np.sum(A_matrix, axis=0)
        grid_violation = np.max(np.maximum(0, np.abs(total_power_t) - cfg.P_MAX_SITE))
        
        # --- CALCUL DES OBJECTIFS (Minimisation) ---
        
        # [cite_start]Obj 1 : Coût Énergie [cite: 1]
        cost_obj = np.sum(total_power_t * self.prices * cfg.DT)
        
        # [cite_start]Obj 2 : Insatisfaction (SoC départ vs SoC requis) [cite: 1]
        final_socs = np.zeros(cfg.N_VEHICLES)
        for i in range(cfg.N_VEHICLES):
            t_dep = self.departure_times[i]
            t_idx = min(t_dep, cfg.T_HORIZON - 1)
            final_socs[i] = soc_profile[i, t_idx]
            
        dissatisfaction_obj = np.sum(np.maximum(0, self.soc_target - final_socs))
        
        # [cite_start]Obj 3 : Stress Réseau (Pic de puissance absolu) [cite: 1]
        grid_stress_obj = np.max(np.abs(total_power_t))

        # Sorties pour Pymoo
        out["F"] = [cost_obj, dissatisfaction_obj, grid_stress_obj]
        out["G"] = [soc_violation, grid_violation]