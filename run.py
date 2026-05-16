#!/usr/bin/env python3
"""
MedAI Backend Runner
Multi-Agent Medical Consultation System
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('medai_backend.log')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and dependencies"""
    logger.info("ðŸ” Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("âŒ Python 3.8 or higher is required")
        return False
    
    # Check for .env file
    env_file = backend_dir / '.env'
    if not env_file.exists():
        logger.warning("âš ï¸  .env file not found. Creating from example...")
        env_example = backend_dir / '.env.example'
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            logger.info("ðŸ“ Created .env file from example. Please update with your API keys.")
        else:
            logger.error("âŒ .env.example not found")
            return False
    
    # Check required environment variables
    required_vars = ['GROQ_API_KEY', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"âŒ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("ðŸ’¡ Set these in the .env file:")
        for var in missing_vars:
            if var == 'GROQ_API_KEY':
                logger.info(f"   {var}=your_groq_api_key_here  # Get from https://console.groq.com/keys")
            elif var == 'SECRET_KEY':
                logger.info(f"   {var}=generate_with: openssl rand -hex 32")
        return False
    
    logger.info("âœ… Environment check passed")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("ðŸ“¦ Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'groq',
        'sqlalchemy',
        'pydantic',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"âŒ Missing packages: {', '.join(missing_packages)}")
        logger.info(f"ðŸ’¡ Install with: pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("âœ… All dependencies are installed")
    return True

def initialize_database():
    """Initialize database if needed"""
    logger.info("ðŸ—„ï¸  Initializing database...")
    
    try:
        from app.db import init_db # type: ignore
        init_db()
        logger.info("âœ… Database initialized")
        return True
    except Exception as e:
        logger.error(f"âŒ Database initialization failed: {e}")
        return False

def start_server(host='0.0.0.0', port=8000, reload=True):
    """Start the FastAPI server"""
    logger.info(f"ðŸš€ Starting MedAI Backend Server...")
    logger.info(f"ðŸŒ Access URLs:")
    logger.info(f"   Local: http://{host}:{port}")
    logger.info(f"   Network: http://localhost:{port}")
    logger.info(f"   API Docs: http://{host}:{port}/docs")
    logger.info(f"   Redoc: http://{host}:{port}/redoc")
    logger.info(f"ðŸ“Š Server will reload automatically on code changes: {reload}")
    
    # Configure uvicorn
    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
        workers=1
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("ðŸ‘‹ Server stopped by user")
    except Exception as e:
        logger.error(f"âŒ Server error: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("ðŸ¥ MedAI - Medical AI Consultation System")
    print("="*60 + "\n")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='MedAI Backend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    parser.add_argument('--check-only', action='store_true', help='Only check environment and exit')
    
    args = parser.parse_args()
    
    # Run checks
    if not check_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_only:
        logger.info("âœ… All checks passed!")
        sys.exit(0)
    
    # Initialize database
    if not initialize_database():
        logger.warning("âš ï¸  Database initialization failed, but continuing...")
    
    # Start server
    success = start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()


