#!/usr/bin/env python3
"""
Simian Setup Test Script
Run this to verify your environment is properly configured.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add agent directory to path
sys.path.append('agent')

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - run: pip install requests")
        return False
    
    try:
        import feedparser
        print("✅ feedparser")
    except ImportError:
        print("❌ feedparser - run: pip install feedparser")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp")
    except ImportError:
        print("❌ aiohttp - run: pip install aiohttp")
        return False
    
    try:
        from intelligence import IntelligenceGatherer
        print("✅ intelligence module")
    except ImportError as e:
        print(f"❌ intelligence module - {e}")
        return False
    
    try:
        from market_scanner import MarketScanner
        print("✅ market_scanner module")
    except ImportError as e:
        print(f"❌ market_scanner module - {e}")
        return False
    
    try:
        from scorer import MarketScorer
        print("✅ scorer module")
    except ImportError as e:
        print(f"❌ scorer module - {e}")
        return False
    
    try:
        from executor import PaperTrader
        print("✅ executor module")
    except ImportError as e:
        print(f"❌ executor module - {e}")
        return False
    
    return True

def test_config_files():
    """Test that config templates exist and are valid."""
    print("\n📋 Testing config templates...")
    
    templates = ['conservative.json', 'balanced.json', 'aggressive.json']
    
    for template in templates:
        path = Path(f'agent/templates/{template}')
        if not path.exists():
            print(f"❌ Missing template: {template}")
            return False
        
        try:
            with open(path) as f:
                config = json.load(f)
            
            # Check required keys
            required_keys = ['marketFilters', 'intelligenceSources', 'riskParameters', 'execution']
            for key in required_keys:
                if key not in config:
                    print(f"❌ {template} missing key: {key}")
                    return False
            
            print(f"✅ {template}")
            
        except json.JSONDecodeError as e:
            print(f"❌ {template} invalid JSON: {e}")
            return False
    
    return True

async def test_intelligence():
    """Test intelligence gathering."""
    print("\n🧠 Testing intelligence gathering...")
    
    try:
        from intelligence import IntelligenceGatherer
        
        config = {
            'hackernews': True,
            'reddit': False,  # Disable to avoid rate limits
            'bbc': True,
            'googleNews': False,  # Disable to avoid rate limits
            'nitter': False,
            'customKeywords': []
        }
        
        ig = IntelligenceGatherer(config)
        
        # Test HackerNews
        hn_data = await ig.gather_hackernews()
        if hn_data:
            print(f"✅ HackerNews: {len(hn_data)} items")
        else:
            print("⚠️  HackerNews: no items (may be API issue)")
        
        # Test BBC RSS
        bbc_data = await ig.gather_bbc_rss()
        if bbc_data:
            print(f"✅ BBC RSS: {len(bbc_data)} items")
        else:
            print("⚠️  BBC RSS: no items (may be feed issue)")
        
        return True
        
    except Exception as e:
        print(f"❌ Intelligence test failed: {e}")
        return False

async def test_market_scanner():
    """Test market scanning."""
    print("\n📊 Testing market scanner...")
    
    try:
        from market_scanner import MarketScanner
        
        config = {
            'minVolume': 1000,
            'priceRange': {'min': 5, 'max': 95},
            'maxDaysToResolution': 365,
            'excludeSports': False,
            'excludeMeme': False
        }
        
        scanner = MarketScanner(config)
        markets = await scanner.fetch_gamma_markets()
        
        if markets:
            print(f"✅ Market scanning: {len(markets)} markets found")
            print(f"   Sample: {markets[0].get('title', 'No title')[:50]}...")
        else:
            print("⚠️  Market scanning: no markets found (Gamma API may be down)")
        
        return True
        
    except Exception as e:
        print(f"❌ Market scanner test failed: {e}")
        return False

def test_directories():
    """Test that required directories exist."""
    print("\n📁 Testing directories...")
    
    directories = [
        'agent',
        'agent/templates',
        'data',
        'data/simulations'
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            print(f"❌ Missing directory: {directory}")
            print(f"   Creating: {directory}")
            path.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ {directory}")
    
    return True

async def main():
    """Run all tests."""
    print("🐵 Simian Setup Test\n")
    print("This script verifies your Simian agent environment is properly configured.\n")
    
    tests = [
        ("Python Dependencies", test_imports()),
        ("Configuration Templates", test_config_files()),
        ("Directory Structure", test_directories()),
        ("Intelligence Gathering", await test_intelligence()),
        ("Market Scanner", await test_market_scanner())
    ]
    
    print(f"\n{'='*50}")
    print("Test Results:")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"{'='*50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your Simian agent is ready to use.")
        print("\nNext steps:")
        print("1. Open builder.html to configure your strategy")
        print("2. Download your config file")
        print("3. Run: python agent/runner.py --config your-config.json --summary")
        print("4. Run: python agent/runner.py --config your-config.json (paper trading)")
    else:
        print(f"\n⚠️  {len(tests) - passed} test(s) failed. Please fix the issues above before proceeding.")

if __name__ == '__main__':
    asyncio.run(main())