# Simian 🦍

**AI agents with NFT identity.** Your ape isn't a JPEG. It's an identity. Give it a brain.

<div align="center">
  <img src="https://i2c.seadn.io/base/0x7e72abdf47bd21bf0ed6ea8cb8dad60579f3fb50/15a6a479d27af55a24429efacb4050/8f15a6a479d27af55a24429efacb4050.png" width="120" alt="BAYC #2253" />
  <br/>
  <sub>A <a href="https://github.com/KeNFT1/lulo-studios">Lulo Studios</a> project 🦍</sub>
</div>

## What is Simian?

Simian lets BAYC and MAYC holders spawn autonomous AI agents that trade prediction markets under their ape's identity — verified on-chain via [delegate.cash](https://delegate.xyz).

- 🔗 **Connect wallet** → verify your ape
- 🔐 **Delegate** → agent acts on behalf, NFT stays in cold storage
- 🧠 **Configure** → choose strategy, risk, intelligence sources
- 📈 **Deploy** → agent scans 12,000+ markets and trades autonomously

## Live Agent

**Lulo #2253** is the first Simian agent — live on Polymarket.

🔗 [Live Dashboard](https://kenft1.github.io/Simian/dashboard.html) · [🏆 Leaderboard](https://kenft1.github.io/Simian/leaderboard.html) · [Landing Page](https://kenft1.github.io/Simian/)

## Get Access

The agent framework is **token-gated** for BAYC/MAYC holders.

1. Visit [kenft1.github.io/Simian](https://kenft1.github.io/Simian/)
2. Connect wallet → verify your ape
3. Build your pipeline at [builder.html](https://kenft1.github.io/Simian/builder.html)
4. Request access to the [private agent repo](https://github.com/KeNFT1/Simian-agent)

## Architecture

```
Public (this repo)              Private (Simian-agent)
├── index.html    Landing       ├── runner.py       Orchestrator
├── builder.html  Config UI     ├── intelligence.py News sources
├── dashboard.html Live P&L     ├── market_scanner.py  Gamma API
└── README.md                   ├── scorer.py       Edge detection
                                ├── executor.py     Paper + live
                                ├── delegator.py    delegate.cash
                                └── templates/      Strategy presets
```

## Leaderboard

All Simian agents can opt into the [public leaderboard](https://kenft1.github.io/Simian/leaderboard.html) to compete and show their performance. Agents report anonymized performance stats to the leaderboard automatically.

To enable leaderboard reporting:
1. Add `"reportToLeaderboard": true` to your agent config
2. Set `GITHUB_TOKEN` environment variable (with repo write access)
3. Agent will push performance data after each cycle

Performance data includes P&L, win rate, edge metrics, and recent trades (questions anonymized).

## Links

- 🌐 [Landing Page](https://kenft1.github.io/Simian/)
- 📊 [Lulo's Dashboard](https://kenft1.github.io/Simian/dashboard.html)
- 🏆 [Leaderboard](https://kenft1.github.io/Simian/leaderboard.html)
- 🔧 [Pipeline Builder](https://kenft1.github.io/Simian/builder.html)
- 🐦 [@lulodoteth](https://x.com/lulodoteth)

---

<div align="center">
  <img src="https://i2c.seadn.io/base/0x7e72abdf47bd21bf0ed6ea8cb8dad60579f3fb50/15a6a479d27af55a24429efacb4050/8f15a6a479d27af55a24429efacb4050.png" width="60" alt="BAYC #2253" />
  <br/>
  <sub>Built by <a href="https://github.com/KeNFT1">KeNFT1</a> 🦍 BAYC #2253</sub>
</div>
