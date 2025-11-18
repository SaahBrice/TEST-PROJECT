# test_setup.py
"""
Simple test script to verify logging and configuration setup.
"""

from utils import setup_logging, ConfigManager

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing logging system...")
    
    # Initialize configuration
    config = ConfigManager()
    logger.info("Testing configuration system...")
    
    # Read some config values
    sample_rate = config.get('audio', 'sample_rate')
    color_scheme = config.get('visualization', 'color_scheme')
    
    logger.info(f"Sample Rate: {sample_rate}")
    logger.info(f"Color Scheme: {color_scheme}")
    
    # Test setting a value
    config.set('ui', 'last_directory', '/test/path')
    config.save_config()
    
    logger.info("Configuration and logging systems working correctly!")
    print("\n✓ Setup successful! Check the 'logs' folder and 'config.json' file.")

if __name__ == '__main__':
    main()
