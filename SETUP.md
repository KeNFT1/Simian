# 🐵 Simian Agent Setup Guide

**Self-Service AI Trading Agent for BAYC/MAYC Holders**

This guide will help you set up and deploy your own Simian agent for automated prediction market trading.

---

## ⚠️ Important Disclaimers

🚨 **READ THIS FIRST** 🚨

- **This is NOT financial advice** — Trade at your own risk
- **Start with paper trading mode** — Always test before going live
- **Start with small amounts** — When ready for live trading, begin with minimal capital
- **US users need VPN** — Use NordVPN SOCKS5 proxy to access Polymarket
- **Your keys, your responsibility** — Private key security is critical
- **Beta software** — Expect bugs and monitor your agent closely

---

## 📋 Prerequisites

### Required
- **BAYC or MAYC NFT** (verified ownership required)
- **Python 3.8+** installed
- **Git** for cloning the repository
- **Web browser** with MetaMask or compatible Web3 wallet

### For Live Trading (Optional)
- **Polymarket-compatible wallet** with private key
- **USDC funding** for trades
- **VPN with SOCKS5 proxy** (US users only)

---

## 🚀 Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/KeNFT1/Simian.git
cd Simian
```

### 2. Install Dependencies

```bash
pip install -r agent/requirements.txt
```

This installs:
- `requests` — For API calls
- `feedparser` — For RSS intelligence gathering

### 3. Configure Your Strategy

#### Option A: Use the Web Interface

1. Open `builder.html` in your browser
2. Connect your wallet to verify BAYC/MAYC ownership
3. Configure your trading strategy:
   - Choose template (Conservative/Balanced/Aggressive)
   - Set market filters (volume, price range, etc.)
   - Select intelligence sources
   - Configure risk parameters
4. Click "Download Config" to save `agent-config.json`

#### Option B: Use a Template

Copy one of the pre-made templates:

```bash
# Conservative resolution sniping
cp agent/templates/conservative.json agent-config.json

# Balanced geopolitical trading  
cp agent/templates/balanced.json agent-config.json

# Aggressive wide net
cp agent/templates/aggressive.json agent-config.json
```

### 4. Test with Paper Trading

**Start with simulation mode** to test your strategy:

```bash
python agent/runner.py --config agent-config.json
```

This will:
- Scan active Polymarket markets
- Gather intelligence from news sources
- Score markets and identify opportunities  
- Show what trades it WOULD make (no real money)
- Save results to `data/simulations/`

### 5. Review Results

Check the simulation results:

```bash
ls data/simulations/
cat data/simulations/2024-XX-XX_HHMMSS.json
```

Review:
- **Markets identified** — Are they relevant?
- **Edge calculations** — Do they make sense?
- **Position sizing** — Appropriate for your risk tolerance?
- **Intelligence signals** — Quality and relevance

### 6. Iterate and Improve

Adjust your configuration based on paper trading results:

1. Edit your `agent-config.json` file
2. Re-run paper trading
3. Compare results
4. Repeat until satisfied

---

## 🔴 Going Live (Advanced)

⚠️ **Only proceed if you're comfortable with the risks and have tested thoroughly in paper mode.**

### 1. Set Up Environment Variables

Create a `.env` file:

```bash
# Your Polymarket-compatible private key (NEVER SHARE THIS)
POLYMARKET_PRIVATE_KEY=your_private_key_here

# For US users - SOCKS5 proxy URL
SOCKS5_PROXY_URL=socks5://username:password@proxy.nordvpn.com:1080
```

### 2. Enable Live Trading

Edit your `agent-config.json`:

```json
{
  "execution": {
    "autoExecute": true,
    "cronInterval": "4h"
  }
}
```

### 3. Fund Your Wallet

- Transfer USDC to your trading wallet
- Start with a small amount (e.g., $50-100)
- Ensure you have ETH for gas fees

### 4. Run Live Agent

```bash
python agent/runner.py --config agent-config.json
```

The agent will now execute real trades! Monitor the output carefully.

---

## 🤖 Automation (Optional)

### Set Up Cron Job

To run your agent automatically:

```bash
crontab -e
```

Add a line based on your desired interval:

```bash
# Every 4 hours
0 */4 * * * cd /path/to/Simian && python agent/runner.py --config agent-config.json

# Every hour
0 * * * * cd /path/to/Simian && python agent/runner.py --config agent-config.json

