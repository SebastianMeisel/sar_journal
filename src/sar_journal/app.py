import argparse
from datetime import timedelta
from .config import AppConfig, parse_timestamp
from .ui import JournalSarApp

def build_args() -> AppConfig:
    """Parse command line arguments and build application configuration.
    
    Returns:
        AppConfig object with parsed arguments
        
    Raises:
        SystemExit: If arguments are invalid
    """
    ap = argparse.ArgumentParser(
        description="Journal+SAR TUI - Monitor system journal and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --time "2024-01-15 14:00" 
  %(prog)s --time "2024-01-15 14:00:00" 
        """
    )
    ap.add_argument("--time", required=True, 
                   help="Start time (YYYY-MM-DD HH:MM[:SS])")
    
    args = ap.parse_args()
    time = parse_timestamp(args.time)
    until = parse_timestamp(args.time) + timedelta(minutes=10)

    return AppConfig(time=time, until=until)

def main() -> None:
    """Run the TUI application."""
    cfg = build_args()                 # ✅ build config
    app = JournalSarApp(cfg)           # ✅ pass cfg into constructor
    app.run()

if __name__ == "__main__":
    main()

