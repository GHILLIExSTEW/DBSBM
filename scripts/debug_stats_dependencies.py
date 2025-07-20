#!/usr/bin/env python3
"""
Debug script to test StatsImageGenerator instantiation and usage.
"""

import sys
import os
import traceback

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

def test_import():
    """Test importing StatsImageGenerator."""
    print("1. Testing import...")
    try:
        from utils.stats_image_generator import StatsImageGenerator
        print("✅ Import successful")
        return StatsImageGenerator
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return None

def test_instantiation(StatsImageGenerator):
    """Test creating an instance of StatsImageGenerator."""
    print("\n2. Testing instantiation...")
    try:
        generator = StatsImageGenerator()
        print("✅ Instantiation successful")
        return generator
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        traceback.print_exc()
        return None

def test_methods(generator):
    """Test calling methods on the generator."""
    print("\n3. Testing methods...")
    
    # Test data
    test_stats = {
        "total_bets": 100,
        "total_cappers": 10,
        "total_units": 500.0,
        "net_units": 50.0,
        "wins": 60,
        "losses": 35,
        "pushes": 5,
        "leaderboard": [
            {"username": "User1", "net_units": 25.0},
            {"username": "User2", "net_units": 15.0}
        ]
    }
    
    try:
        # Test generate_guild_stats_image
        print("Testing generate_guild_stats_image...")
        image = generator.generate_guild_stats_image(test_stats)
        print("✅ generate_guild_stats_image successful")
        
        # Test generate_capper_stats_image
        print("Testing generate_capper_stats_image...")
        image = generator.generate_capper_stats_image(test_stats, "TestUser")
        print("✅ generate_capper_stats_image successful")
        
        return True
    except Exception as e:
        print(f"❌ Method test failed: {e}")
        traceback.print_exc()
        return False

def test_matplotlib_backend():
    """Test matplotlib backend configuration."""
    print("\n4. Testing matplotlib backend...")
    try:
        import matplotlib
        print(f"Matplotlib version: {matplotlib.__version__}")
        print(f"Backend: {matplotlib.get_backend()}")
        
        # Test if we can create a simple plot
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])
        plt.close(fig)
        print("✅ Matplotlib plotting works")
        return True
    except Exception as e:
        print(f"❌ Matplotlib test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("=" * 60)
    print("STATS IMAGE GENERATOR COMPREHENSIVE DEBUG")
    print("=" * 60)
    
    # Test 1: Import
    StatsImageGenerator = test_import()
    if not StatsImageGenerator:
        return
    
    # Test 2: Instantiation
    generator = test_instantiation(StatsImageGenerator)
    if not generator:
        return
    
    # Test 3: Matplotlib backend
    matplotlib_ok = test_matplotlib_backend()
    if not matplotlib_ok:
        print("\n⚠️  Matplotlib backend issues detected")
    
    # Test 4: Methods
    methods_ok = test_methods(generator)
    
    print("\n" + "=" * 60)
    if methods_ok:
        print("✅ All tests passed - StatsImageGenerator should work in bot")
    else:
        print("❌ Some tests failed - Check the issues above")
    print("=" * 60)

if __name__ == "__main__":
    main() 