"""
Interactive menu for user configuration.
"""
from typing import Optional, List, Tuple
from datetime import date, datetime
import sys

from ..infrastructure.repositories.caltech_repository import CaltechRepository
from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


def get_available_dates(
    repository: CaltechRepository,
    site: str = "caltech",
    limit: int = 10
) -> List[str]:
    """
    Get available dates with charging sessions from Caltech API.
    
    Args:
        repository: Caltech repository instance
        site: Site ID to query
        limit: Max number of dates to return
        
    Returns:
        List of dates (YYYY-MM-DD strings) with data
    """
    logger.info(f"Fetching available dates from {site}...")
    
    # Query API for latest sessions (without date filter to get any available)
    try:
        url = f"{repository.api_url}/{site}"
        params = {
            "max_results": 100,  # Get last 100 sessions
            "sort": "-connectionTime"  # Descending order
        }
        
        data = repository._make_request(url, params)
        sessions_data = data.get("_items", [])
        
        # Extract unique dates
        dates_set = set()
        for item in sessions_data:
            if "connectionTime" in item:
                try:
                    conn_time = datetime.strptime(item["connectionTime"], "%a, %d %b %Y %H:%M:%S %Z")
                    dates_set.add(conn_time.date().isoformat())
                except:
                    pass
        
        # Sort descending and limit
        available_dates = sorted(list(dates_set), reverse=True)[:limit]
        logger.info(f"Found {len(available_dates)} dates with data")
        
        return available_dates
        
    except Exception as e:
        logger.warning(f"Could not fetch available dates: {e}")
        # Return default date if API fails
        return [settings.caltech_date]


def interactive_menu() -> dict:
    """
    Display interactive menu for user to configure optimization.
    
    Returns:
        Dictionary with user selections
    """
    print("\n" + "="*70)
    print("  🚗 EV Charging Optimizer - Configuration Interactive")
    print("="*70 + "\n")
    
    config = {}
    
    # Initialize repository for date fetching
    try:
        repository = CaltechRepository()
        can_fetch_dates = True
    except Exception as e:
        logger.warning(f"Cannot connect to Caltech API: {e}")
        can_fetch_dates = False
    
    # 1. Site selection
    print("📍 Sélection du site Caltech")
    print(f"   Options: caltech, jpl, office001")
    site_input = input(f"   Choisir un site [défaut: {settings.caltech_site}]: ").strip()
    config['site'] = site_input if site_input else settings.caltech_site
    
    # 2. Date selection with available dates
    print(f"\n📅 Sélection de la date")
    
    if can_fetch_dates:
        print("   Récupération des dates disponibles...")
        available_dates = get_available_dates(repository, config['site'])
        
        if available_dates:
            print("\n   Dates disponibles avec des données :")
            for i, date_str in enumerate(available_dates[:10], 1):
                print(f"   {i}. {date_str}")
            
            print(f"\n   Ou entrez une date manuelle (YYYY-MM-DD)")
            date_input = input(f"   Choisir [1-{min(10, len(available_dates))}] ou date [défaut: {settings.caltech_date}]: ").strip()
            
            if date_input.isdigit() and 1 <= int(date_input) <= len(available_dates):
                config['date'] = available_dates[int(date_input) - 1]
            elif date_input:
                config['date'] = date_input
            else:
                config['date'] = settings.caltech_date
        else:
            date_input = input(f"   Entrer une date (YYYY-MM-DD) [défaut: {settings.caltech_date}]: ").strip()
            config['date'] = date_input if date_input else settings.caltech_date
    else:
        date_input = input(f"   Entrer une date (YYYY-MM-DD) [défaut: {settings.caltech_date}]: ").strip()
        config['date'] = date_input if date_input else settings.caltech_date
    
    # 2.5. Get stats for selected date
    max_vehicles_available = None
    suggested_power = None
    
    if can_fetch_dates:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(config['date'], "%Y-%m-%d").date()
            
            print(f"\n   📊 Analyse des données pour {config['date']}...")
            
            # Fetch all sessions for that date
            sessions = repository.fetch_sessions(
                start_date=selected_date,
                site=config['site'],
                limit=None  # Get all
            )
            
            max_vehicles_available = len(sessions)
            
            # Calculate suggested power (sum of max charging rates)
            if sessions:
                total_power = sum(min(30.0, s.kwh_delivered) for s in sessions[:50])  # Estimate
                suggested_power = round(total_power / 2, 1)  # Rough estimate
            
            print(f"   ✓ {max_vehicles_available} sessions de charge détectées")
            if suggested_power:
                print(f"   ✓ Puissance suggérée pour ce jour : ~{suggested_power} kW")
                
        except Exception as e:
            logger.warning(f"Could not fetch stats: {e}")
    
    # 3. Number of vehicles
    print(f"\n🚙 Nombre de véhicules")
    if max_vehicles_available:
        print(f"   Maximum disponible pour cette date : {max_vehicles_available}")
        limit_input = input(f"   Nombre de véhicules [défaut: {min(settings.caltech_limit, max_vehicles_available)}]: ").strip()
    else:
        limit_input = input(f"   Nombre maximum de véhicules [défaut: {settings.caltech_limit}]: ").strip()
    
    if limit_input.isdigit():
        config['limit'] = int(limit_input)
    else:
        config['limit'] = min(settings.caltech_limit, max_vehicles_available) if max_vehicles_available else settings.caltech_limit
    
    # 4. Site max power (optional)
    print(f"\n⚡ Puissance maximale du site")
    if suggested_power:
        print(f"   Puissance suggérée basée sur les données : {suggested_power} kW")
        power_input = input(f"   Puissance max (kW) [défaut: {suggested_power}]: ").strip()
        default_power = suggested_power
    else:
        power_input = input(f"   Puissance max (kW) [défaut: {settings.site_max_power}]: ").strip()
        default_power = settings.site_max_power
    
    if power_input:
        try:
            config['site_max_power'] = float(power_input)
        except:
            config['site_max_power'] = default_power
    else:
        config['site_max_power'] = default_power
    
    # 5. GDE3 parameters (advanced, optional)
    print(f"\n🧬 Paramètres algorithme GDE3 (optionnel)")
    advanced = input(f"   Configurer les paramètres avancés ? [o/N]: ").strip().lower()
    
    if advanced == 'o' or advanced == 'oui':
        gen_input = input(f"   Nombre de générations [défaut: {settings.gde3_n_gen}]: ").strip()
        config['generations'] = int(gen_input) if gen_input.isdigit() else settings.gde3_n_gen
        
        pop_input = input(f"   Taille de population [défaut: {settings.gde3_pop_size}]: ").strip()
        config['population'] = int(pop_input) if pop_input.isdigit() else settings.gde3_pop_size
    else:
        config['generations'] = settings.gde3_n_gen
        config['population'] = settings.gde3_pop_size
    
    # Summary
    print("\n" + "="*70)
    print("  📋 Résumé de la configuration")
    print("="*70)
    print(f"  Site:           {config['site']}")
    print(f"  Date:           {config['date']}")
    print(f"  Véhicules:      {config['limit']}")
    print(f"  Puissance site: {config['site_max_power']} kW")
    print(f"  GDE3 gens:      {config['generations']}")
    print(f"  GDE3 pop:       {config['population']}")
    print("="*70 + "\n")
    
    confirm = input("  Lancer l'optimisation ? [O/n]: ").strip().lower()
    if confirm == 'n' or confirm == 'non':
        print("\n  ❌ Annulé par l'utilisateur\n")
        sys.exit(0)
    
    return config
