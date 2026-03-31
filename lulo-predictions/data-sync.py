#!/usr/bin/env python3
"""
Lulo Predictions - Data Sync Script
Automatically pulls Strategy D results and updates the dashboard
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

def get_latest_strategy_d_results():
    """Pull latest Strategy D analysis results"""
    try:
        # Path to Strategy D results
        strategy_d_path = Path.home() / ".openclaw" / "workspace" / "polymarket-arb" / "data"
        
        # Find latest strategy_d_intelligence file
        intelligence_files = list(strategy_d_path.glob("strategy_d_intelligence_*.json"))
        if not intelligence_files:
            return None
            
        latest_file = max(intelligence_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        return data
    except Exception as e:
        print(f"Error reading Strategy D data: {e}")
        return None

def get_position_data():
    """Get current position data from Polymarket API"""
    try:
        wallet = "0xC3499259f08E950031a749353A1422179C28E9C1"
        
        # This would call the Polymarket API
        # For now, return mock data structure
        return {
            "positions": [],
            "total_pnl": 0,
            "total_volume": 0
        }
    except Exception as e:
        print(f"Error fetching position data: {e}")
        return None

def calculate_win_rate(signals):
    """Calculate win rate from historical signals"""
    if not signals:
        return 0
    
    resolved_signals = [s for s in signals if s.get('status') in ['WIN', 'LOSS']]
    if not resolved_signals:
        return 0
    
    wins = len([s for s in resolved_signals if s['status'] == 'WIN'])
    return (wins / len(resolved_signals)) * 100

def update_dashboard_data(signals_data):
    """Update the dashboard with latest data"""
    dashboard_data = {
        "last_updated": datetime.now().isoformat(),
        "summary": {
            "total_signals": len(signals_data.get('signals', [])),
            "win_rate": calculate_win_rate(signals_data.get('signals', [])),
            "total_return": signals_data.get('total_pnl', 0),
            "avg_edge": signals_data.get('avg_edge', 0)
        },
        "recent_signals": signals_data.get('signals', [])[-10:],  # Last 10 signals
        "equity_curve": signals_data.get('equity_curve', [])
    }
    
    # Write to dashboard data file
    dashboard_file = Path(__file__).parent / "data" / "dashboard.json"
    dashboard_file.parent.mkdir(exist_ok=True)
    
    with open(dashboard_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"Dashboard updated at {datetime.now()}")

def sync_live_data():
    """Main sync function - pull all data and update dashboard"""
    print("🔄 Syncing live data...")
    
    # Get Strategy D results
    strategy_data = get_latest_strategy_d_results()
    if not strategy_data:
        print("⚠️  No Strategy D data found")
        return
    
    # Get position data
    position_data = get_position_data()
    
    # Combine and process data
    combined_data = {
        **strategy_data,
        "positions": position_data.get('positions', []) if position_data else []
    }
    
    # Update dashboard
    update_dashboard_data(combined_data)
    print("✅ Data sync complete")

if __name__ == "__main__":
    sync_live_data()