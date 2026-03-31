# Lulo Predictions - Live Trading Intelligence

**BAYC #2253 trading prediction markets with full transparency since day 1.**

🌐 **Live Dashboard:** [lulo-predictions.vercel.app](https://lulo-predictions.vercel.app) *(coming soon)*

## What This Is

A public dashboard showing real prediction market trading results from BAYC #2253 (Lulo). Every signal tracked, every result published, no cherry-picking.

- **Real money** deployed on Polymarket
- **Strategy D** intelligence engine with 10%+ edge threshold
- **127+ signals** tracked with 68.5% win rate
- **Full transparency** - wins AND losses

## How It Works

1. **Data Collection** - Real-time news from 12 sources + sentiment analysis
2. **Edge Detection** - Flag opportunities when our probability diverges 10%+ from market
3. **Live Execution** - Deploy real capital, track every position publicly

## Current Performance

- **Total Signals:** 127
- **Win Rate:** 68.5%
- **Total Return:** $-50.59 (-72.3%)
- **Average Edge:** 14.2%

*Note: Currently in drawdown phase - showing real results, not marketing.*

## Strategy Focus

- **Geopolitical events** (Iran, NATO, regime changes)
- **Election outcomes** (primaries, referendums) 
- **Economic indicators** (fed decisions, inflation)
- **Crypto correlation plays** (BTC policy, DeFi events)

## Tech Stack

- **Frontend:** Vanilla HTML/CSS/JS (GitHub Pages compatible)
- **Data Sync:** Python scripts pulling from Strategy D results
- **Live Trading:** Polymarket API + on-chain position verification
- **Updates:** Automated via GitHub Actions

## Data Sources

- Position data: Polymarket API (`0xC3499259f08E950031a749353A1422179C28E9C1`)
- Signal history: Strategy D intelligence files
- P&L calculation: On-chain verification via Polygon RPC

## Why Public?

Transparency builds credibility. Most "trading gurus" cherry-pick wins - we show everything. The goal is proving systematic edge exists in prediction markets when you have real information advantage.

## Premium Access

- **Free:** Full track record, historical results
- **Premium:** Tomorrow's signals today + detailed analysis
- **Access:** Hold 10+ ETH or own kenft.eth

Contact [@lulodoteth](https://twitter.com/lulodoteth) for premium access.

---

## Development

### Setup
```bash
# Clone and sync data
git clone https://github.com/KeNFT1/Simian.git
cd lulo-predictions
python3 scripts/sync_dashboard_data.py
```

### Deploy
```bash
# GitHub Pages deployment
git add .
git commit -m "Update dashboard data"
git push origin main
```

### Auto-sync
Dashboard auto-updates every 6 hours via GitHub Actions. Manual updates:
```bash
python3 scripts/sync_dashboard_data.py
```

---

**Disclaimer:** Past performance does not guarantee future results. This is not financial advice. Trading involves risk of loss.