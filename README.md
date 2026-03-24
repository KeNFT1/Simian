# Simian — AI Agents with NFT Identity

<div align="center">
  <img src="https://i2c.seadn.io/base/0x7e72abdf47bd21bf0ed6ea8cb8dad60579f3fb50/15a6a479d27af55a24429efacb4050/8f15a6a479d27af55a24429efacb4050.png" alt="Lulo BAYC #2253" width="300px" />
  
  ## Your ape isn't a JPEG. It's an identity. Give it a brain.
  
  **Simian transforms your Bored Ape into an autonomous AI agent that acts on-chain under your NFT's identity—without ever touching your actual token.**
</div>

---

## 🧠 How It Works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Connect       │    │   Delegate      │    │   Configure     │    │   Agent Acts   │
│   Wallet        │───▶│   via           │───▶│   Agent         │───▶│   On-Chain     │
│                 │    │   delegate.cash │    │   Capabilities  │    │   Autonomously  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
  Verify NFT              Agent never              Set risk params         Track P&L &
  ownership               touches your NFT          & preferences           activity
```

### The Process:

1. **🔗 Connect Wallet** → Verify NFT ownership (BAYC, MAYC, CryptoPunks)
2. **🔐 Delegate via delegate.cash** → Grant specific permissions without transferring your NFT
3. **⚙️ Configure Agent Capabilities** → Choose from trading, social, governance, airdrop claiming
4. **🤖 Agent Acts On-Chain** → Your ape's identity drives autonomous actions
5. **📊 Dashboard Monitoring** → Real-time activity, P&L tracking, action logs

---

## 🏗️ Architecture

Simian uses **delegate.cash** as the security foundation, ensuring your NFT never leaves your wallet while granting specific permissions to AI agents.

```
┌─────────────────┐
│  Your Wallet    │
│  ┌───────────┐  │     ┌─────────────────┐     ┌─────────────────┐
│  │    NFT    │  │────▶│  delegate.cash  │────▶│ Simian Registry │
│  │  (BAYC)   │  │     │   Delegation    │     │   Contract      │
│  └───────────┘  │     │    Registry     │     └─────────────────┘
└─────────────────┘     └─────────────────┘              │
                                                          ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   AI Agent      │◀────│ Agent Config &  │
                        │   Runtime       │     │  Capabilities   │
                        └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   On-Chain      │
                        │   Actions       │
                        └─────────────────┘
```

**Security Model:**
- **Delegation-based**: Agent never holds your NFT
- **Revocable**: Cancel delegation anytime via delegate.cash
- **Granular permissions**: Choose which capabilities to enable
- **Non-custodial**: Your NFT stays in your wallet

---

## 🎯 Supported Collections

- **Bored Ape Yacht Club (BAYC)** — Full support
- **Mutant Ape Yacht Club (MAYC)** — Full support  
- **CryptoPunks** — Full support
- **Extensible architecture** for additional collections

---

## 🚀 Agent Capabilities

### 📈 Prediction Market Trading
- Autonomous trading on Polymarket and other prediction markets
- Risk-managed position sizing based on your preferences
- Profit/loss tracking and strategy optimization

### 👁️ Portfolio Monitoring  
- Real-time tracking of your NFT and token holdings
- Market alerts and opportunity notifications
- Performance analytics and insights

### 🗳️ DAO Governance
- Automatic participation in governance proposals
- Voting based on your predefined preferences
- Snapshot integration for off-chain governance

### 📱 Social Posting
- Automated social media presence reflecting your ape's personality
- Community engagement and alpha sharing
- Brand building for your NFT identity

### 🎁 Airdrop Auto-Claim
- Monitor and claim airdrops for eligible NFT holders
- Gas optimization and timing strategies
- Comprehensive claim tracking

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Smart Contracts** | Solidity, delegate.cash integration |
| **Backend** | Python, FastAPI |
| **Blockchain** | Ethereum, Base, Polygon |
| **Identity** | OpenSea API, on-chain metadata |
| **Frontend** | React, Web3.js |
| **AI/ML** | OpenAI GPT-4, custom trading models |
| **Data** | PostgreSQL, Redis |
| **Infrastructure** | AWS, Docker |

---

## 🗺️ Roadmap

### Phase 1: Trading Agent (Q2 2024)
- [ ] Core delegation infrastructure
- [ ] Prediction market trading capabilities
- [ ] Basic dashboard and monitoring
- [ ] BAYC/MAYC support

### Phase 2: Social & Governance (Q3 2024)  
- [ ] DAO governance participation
- [ ] Social media automation
- [ ] Advanced portfolio analytics
- [ ] CryptoPunks support

### Phase 3: Multi-Collection Expansion (Q4 2024)
- [ ] Support for additional NFT collections
- [ ] Advanced AI personality customization
- [ ] Cross-chain capabilities
- [ ] Community marketplace

---

## 🔧 Getting Started

```bash
# Clone the repository
git clone https://github.com/KeNFT1/Simian.git
cd Simian

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy contracts (testnet)
npm run deploy:testnet

# Start the application
npm run dev
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🦍 About

<div align="center">
  
**Built by BAYC holders, for BAYC holders**

<img src="https://img.shields.io/badge/BAYC-%232253-orange" alt="BAYC #2253" />
<img src="https://img.shields.io/badge/Built_by-Lulo_Studios-purple" alt="Lulo Studios" />

*Part of the [Lulo Studios](https://github.com/KeNFT1/lulo-studios) ecosystem*

[@lulodoteth](https://x.com/lulodoteth) • [Lulo Studios](https://github.com/KeNFT1/lulo-studios) • BAYC #2253

</div>