"""
Main CLI entry point for EV Charging Optimizer.
"""
import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from ..config.settings import settings
from ..config.logging_config import setup_logging, get_logger
from ..services.optimization_service import GDE3OptimizerService
from ..infrastructure.repositories.caltech_repository import CaltechRepository
from ..infrastructure.repositories.synthetic_generator import SyntheticDataGenerator
from ..infrastructure.cache.file_cache import FileCache
from ..application.use_cases.optimize_charging import OptimizeChargingUseCase
from .interactive import interactive_menu

# Setup logging
setup_logging(level=settings.log_level, log_file=settings.log_file)
logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="EV Charging Optimization - Professional Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Synthetic mode (default)
  python -m src.cli.main
  
  # Real data mode
  python -m src.cli.main --real-data --date 2019-05-01 --limit 30
  
  # Custom configuration
  python -m src.cli.main --real-data --site jpl --vehicles 50
        """
    )
    
    # Mode selection
    parser.add_argument(
        '--real-data',
        action='store_true',
        help='Use real Caltech dataset instead of synthetic data'
    )
    
    # Real data options
    parser.add_argument(
        '--site',
        type=str,
        default=settings.caltech_site,
        choices=['caltech', 'jpl', 'office001'],
        help=f'Caltech site ID (real data mode, default: {settings.caltech_site})'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        default=settings.caltech_date,
        help=f'Date for real data (YYYY-MM-DD), defaults to {settings.caltech_date}'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=settings.caltech_limit,
        help=f'Maximum number of vehicles (default: {settings.caltech_limit})'
    )
    
    # Synthetic data options
    parser.add_argument(
        '--vehicles',
        type=int,
        default=settings.n_vehicles,
        help=f'Number of vehicles for synthetic mode (default: {settings.n_vehicles})'
    )
    
    parser.add_argument(
        '--horizon',
        type=int,
        default=settings.t_horizon,
        help=f'Time horizon in hours (default: {settings.t_horizon})'
    )
    
    parser.add_argument(
        '--site-power',
        type=float,
        default=settings.site_max_power,
        help=f'Maximum site power in kW (default: {settings.site_max_power})'
    )
    
    # Optimization options
    parser.add_argument(
        '--generations',
        type=int,
        default=settings.gde3_n_gen,
        help=f'GDE3 generations (default: {settings.gde3_n_gen})'
    )
    
    parser.add_argument(
        '--population',
        type=int,
        default=settings.gde3_pop_size,
        help=f'GDE3 population size (default: {settings.gde3_pop_size})'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('results'),
        help='Output directory for results (default: results/)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to files'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Interactive mode - choose parameters via menu'
    )
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Update log level if verbose
    if args.verbose:
        setup_logging(level="DEBUG")
    
    # Interactive mode - override args with menu selections
    if args.interactive:
        interactive_config = interactive_menu()
        # Override CLI args with interactive selections
        args.real_data = True  # Interactive mode always uses real data
        args.site = interactive_config['site']
        args.date = interactive_config['date']
        args.limit = interactive_config['limit']
        args.site_power = interactive_config['site_max_power']
        args.generations = interactive_config['generations']
        args.population = interactive_config['population']
    
    # Print banner
    print(f"\n{'='*70}")
    print(f"  {settings.app_name} v{settings.app_version}")
    print(f"{'='*70}\n")
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        # Cache
        cache = FileCache(
            cache_dir=settings.cache_dir,
            default_ttl=timedelta(seconds=settings.cache_ttl),
            use_pickle=True  # Use pickle to cache complex objects like Scenario
        )
        
        # Optimizer
        optimizer_config = settings.get_optimizer_config()
        optimizer_config['n_gen'] = args.generations
        optimizer_config['pop_size'] = args.population
        optimizer = GDE3OptimizerService(config=optimizer_config)
        
        # Data sources
        caltech_repo = None
        if args.real_data:
            try:
                caltech_repo = CaltechRepository()
            except ValueError as e:
                logger.error(f"Failed to initialize Caltech repository: {e}")
                print(f"\n❌ Error: {e}")
                print("   Please set CALTECH_API_KEY in your .env file\n")
                sys.exit(1)
        
        synthetic_gen = SyntheticDataGenerator()
        
        # Use case
        use_case = OptimizeChargingUseCase(
            optimizer=optimizer,
            real_data_source=caltech_repo,
            synthetic_data_source=synthetic_gen,
            cache=cache
        )
        
        # Execute
        if args.real_data:
            # Parse date
            optimization_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            
            print(f"🌐 MODE: Real Data")
            print(f"   Site: {args.site}")
            print(f"   Date: {optimization_date}")
            print(f"   Limit: {args.limit or 'None'}")
            print(f"{'='*70}\n")
            
            result = use_case.execute_real_data(
                start_date=optimization_date,
                site=args.site,
                site_max_power=args.site_power,
                limit=args.limit,
                save_results=not args.no_save,
                output_dir=args.output_dir
            )
        else:
            print(f"🔧 MODE: Synthetic Data")
            print(f"   Vehicles: {args.vehicles}")
            print(f"   Horizon: {args.horizon}h")
            print(f"   Site Power: {args.site_power}kW")
            print(f"{'='*70}\n")
            
            result = use_case.execute_synthetic(
                n_vehicles=args.vehicles,
                time_horizon=args.horizon,
                site_max_power=args.site_power,
                save_results=not args.no_save,
                output_dir=args.output_dir
            )
        
        # Display results
        print(f"\n{'='*70}")
        print(f"✅ OPTIMIZATION SUCCESSFUL")
        print(f"{'='*70}")
        print(f"\n📊 Results:")
        print(f"   Cost:            {result.metrics.cost:.2f} €")
        print(f"   Dissatisfaction: {result.metrics.dissatisfaction:.4f}")
        print(f"   Peak Power:      {result.metrics.peak_power:.2f} kW")
        print(f"   Execution Time:  {result.execution_time:.2f} s")
        print(f"   Solutions Found: {result.solutions_found}")
        print(f"\n📋 Schedule:")
        print(f"   Vehicles:        {result.n_vehicles}")
        print(f"   Time Horizon:    {result.n_hours}h")
        print(f"   Total Energy:    {result.charging_schedule.sum():.2f} kWh")
        
        if not args.no_save:
            print(f"\n💾 Results saved to: {args.output_dir}/")
        
        print(f"\n{'='*70}\n")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n\n⚠️  Interrupted by user\n")
        sys.exit(0)
        
    except Exception as e:
        logger.exception("Fatal error")
        print(f"\n\n❌ Fatal Error: {e}\n")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
