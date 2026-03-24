#!/usr/bin/env python3
"""
Simian Delegation Verifier

Verifies on-chain delegation via delegate.cash v2 registry.
Checks that a hot wallet is authorized to act on behalf of a specific NFT.

delegate.cash v2 registry: 0x00000000000000447e69651d841bD8D104Bed493
Deployed on: Ethereum mainnet, Polygon, Arbitrum, Optimism, Base, etc.

Key methods:
  - checkDelegateForERC721(delegate, vault, contract, tokenId, rights)
  - checkDelegateForContract(delegate, vault, contract, rights) 
  - checkDelegateForAll(delegate, vault, rights)
"""

import json
from typing import Optional
from pathlib import Path

# delegate.cash v2 registry address (same on all chains)
DELEGATE_REGISTRY_V2 = "0x00000000000000447e69651d841bD8D104Bed493"

# BAYC contract
BAYC_CONTRACT = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"

# Minimal ABI for delegate.cash v2 read methods
DELEGATE_REGISTRY_ABI = json.loads('''[
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "from", "type": "address"},
            {"name": "contract_", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
            {"name": "rights", "type": "bytes32"}
        ],
        "name": "checkDelegateForERC721",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "from", "type": "address"},
            {"name": "contract_", "type": "address"},
            {"name": "rights", "type": "bytes32"}
        ],
        "name": "checkDelegateForContract",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "from", "type": "address"},
            {"name": "rights", "type": "bytes32"}
        ],
        "name": "checkDelegateForAll",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# ERC-721 ownerOf ABI
ERC721_ABI = json.loads('''[
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# Empty rights = delegate for everything
EMPTY_RIGHTS = b'\x00' * 32


class DelegationVerifier:
    """Verify delegate.cash delegations on-chain."""
    
    def __init__(self, rpc_url: str = "https://eth.llamarpc.com"):
        try:
            from web3 import Web3
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            self.registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(DELEGATE_REGISTRY_V2),
                abi=DELEGATE_REGISTRY_ABI,
            )
            self.connected = self.w3.is_connected()
        except ImportError:
            print("⚠️ web3 not installed. Run: pip install web3")
            self.w3 = None
            self.connected = False
    
    def verify_nft_ownership(self, contract_address: str, token_id: int) -> Optional[str]:
        """Check who owns a specific NFT. Returns owner address or None."""
        if not self.w3:
            return None
        
        from web3 import Web3
        nft_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=ERC721_ABI,
        )
        
        try:
            owner = nft_contract.functions.ownerOf(token_id).call()
            return owner
        except Exception as e:
            print(f"❌ ownerOf failed: {e}")
            return None
    
    def check_delegation_for_token(
        self,
        hot_wallet: str,
        cold_wallet: str,
        contract_address: str,
        token_id: int,
        rights: bytes = EMPTY_RIGHTS,
    ) -> bool:
        """Check if hot_wallet is delegated for a specific token."""
        if not self.w3:
            return False
        
        from web3 import Web3
        try:
            result = self.registry.functions.checkDelegateForERC721(
                Web3.to_checksum_address(hot_wallet),
                Web3.to_checksum_address(cold_wallet),
                Web3.to_checksum_address(contract_address),
                token_id,
                rights,
            ).call()
            return bool(result)
        except Exception as e:
            print(f"❌ checkDelegateForERC721 failed: {e}")
            return False
    
    def check_delegation_for_contract(
        self,
        hot_wallet: str,
        cold_wallet: str,
        contract_address: str,
        rights: bytes = EMPTY_RIGHTS,
    ) -> bool:
        """Check if hot_wallet is delegated for an entire collection."""
        if not self.w3:
            return False
        
        from web3 import Web3
        try:
            result = self.registry.functions.checkDelegateForContract(
                Web3.to_checksum_address(hot_wallet),
                Web3.to_checksum_address(cold_wallet),
                Web3.to_checksum_address(contract_address),
                rights,
            ).call()
            return bool(result)
        except Exception as e:
            print(f"❌ checkDelegateForContract failed: {e}")
            return False
    
    def check_delegation_for_all(
        self,
        hot_wallet: str,
        cold_wallet: str,
        rights: bytes = EMPTY_RIGHTS,
    ) -> bool:
        """Check if hot_wallet is delegated for ALL assets from cold_wallet."""
        if not self.w3:
            return False
        
        from web3 import Web3
        try:
            result = self.registry.functions.checkDelegateForAll(
                Web3.to_checksum_address(hot_wallet),
                Web3.to_checksum_address(cold_wallet),
                rights,
            ).call()
            return bool(result)
        except Exception as e:
            print(f"❌ checkDelegateForAll failed: {e}")
            return False
    
    def full_verification(self, agent_config: dict) -> dict:
        """Run full verification for a Simian agent.
        
        Checks:
        1. NFT ownership (who holds the token?)
        2. Token-level delegation
        3. Contract-level delegation (fallback)
        4. Wallet-level delegation (fallback)
        
        Returns verification result dict.
        """
        hot_wallet = agent_config.get('wallet', {}).get('hot_wallet', '')
        contract = agent_config.get('contract', BAYC_CONTRACT)
        token_id = agent_config.get('token_id', 0)
        
        result = {
            'agent_id': agent_config.get('agent_id', '?'),
            'token_id': token_id,
            'contract': contract,
            'hot_wallet': hot_wallet,
            'verified': False,
            'delegation_type': None,
            'owner': None,
            'checks': {},
        }
        
        # 1. Check NFT ownership
        owner = self.verify_nft_ownership(contract, token_id)
        result['owner'] = owner
        result['checks']['ownership'] = owner is not None
        
        if not owner:
            result['checks']['error'] = 'Could not verify NFT ownership'
            return result
        
        # 2. Check token-level delegation (most specific)
        token_delegated = self.check_delegation_for_token(
            hot_wallet, owner, contract, token_id
        )
        result['checks']['token_delegation'] = token_delegated
        if token_delegated:
            result['verified'] = True
            result['delegation_type'] = 'token'
            return result
        
        # 3. Check contract-level delegation
        contract_delegated = self.check_delegation_for_contract(
            hot_wallet, owner, contract
        )
        result['checks']['contract_delegation'] = contract_delegated
        if contract_delegated:
            result['verified'] = True
            result['delegation_type'] = 'contract'
            return result
        
        # 4. Check wallet-level delegation
        wallet_delegated = self.check_delegation_for_all(hot_wallet, owner)
        result['checks']['wallet_delegation'] = wallet_delegated
        if wallet_delegated:
            result['verified'] = True
            result['delegation_type'] = 'wallet'
            return result
        
        result['checks']['note'] = 'No delegation found. Set up at delegate.xyz'
        return result


