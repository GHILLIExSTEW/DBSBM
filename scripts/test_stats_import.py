#!/usr/bin/env python3
"""
Test script to check if StatsImageGenerator can be imported correctly.
"""

import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

def test_imports():
    """Test various import methods for StatsImageGenerator."""
    print("Testing StatsImageGenerator imports...")
    
    # Test 1: Direct import
    try:
        from bot.utils.stats_image_generator import StatsImageGenerator
        print("✅ Direct import successful")
        return True
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")
    
    # Test 2: Relative import
    try:
        from utils.stats_image_generator import StatsImageGenerator
        print("✅ Relative import successful")
        return True
    except ImportError as e:
        print(f"❌ Relative import failed: {e}")
    
    # Test 3: Absolute import
    try:
        import utils.stats_image_generator
        StatsImageGenerator = utils.stats_image_generator.StatsImageGenerator
        print("✅ Absolute import successful")
        return True
    except ImportError as e:
        print(f"❌ Absolute import failed: {e}")
    
    return False

def test_dependencies():
    """Test if required dependencies are available."""
    print("\nTesting dependencies...")
    
    dependencies = [
        'matplotlib',
        'numpy', 
        'seaborn',
        'PIL'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            if dep == 'PIL':
                import PIL
            else:
                __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            print(f"❌ {dep} missing")
            missing.append(dep)
    
    return len(missing) == 0

def main():
    """Main test function."""
    print("=" * 50)
    print("STATS IMAGE GENERATOR IMPORT TEST")
    print("=" * 50)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    # Test imports
    import_ok = test_imports()
    
    print("\n" + "=" * 50)
    if deps_ok and import_ok:
        print("✅ All tests passed - StatsImageGenerator should work")
    else:
        print("❌ Some tests failed - Check the issues above")
    print("=" * 50)

if __name__ == "__main__":
    main() 