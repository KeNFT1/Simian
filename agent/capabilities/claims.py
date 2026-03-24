"""
Simian — Airdrop Auto-Claim Capability

Monitors for airdrops targeting the delegated NFT collection and
auto-claims via the hot wallet using delegate.cash verification.

Flow:
  1. Monitor known airdrop contracts for eligible claims
  2. Verify delegation is active via delegate.cash registry
  3. Submit claim transaction from hot wallet
  4. Log claim result and notify owner
"""

from typing import Optional, Dict, List


class AirdropClaimer:
    """Auto-claim airdrops for delegated NFT holders."""

    def __init__(self, config: dict):
        self.enabled = config.get("claims_enabled", False)
        self.auto_claim = config.get("auto_claim", False)
        self.notify_before_claim = config.get("notify_before_claim", True)
        self.max_gas_gwei = config.get("max_gas_gwei", 50)
        self.monitored_contracts: List[str] = config.get("monitored_contracts", [])

    async def check_eligible_claims(self, token_id: int, collection: str) -> List[Dict]:
        """Check if any airdrops are available for this NFT.
        
        TODO:
        - Query known airdrop contracts (Yuga, BAYC ecosystem)
        - Check Merkle proof eligibility
        - Return list of claimable airdrops with value estimates
        """
        raise NotImplementedError("Airdrop monitoring not yet implemented")

    async def execute_claim(self, airdrop_contract: str, token_id: int, 
                           proof: list, hot_wallet: str) -> Dict:
        """Execute an airdrop claim via the delegated hot wallet.
        
        TODO:
        - Verify delegation is still active
        - Estimate gas and check against max_gas_gwei
        - Submit claim transaction
        - Wait for confirmation
        - Return claim result
        """
        raise NotImplementedError("Claim execution not yet implemented")

    async def get_claim_history(self, token_id: int) -> List[Dict]:
        """Get history of claims made by this agent.
        
        TODO:
        - Query local database for past claims
        - Include tx hash, value, timestamp
        """
        raise NotImplementedError("Claim history not yet implemented")