# Once daily at 9 AM
0 9 * * * cd /path/to/Simian && python agent/runner.py --config agent-config.json
```

### Monitor Logs

Track your agent's activity:

```bash
# Real-time monitoring
tail -f data/live/latest.log

# Check recent results
ls -la data/live/
```

---

## 🛠️ Configuration Reference

### Market Filters

```json
"marketFilters": {
  "excludeSports": true,           // Skip sports betting
  "excludeMeme": true,             // Skip gaming/meme markets  
  "minVolume": 10000,             // Minimum $10k volume
  "priceRange": {
    "min": 10,                    // 10¢ minimum price
    "max": 90                     // 90¢ maximum price
  },
  "maxDaysToResolution": 180      // Max 180 days to resolution
}
```

### Intelligence Sources

```json
"intelligenceSources": {
  "hackernews": true,             // Tech trends
  "reddit": true,                 // Social sentiment
  "bbc": true,                    // Breaking news
  "googleNews": true,             // Global news
  "nitter": false,                // Twitter/X trends (limited)
  "customKeywords": [             // Your focus areas
    "fed", "ukraine", "bitcoin", "election"
  ]
}
```

### Risk Parameters

```json
"riskParameters": {
  "budget": 50,                   // Total budget ($50)
  "maxPerPosition": 10,           // Max $10 per trade
  "maxConcurrentPositions": 5,    // Max 5 open positions
  "minEdgeThreshold": 0.04,       // 4% minimum edge required
  "kellyFraction": 0.25           // Quarter Kelly sizing
}
```

---

## 🔧 Troubleshooting

### Common Issues

**"No markets found"**
- Check your filters — they might be too restrictive
- Verify Polymarket API is accessible
- Try running with `--debug` flag

**"Intelligence gathering failed"**  
- Check internet connection
- Some sources may be temporarily down
- Review which sources are enabled

**"Insufficient budget"**
- Increase your budget in config
- Lower your `maxPerPosition` setting
- Reduce `maxConcurrentPositions`

**"Connection refused" (US users)**
- Set up SOCKS5 proxy in `.env` file
- Verify VPN is connected
- Test proxy connection separately

### Debug Mode

Run with debug logging:

```bash
python agent/runner.py --config agent-config.json --debug
```

### Get Help

- Check logs in `data/` directories
- Review configuration against templates
- Ensure wallet has sufficient funds
- Verify NFT ownership via `builder.html`

---

## 📊 Understanding Results

### Paper Trading Output

```json
{
  "timestamp": "2024-03-23T22:00:00",
  "markets_scanned": 45,
  "profitable_markets": 3,
  "trades_executed": 3,
  "details": [
    {
      "title": "Will Fed raise rates in March?",
      "edge": 0.08,
      "confidence": 0.75,
      "position_size": 12.50,
      "signals": 5
    }
  ]
}
```

### Key Metrics

- **Edge** — Expected profit percentage
- **Confidence** — Signal strength (0-1)
- **Position Size** — Dollar amount to risk
- **Signals** — Number of supporting intelligence items

---

## 🚨 Security Best Practices

### Private Key Safety
- **Never share your private key**
- Store in secure password manager
- Use a dedicated trading wallet (not your main holdings)
- Consider hardware wallet for larger amounts

### Risk Management
- Start with paper trading
- Begin live trading with minimal amounts
- Set strict budget limits
- Monitor positions regularly
- Have a stop-loss strategy

### Operational Security
- Use VPN when required
- Keep software updated
- Monitor for unusual activity
- Have backup/recovery plan

---

## 📞 Support

### Resources
- **Documentation**: Check README.md and source code comments
- **Templates**: Study the strategy templates for examples
- **Logs**: Review output logs for troubleshooting

### Community
- **GitHub**: [Issues and discussions](https://github.com/KeNFT1/Simian/issues)
- **Twitter**: [@lulodoteth](https://x.com/lulodoteth) for updates
- **Discord**: BAYC/MAYC holder channels

---

## ✅ Final Checklist

Before going live:

- [ ] Successfully run paper trading for multiple cycles
- [ ] Reviewed and understood all trade decisions
- [ ] Set appropriate risk parameters for your situation
- [ ] Secured private key and environment variables
- [ ] Set up VPN/proxy if in restricted region
- [ ] Funded wallet with small test amount
- [ ] Have monitoring and alerting in place
- [ ] Understand how to stop/pause the agent

Remember: **Your ape, your agent, your responsibility**. Trade wisely! 🐵

---

*Built by BAYC holders, for BAYC holders. BAYC #2253 "Lulo"*