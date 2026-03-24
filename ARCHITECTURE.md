# Simian Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        NFT HOLDER                             │
│                   (Cold Wallet + BAYC)                         │
└──────────────────────┬───────────────────────────────────────┘
                       │ delegate via delegate.cash
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                   DELEGATE.CASH REGISTRY                      │
│              (On-chain, immutable, revocable)                  │
│                                                               │
│  Cold Wallet ──delegates──> Hot Wallet (Simian Agent)         │
│  Token: BAYC #2253                                            │
│  Rights: ALL or specific (TRADE, GOVERN, CLAIM)               │
└──────────────────────┬───────────────────────────────────────┘
                       │ verified delegation
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    SIMIAN REGISTRY                             │
│                 (SimianRegistry.sol)                           │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Verify      │  │ Agent Config │  │ Capability       │    │
│  │ Delegation  │  │ Storage      │  │ Bitmask          │    │
│  │ (delegate.  │  │ (NFT → Agent │  │ TRADE|SOCIAL|    │    │
│  │  cash)      │  │  settings)   │  │ GOVERN|CLAIM     │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                      SIMIAN AGENT                             │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Identity │  │ Trading  │  │ Social   │  │ Claims   │    │
│  │          │  │          │  │          │  │          │    │
│  │ NFT meta │  │ Poly-    │  │ X/Fcast  │  │ Airdrop  │    │
│  │ Traits   │  │ market   │  │ posting  │  │ auto-    │    │
│  │ Name     │  │ Hyper-   │  │ DAO      │  │ claim    │    │
│  │ Image    │  │ liquid   │  │ votes    │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    Delegator                          │    │
│  │  Verifies delegation before EVERY on-chain action     │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Security Model

### Core Principle: Agent Never Holds the NFT

The NFT stays in the cold wallet at all times. The agent operates through
delegate.cash delegation, which:

1. **Is on-chain** — delegation is stored in an immutable smart contract
2. **Is revocable** — owner can revoke delegation at any time
3. **Is verifiable** — any contract/dApp can check if delegation is valid
4. **Is granular** — can delegate specific tokens, collections, or all

### Verification Flow

```
Agent wants to act on behalf of BAYC #2253
    │
    ├── Check delegate.cash: Is hot_wallet delegated for this token?
    │   ├── YES → Proceed with action
    │   └── NO  → Reject action, alert owner
    │
    ├── Check SimianRegistry: Is this agent configured for this capability?
    │   ├── TRADE bit set → Allow trading actions
    │   ├── SOCIAL bit set → Allow social posting
    │   ├── GOVERN bit set → Allow governance votes
    │   └── CLAIM bit set → Allow airdrop claims
    │
    └── Execute action from hot wallet
```

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| Agent compromised | Only hot wallet at risk, NFT safe in cold wallet |
| Delegation revoked | Agent checks delegation before every action |
| Malicious contract | Agent only interacts with whitelisted contracts |
| Front-running | MEV protection via Flashbots/private transactions |
| Key exposure | Hot wallet has limited funds, cold wallet untouched |

## Integration Points

### delegate.cash Registry
- **Contract**: `0x00000000000000447e69651d841bD8D104Bed493` (v2)
- **Interface**: `IDelegationRegistry`
- **Key methods**: 
  - `checkDelegateForERC721()` — verify token-level delegation
  - `checkDelegateForContract()` — verify collection-level delegation
  - `checkDelegateForAll()` — verify wallet-level delegation

### OpenSea API
- Fetch NFT metadata (traits, image, name)
- Verify ownership
- Get collection floor price

### Polymarket / Hyperliquid
- Trading execution (existing infrastructure from prediction-markets repo)
- Position management, P&L tracking

### Snapshot / Tally
- DAO governance voting
- Proposal monitoring
- Vote delegation

### X / Farcaster
- Social posting under ape identity
- Community engagement
- Automated content generation

## Data Flow

```
1. SETUP
   Owner connects cold wallet → verifies NFT → delegates to hot wallet
   Hot wallet registered in SimianRegistry with capabilities

2. RUNTIME (every cycle)
   Agent wakes up → checks delegation (still valid?) → loads identity
   → scans for opportunities (markets, votes, airdrops, social)
   → executes actions within configured capabilities
   → logs results → reports to owner

3. TEARDOWN
   Owner revokes delegation → agent detects revocation → shuts down
   All funds in hot wallet returned to owner
```

## Supported Collections (Phase 1+)

| Collection | Token Standard | Notes |
|-----------|---------------|-------|
| BAYC | ERC-721 | Primary, full support |
| MAYC | ERC-721 | Same Yuga ecosystem |
| CryptoPunks | Custom (wrapped ERC-721) | Needs wrapper support |
| Azuki | ERC-721 | Strong delegate.cash adoption |
| *Extensible* | ERC-721 / ERC-1155 | Any collection can be added |
