#!/usr/bin/env python3
"""
Logging Reduction Script
This script helps reduce verbose logging by applying configuration settings.
"""

import yaml
import logging
import os
from pathlib import Path

def load_logging_config():
    """Load logging configuration from YAML file."""
    config_path = Path("config/logging_config.yaml")
    if not config_path.exists():
        print("❌ Logging config file not found: config/logging_config.yaml")
        return None
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def apply_logging_config(config):
    """Apply logging configuration."""
    if not config:
        return False
    
    try:
        # Set logging levels for specific modules
        if 'logging_levels' in config and 'modules' in config['logging_levels']:
            for module, level in config['logging_levels']['modules'].items():
                logging.getLogger(module).setLevel(getattr(logging, level))
                print(f"✅ Set {module} logging level to {level}")
        
        # Set default logging level
        if 'logging_levels' in config and 'default' in config['logging_levels']:
            default_level = config['logging_levels']['default']
            logging.getLogger().setLevel(getattr(logging, default_level))
            print(f"✅ Set default logging level to {default_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying config: {e}")
        return False

def show_current_settings():
    """Show current logging configuration."""
    config = load_logging_config()
    if not config:
        return
    
    print("\n📋 Current Logging Configuration:")
    print("=" * 50)
    
    if 'system_integration' in config:
        si = config['system_integration']
        print(f"🔧 Load Balancer Loop: {'✅ Enabled' if si.get('enable_load_balancer_loop', True) else '❌ Disabled'}")
        print(f"⏱️  Update Interval: {si.get('load_balancer_update_interval', 30)} seconds")
        print(f"📝 Verbose Logging: {'✅ Enabled' if si.get('enable_verbose_logging', False) else '❌ Disabled'}")
    
    if 'logging_levels' in config:
        levels = config['logging_levels']
        print(f"📊 Default Level: {levels.get('default', 'INFO')}")
        
        if 'modules' in levels:
            print("\n📦 Module Logging Levels:")
            for module, level in levels['modules'].items():
                print(f"  • {module}: {level}")

def main():
    """Main function."""
    print("🔇 DBSBM Logging Reduction Tool")
    print("=" * 40)
    
    # Show current settings
    show_current_settings()
    
    # Apply configuration
    config = load_logging_config()
    if apply_logging_config(config):
        print("\n✅ Logging configuration applied successfully!")
        print("\n💡 To permanently reduce logging:")
        print("   1. Set 'enable_load_balancer_loop: false' in config/logging_config.yaml")
        print("   2. Set 'enable_verbose_logging: false' in config/logging_config.yaml")
        print("   3. Increase 'load_balancer_update_interval' to 300+ seconds")
        print("   4. Set module logging levels to 'WARNING' or 'ERROR'")
    else:
        print("\n❌ Failed to apply logging configuration")

if __name__ == "__main__":
    main() 