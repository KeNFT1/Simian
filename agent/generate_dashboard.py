#!/usr/bin/env python3
"""
Generate dashboard.json for Lulo's public Simian dashboard.
Reads from Strategy D v5 + E v5 position files and latest scan results.
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

POLYMARKET_ARB = Path(__file__).resolve().parent.parent.parent / "polymarket-arb"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "dashboard.json"


def load_positions():
    """Load all open positions from Strategy D and E."""
    open_positions = []
    closed_trades = []
    
    for strat in ['d', 'e']:
        pos_file = POLYMARKET_ARB / "data" / f"real_positions_{strat}.json"
        if not pos_file.exists():
            continue
        positions = json.loads(pos_file.read_text())
        
        for p in positions:
            entry = p.get('entry_price', p.get('price', 0))
            token_id = p.get('token_id', '')
            
            if p.get('status') == 'OPEN':
                # Get live price
                mid = 0
                try:
                    resp = requests.get('https://clob.polymarket.com/midpoint',
                                       params={'token_id': token_id}, timeout=5)
                    mid = float(resp.json().get('mid', 0))
                except:
                    mid = entry
                
                shares = p.get('shares', p.get('size', 0))
                pnl = shares * (mid - entry) if mid > 0 and entry > 0 else 0
                pnl_pct = ((mid - entry) / entry * 100) if entry > 0 else 0
                
                open_positions.append({
                    'question': p.get('question', ''),
                    'outcome': p.get('outcome', '?'),
                    'entry_price': entry,
                    'current_price': mid,
                    'cost_usd': p.get('cost_usd', 0),
                    'pnl_usd': round(pnl, 2),
                    'pnl_pct': round(pnl_pct, 1),
                    'edge': p.get('edge', 0),
                    'strategy': strat.upper(),
                    'version': p.get('version', '?'),
                })
            else:
                closed_trades.append({
                    'question': p.get('question', ''),
                    'outcome': p.get('outcome', '?'),
                    'realized_pnl': p.get('realized_pnl', 0),
                    'close_reason': p.get('close_reason', '?'),
                })
    
    return open_positions, closed_trades


def load_latest_scan():
    """Load latest Strategy D v5 scan results."""
    latest_file = POLYMARKET_ARB / "data" / "strategy_d_v5" / "latest.json"
    if latest_file.exists():
        return json.loads(latest_file.read_text())
    return {}


def generate():
    """Generate dashboard JSON."""
    open_positions, closed_trades = load_positions()
    scan = load_latest_scan()
    
    # Calculate realized P&L
    realized = sum(t.get('realized_pnl', 0) for t in closed_trades)
    unrealized = sum(p.get('pnl_usd', 0) for p in open_positions)
    
    # Recent activity
    activity = []
    for t in closed_trades[-5:]:
        pnl = t.get('realized_pnl', 0)
        emoji = '💰' if pnl > 0 else '📉'
        activity.append({
            'icon': emoji,
            'text': f"{t['outcome']} {t['question'][:50]} — ${pnl:+.2f} ({t['close_reason']})",
        })
    
    for p in open_positions[-5:]:
        activity.append({
            'icon': '🎯',
            'text': f"Opened {p['outcome']} {p['question'][:50]} — ${p['cost_usd']:.2f}",
        })
    
    dashboard = {
        'agent': {
            'id': 'lulo-2253',
            'name': 'Lulo',
            'collection': 'BAYC',
            'token_id': 2253,
            'status': 'live',
        },
        'market_scan': scan.get('market_scan', {}),
        'intelligence': {
            'combined': scan.get('intelligence', {}).get('combined', 0),
            'top_signals': scan.get('intelligence', {}).get('top_news', {}),
        },
        'open_positions': sorted(open_positions, key=lambda x: abs(x.get('pnl_pct', 0)), reverse=True),
        'closed_trades': closed_trades,
        'realized_pnl': round(realized, 2),
        'unrealized_pnl': round(unrealized, 2),
        'total_pnl': round(realized + unrealized, 2),
        'recent_activity': list(reversed(activity)),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(dashboard, indent=2))
    print(f"✅ Dashboard generated: {len(open_positions)} open, {len(closed_trades)} closed, P&L: ${realized + unrealized:+.2f}")
    return dashboard


if __name__ == '__main__':
    generate()
