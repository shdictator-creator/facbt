#!/usr/bin/env python3
"""
FACBT (Facebook Account Creator Bot) - Main Entry Point
A sophisticated Facebook account creation bot with advanced anti-detection features.

Author: Manus AI
Version: 1.0.0
License: MIT
"""

import sys
import os
import asyncio
import argparse
import signal
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.engine import FACBTEngine
from utils.logger import LoggerFactory
from utils.config_manager import ConfigurationManager
from utils.banner import print_banner


class FACBTApplication:
    """Main application class for FACBT"""
    
    def __init__(self):
        self.engine: Optional[FACBTEngine] = None
        self.config_manager: Optional[ConfigurationManager] = None
        self.logger = LoggerFactory.create_logger(__name__)
        self.shutdown_event = asyncio.Event()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def initialize(self, config_path: Optional[str] = None):
        """Initialize the application"""
        try:
            self.logger.info("Initializing FACBT application...")
            
            # Load configuration
            self.config_manager = ConfigurationManager(config_path)
            config = self.config_manager.get_configuration()
            
            # Initialize the main engine
            self.engine = FACBTEngine(config)
            await self.engine.initialize()
            
            self.logger.info("FACBT application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False
            
    async def run(self, accounts_to_create: int = 1):
        """Run the main application loop"""
        try:
            self.logger.info(f"Starting FACBT - Creating {accounts_to_create} accounts")
            
            if not self.engine:
                raise RuntimeError("Engine not initialized")
                
            # Start the engine
            await self.engine.start()
            
            # Create accounts
            success_count = 0
            for i in range(accounts_to_create):
                if self.shutdown_event.is_set():
                    break
                    
                self.logger.info(f"Creating account {i + 1}/{accounts_to_create}")
                result = await self.engine.create_account()
                
                if result.success:
                    success_count += 1
                    self.logger.info(f"Account {i + 1} created successfully")
                else:
                    self.logger.error(f"Failed to create account {i + 1}: {result.error}")
                    
            self.logger.info(f"Account creation completed. Success: {success_count}/{accounts_to_create}")
            
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            
    async def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            self.logger.info("Shutting down FACBT application...")
            self.shutdown_event.set()
            
            if self.engine:
                await self.engine.stop()
                
            self.logger.info("FACBT application shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="FACBT - Facebook Account Creator Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --accounts 5                    # Create 5 accounts
  python main.py --config custom.json           # Use custom config
  python main.py --accounts 10 --verbose        # Verbose logging
  python main.py --test-mode                    # Run in test mode
        """
    )
    
    parser.add_argument(
        "--accounts", "-a",
        type=int,
        default=1,
        help="Number of accounts to create (default: 1)"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--test-mode", "-t",
        action="store_true",
        help="Run in test mode (no actual account creation)"
    )
    
    parser.add_argument(
        "--proxy-test",
        action="store_true",
        help="Test proxy connectivity only"
    )
    
    parser.add_argument(
        "--email-test",
        action="store_true",
        help="Test email services only"
    )
    
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="FACBT 1.0.0"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    # Print banner
    print_banner()
    
    # Parse arguments
    args = parse_arguments()
    
    # Set log level based on arguments
    if args.debug:
        os.environ["FACBT_LOG_LEVEL"] = "DEBUG"
    elif args.verbose:
        os.environ["FACBT_LOG_LEVEL"] = "INFO"
        
    # Set test mode if specified
    if args.test_mode:
        os.environ["FACBT_TEST_MODE"] = "true"
        
    # Create application instance
    app = FACBTApplication()
    app.setup_signal_handlers()
    
    try:
        # Initialize application
        if not await app.initialize(args.config):
            sys.exit(1)
            
        # Handle special modes
        if args.validate_config:
            print("✅ Configuration is valid")
            return
            
        if args.proxy_test:
            # TODO: Implement proxy testing
            print("🔍 Testing proxy connectivity...")
            return
            
        if args.email_test:
            # TODO: Implement email testing
            print("📧 Testing email services...")
            return
            
        # Run main application
        await app.run(args.accounts)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
        
    # Check if running in Termux
    if "com.termux" in os.environ.get("PREFIX", ""):
        print("📱 Detected Termux environment")
        
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