def verify_lulo():
    """Verify Lulo #2253 delegation status."""
    config_path = Path(__file__).parent / "agents" / "lulo.json"
    config = json.loads(config_path.read_text())
    
    print(f"🦍 Verifying Simian Agent: {config['name']} #{config['token_id']}")
    print(f"   Collection: {config['collection']}")
    print(f"   Hot wallet: {config['wallet']['hot_wallet']}")
    print()
    
    verifier = DelegationVerifier()
    
    if not verifier.connected:
        print("❌ Cannot connect to Ethereum RPC")
        return
    
    print("🔍 Running verification...")
    result = verifier.full_verification(config)
    
    print(f"\n{'='*50}")
    print(f"📋 VERIFICATION RESULT")
    print(f"{'='*50}")
    print(f"   Agent: {result['agent_id']}")
    print(f"   Token: #{result['token_id']}")
    print(f"   Owner: {result['owner']}")
    print(f"   Hot wallet: {result['hot_wallet']}")
    print(f"   Verified: {'✅ YES' if result['verified'] else '❌ NO'}")
    
    if result['verified']:
        print(f"   Delegation type: {result['delegation_type']}")
    else:
        print(f"   ⚠️ No delegation found.")
        print(f"   Set up delegation at: https://delegate.xyz")
        print(f"   Delegate {result['hot_wallet']} for BAYC #{result['token_id']}")
    
    print(f"\n   Checks: {json.dumps(result['checks'], indent=6)}")
    
    return result


if __name__ == '__main__':
    verify_lulo()
