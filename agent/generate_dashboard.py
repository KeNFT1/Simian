#!/usr/bin/env python3
"""
Generate dashboard.json for Simian dashboard + leaderboard.
Uses Polymarket's on-chain data API as source of truth (not local position files).
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

WALLET = "0xC3499259f08E950031a749353A1422179C28E9C1"
DATA_API = "https://data-api.polymarket.com"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "dashboard.json"
LEADERBOARD_OUTPUT = Path(__file__).resolve().parent.parent / "leaderboard" / "BAYC_2253.json"


def get_onchain_positions():
    """Fetch real positions from Polymarket data API."""
    resp = requests.get(f"{DATA_API}/positions?user={WALLET}", timeout=15)
    if resp.status_code != 200:
        print(f"⚠️ Data API error: {resp.status_code}")
        return []
    return resp.json()


def generate():
    """Generate dashboard + leaderboard JSON from on-chain data."""
    positions = get_onchain_positions()
    
    open_positions = []
    closed_trades = []
    total_initial = 0
    total_current = 0
    total_cash_pnl = 0
    total_realized = 0
    winning = 0
    losing = 0
    
    for p in positions:
        size = float(p.get('size', 0))
        if size <= 0:
            continue
        
        initial = float(p.get('initialValue', 0))
        current = float(p.get('currentValue', 0))
        cash_pnl = float(p.get('cashPnl', 0))
        pct_pnl = float(p.get('percentPnl', 0))
        realized = float(p.get('realizedPnl', 0))
        avg_price = float(p.get('avgPrice', 0))
        cur_price = float(p.get('curPrice', 0))
        redeemable = p.get('redeemable', False)
        
        total_initial += initial
        total_current += current
        total_cash_pnl += cash_pnl
        total_realized += realized
        
        if cash_pnl >= 0:
            winning += 1
        else:
            losing += 1
        
        entry = {
            'question': p.get('title', ''),
            'outcome': p.get('outcome', '?'),
            'entry_price': avg_price,
            'current_price': cur_price,
            'cost_usd': round(initial, 2),
            'current_value': round(current, 2),
            'pnl_usd': round(cash_pnl, 2),
            'pnl_pct': round(pct_pnl, 1),
            'realized_pnl': round(realized, 2),
            'size': size,
            'slug': p.get('slug', ''),
            'end_date': p.get('endDate', ''),
            'redeemable': redeemable,
        }
        
        if redeemable or cur_price == 0:
            closed_trades.append(entry)
        else:
            open_positions.append(entry)
    
    # Sort: open by P&L desc, closed by P&L desc
    open_positions.sort(key=lambda x: x['pnl_usd'], reverse=True)
    closed_trades.sort(key=lambda x: x['pnl_usd'], reverse=True)
    
    total_trades = winning + losing
    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
    
    # Build activity log
    activity = []
    for p in open_positions[:5]:
        emoji = '🟢' if p['pnl_usd'] >= 0 else '🔴'
        activity.append({
            'icon': emoji,
            'text': f"{p['outcome']} {p['question'][:45]} — ${p['pnl_usd']:+.2f} ({p['pnl_pct']:+.1f}%)",
        })
    
    # Load latest intelligence scan if available
    intel_data = {}
    try:
        scan_dir = Path(__file__).resolve().parent.parent.parent / "polymarket-arb" / "data" / "strategy_d_v5"
        latest = scan_dir / "latest.json"
        if latest.exists():
            scan = json.loads(latest.read_text())
            intel_data = {
                'combined': scan.get('intelligence', {}).get('combined', 0),
                'top_signals': scan.get('intelligence', {}).get('top_news', {}),
            }
    except:
        pass
    
    dashboard = {
        'agent': {
            'id': 'lulo-2253',
            'name': 'Lulo',
            'collection': 'BAYC',
            'token_id': 2253,
            'status': 'live',
            'wallet': WALLET,
        },
        'source': 'on-chain (data-api.polymarket.com)',
        'market_scan': {
            'total_tradeable': 12259,
            'after_filters': 364,
        },
        'intelligence': intel_data,
        'open_positions': open_positions,
        'closed_trades': closed_trades,
        'portfolio': {
            'total_deployed': round(total_initial, 2),
            'current_value': round(total_current, 2),
            'unrealized_pnl': round(total_cash_pnl, 2),
            'realized_pnl': round(total_realized, 2),
            'total_pnl': round(total_cash_pnl + total_realized, 2),
            'total_pnl_pct': round((total_cash_pnl / total_initial * 100) if total_initial > 0 else 0, 1),
        },
        'stats': {
            'total_trades': total_trades,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': round(win_rate, 1),
            'open_positions': len(open_positions),
            'resolved_positions': len(closed_trades),
        },
        'recent_activity': list(reversed(activity)),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    
    # Save dashboard
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(dashboard, indent=2))
    
    # Also update leaderboard entry
    leaderboard_entry = {
        'agent_id': 'BAYC_2253',
        'collection': 'BAYC',
        'token_id': 2253,
        'display_name': 'Lulo',
        'ape_image': 'https://i2c.seadn.io/base/0x7e72abdf47bd21bf0ed6ea8cb8dad60579f3fb50/15a6a479d27af55a24429efacb4050/8f15a6a479d27af55a24429efacb4050.png',
        'strategy': 'balanced',
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'performance': {
            'total_pnl_usd': dashboard['portfolio']['total_pnl'],
            'total_pnl_pct': dashboard['portfolio']['total_pnl_pct'],
            'realized_pnl': dashboard['portfolio']['realized_pnl'],
            'unrealized_pnl': dashboard['portfolio']['unrealized_pnl'],
            'total_trades': dashboard['stats']['total_trades'],
            'winning_trades': dashboard['stats']['winning_trades'],
            'losing_trades': dashboard['stats']['losing_trades'],
            'win_rate': dashboard['stats']['win_rate'],
            'best_trade_pnl': max((p['pnl_usd'] for p in open_positions + closed_trades), default=0),
            'worst_trade_pnl': min((p['pnl_usd'] for p in open_positions + closed_trades), default=0),
            'active_positions': len(open_positions),
            'budget_usd': 70,
            'days_active': 7,
        },
        'recent_trades': [
            {
                'question': p['question'][:60],
                'outcome': p['outcome'],
                'pnl': p['pnl_usd'],
            }
            for p in (open_positions + closed_trades)[:5]
        ],
    }
    
    LEADERBOARD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LEADERBOARD_OUTPUT.write_text(json.dumps(leaderboard_entry, indent=2))
    
    print(f"✅ Dashboard: {len(open_positions)} open, {len(closed_trades)} closed")
    print(f"💰 On-chain P&L: ${dashboard['portfolio']['total_pnl']:+.2f} ({dashboard['portfolio']['total_pnl_pct']:+.1f}%)")
    print(f"📊 Win rate: {win_rate:.1f}% ({winning}W / {losing}L)")
    
    return dashboard


if __name__ == '__main__':
    generate()
