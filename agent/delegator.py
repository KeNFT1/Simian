"""
Simian Agent Delegator Module

This module handles verification and management of NFT delegations via delegate.cash,
ensuring that agents have proper authorization to act on behalf of NFT owners.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import time

from web3 import Web3
from web3.contract import Contract
from eth_typing import Address, ChecksumAddress


logger = logging.getLogger(__name__)


class DelegationType(Enum):
    """Types of delegations supported by delegate.cash."""
    ALL = "all"           # All NFTs from vault
    CONTRACT = "contract" # All NFTs from specific contract
    TOKEN = "token"      # Specific NFT token


@dataclass
class DelegationInfo:
    """Information about a specific delegation."""
    delegate: str
    vault: str          # NFT owner address
    contract_address: str
    token_id: Optional[int] = None
    delegation_type: DelegationType = DelegationType.TOKEN
    is_valid: bool = False
    expires_at: Optional[int] = None
    created_at: Optional[int] = None
    last_verified: int = 0


class DelegationVerifier:
    """Verifies and manages NFT delegations via delegate.cash registry."""
    
    # delegate.cash registry contract address (mainnet)
    DELEGATE_REGISTRY_ADDRESS = "0x00000000000076A84feF008CDAbe6409d2FE638B"
    
    # Contract ABI for delegate.cash registry
    DELEGATE_REGISTRY_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "delegate", "type": "address"},
                {"internalType": "address", "name": "vault", "type": "address"},
                {"internalType": "address", "name": "contract_", "type": "address"},
                {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
            ],
            "name": "checkDelegateForToken",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "delegate", "type": "address"},
                {"internalType": "address", "name": "vault", "type": "address"},
                {"internalType": "address", "name": "contract_", "type": "address"}
            ],
            "name": "checkDelegateForContract",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "delegate", "type": "address"},
                {"internalType": "address", "name": "vault", "type": "address"}
            ],
            "name": "checkDelegateForAll",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self, web3_provider: Union[str, Web3]):
        """
        Initialize the delegation verifier.
        
        Args:
            web3_provider: Web3 instance or RPC endpoint URL
        """
        if isinstance(web3_provider, str):
            self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        else:
            self.w3 = web3_provider
            
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum provider")
        
        # Initialize delegate registry contract
        self.delegate_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.DELEGATE_REGISTRY_ADDRESS),
            abi=self.DELEGATE_REGISTRY_ABI
        )
        
        # Cache for verified delegations (delegate -> delegation_info)
        self._delegation_cache: Dict[str, DelegationInfo] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def _get_cache_key(self, delegate: str, vault: str, contract: str, token_id: Optional[int] = None) -> str:
        """Generate cache key for delegation."""
        key = f"{delegate.lower()}:{vault.lower()}:{contract.lower()}"
        if token_id is not None:
            key += f":{token_id}"
        return key
    
    def _is_cache_valid(self, delegation_info: DelegationInfo) -> bool:
        """Check if cached delegation info is still valid."""
        return (time.time() - delegation_info.last_verified) < self._cache_ttl
    
    async def verify_delegation(
        self,
        delegate: str,
        vault: str,
        contract_address: str,
        token_id: Optional[int] = None,
        use_cache: bool = True
    ) -> DelegationInfo:
        """
        Verify if a delegate has permission to act for a specific NFT.
        
        Args:
            delegate: Address that should have delegation rights
            vault: NFT owner address
            contract_address: NFT contract address
            token_id: Specific token ID (if None, checks contract-level delegation)
            use_cache: Whether to use cached results
            
        Returns:
            DelegationInfo object with verification results
        """
        # Normalize addresses
        delegate = Web3.to_checksum_address(delegate)
        vault = Web3.to_checksum_address(vault)
        contract_address = Web3.to_checksum_address(contract_address)
        
        # Check cache first
        cache_key = self._get_cache_key(delegate, vault, contract_address, token_id)
        if use_cache and cache_key in self._delegation_cache:
            cached_info = self._delegation_cache[cache_key]
            if self._is_cache_valid(cached_info):
                logger.debug(f"Using cached delegation result for {cache_key}")
                return cached_info
        
        # Create delegation info object
        delegation_info = DelegationInfo(
            delegate=delegate,
            vault=vault,
            contract_address=contract_address,
            token_id=token_id,
            delegation_type=DelegationType.TOKEN if token_id is not None else DelegationType.CONTRACT,
            last_verified=int(time.time())
        )
        
        try:
            # Check different delegation types in order of specificity
            is_valid = False
            
            if token_id is not None:
                # Check token-specific delegation
                logger.debug(f"Checking token delegation: {delegate} for {contract_address}:{token_id}")
                is_valid = await self._check_token_delegation(delegate, vault, contract_address, token_id)
                
                if is_valid:
                    delegation_info.delegation_type = DelegationType.TOKEN
            
            if not is_valid:
                # Check contract-wide delegation
                logger.debug(f"Checking contract delegation: {delegate} for {contract_address}")
                is_valid = await self._check_contract_delegation(delegate, vault, contract_address)
                
                if is_valid:
                    delegation_info.delegation_type = DelegationType.CONTRACT
            
            if not is_valid:
                # Check vault-wide (all) delegation
                logger.debug(f"Checking vault delegation: {delegate} for {vault}")
                is_valid = await self._check_all_delegation(delegate, vault)
                
                if is_valid:
                    delegation_info.delegation_type = DelegationType.ALL
            
            delegation_info.is_valid = is_valid
            
            # Cache the result
            self._delegation_cache[cache_key] = delegation_info
            
            logger.info(f"Delegation verification: {delegate} -> {vault}:{contract_address}:{token_id} = {is_valid}")
            
        except Exception as e:
            logger.error(f"Delegation verification failed: {e}")
            delegation_info.is_valid = False
        
        return delegation_info
    
    async def _check_token_delegation(
        self, 
        delegate: str, 
        vault: str, 
        contract_address: str, 
        token_id: int
    ) -> bool:
        """Check token-specific delegation."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.delegate_registry.functions.checkDelegateForToken(
                    delegate, vault, contract_address, token_id
                ).call
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Token delegation check failed: {e}")
            return False
    
    async def _check_contract_delegation(
        self, 
        delegate: str, 
        vault: str, 
        contract_address: str
    ) -> bool:
        """Check contract-wide delegation."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.delegate_registry.functions.checkDelegateForContract(
                    delegate, vault, contract_address
                ).call
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Contract delegation check failed: {e}")
            return False
    
    async def _check_all_delegation(self, delegate: str, vault: str) -> bool:
        """Check vault-wide delegation."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.delegate_registry.functions.checkDelegateForAll(
                    delegate, vault
                ).call
            )
            return bool(result)
        except Exception as e:
            logger.error(f"All delegation check failed: {e}")
            return False
    
    def clear_cache(self, delegate: Optional[str] = None):
        """Clear delegation cache."""
        if delegate:
            # Clear cache for specific delegate
            keys_to_remove = [k for k in self._delegation_cache.keys() if k.startswith(delegate.lower())]
            for key in keys_to_remove:
                del self._delegation_cache[key]
        else:
            # Clear entire cache
            self._delegation_cache.clear()
        
        logger.info(f"Cleared delegation cache for {'all' if not delegate else delegate}")
    
    def get_cached_delegations(self, delegate: Optional[str] = None) -> List[DelegationInfo]:
        """Get all cached delegations for a delegate."""
        if delegate:
            return [
                info for key, info in self._delegation_cache.items() 
                if key.startswith(delegate.lower()) and self._is_cache_valid(info)
            ]
        else:
            return [
                info for info in self._delegation_cache.values() 
                if self._is_cache_valid(info)
            ]
    
    async def batch_verify_delegations(
        self, 
        delegations: List[Tuple[str, str, str, Optional[int]]]
    ) -> Dict[str, DelegationInfo]:
        """
        Verify multiple delegations in batch.
        
        Args:
            delegations: List of (delegate, vault, contract, token_id) tuples
            
        Returns:
            Dictionary mapping cache keys to delegation results
        """
        tasks = []
        cache_keys = []
        
        for delegate, vault, contract, token_id in delegations:
            task = self.verify_delegation(delegate, vault, contract, token_id)
            tasks.append(task)
            cache_keys.append(self._get_cache_key(delegate, vault, contract, token_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        verification_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch verification failed for {delegations[i]}: {result}")
                continue
            verification_results[cache_keys[i]] = result
        
        return verification_results


class DelegationManager:
    """Higher-level manager for agent delegations."""
    
    def __init__(self, verifier: DelegationVerifier):
        self.verifier = verifier
        self._active_delegations: Dict[str, DelegationInfo] = {}
    
    async def register_agent_delegation(
        self,
        agent_id: str,
        delegate: str,
        vault: str,
        contract_address: str,
        token_id: int
    ) -> bool:
        """
        Register and verify a delegation for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            delegate: Agent's delegate address
            vault: NFT owner address
            contract_address: NFT contract address
            token_id: NFT token ID
            
        Returns:
            True if delegation is valid and registered
        """
        delegation_info = await self.verifier.verify_delegation(
            delegate, vault, contract_address, token_id
        )
        
        if delegation_info.is_valid:
            self._active_delegations[agent_id] = delegation_info
            logger.info(f"Registered valid delegation for agent {agent_id}")
            return True
        else:
            logger.warning(f"Invalid delegation for agent {agent_id}")
            return False
    
    async def verify_agent_authority(
        self,
        agent_id: str,
        action_description: str = ""
    ) -> bool:
        """
        Verify that an agent has current authority to act.
        
        Args:
            agent_id: Unique identifier for the agent
            action_description: Optional description of the action being verified
            
        Returns:
            True if agent has valid delegation
        """
        if agent_id not in self._active_delegations:
            logger.error(f"No delegation registered for agent {agent_id}")
            return False
        
        delegation_info = self._active_delegations[agent_id]
        
        # Re-verify if cache is stale
        if not self.verifier._is_cache_valid(delegation_info):
            logger.info(f"Re-verifying delegation for agent {agent_id}")
            updated_info = await self.verifier.verify_delegation(
                delegation_info.delegate,
                delegation_info.vault,
                delegation_info.contract_address,
                delegation_info.token_id
            )
            
            if updated_info.is_valid:
                self._active_delegations[agent_id] = updated_info
            else:
                # Delegation is no longer valid
                del self._active_delegations[agent_id]
                logger.warning(f"Delegation revoked for agent {agent_id}")
                return False
        
        if action_description:
            logger.info(f"Agent {agent_id} authorized for action: {action_description}")
        
        return True
    
    def revoke_agent_delegation(self, agent_id: str) -> bool:
        """Remove a delegation registration for an agent."""
        if agent_id in self._active_delegations:
            del self._active_delegations[agent_id]
            logger.info(f"Revoked delegation for agent {agent_id}")
            return True
        return False
    
    def get_agent_delegation(self, agent_id: str) -> Optional[DelegationInfo]:
        """Get delegation info for an agent."""
        return self._active_delegations.get(agent_id)
    
    def list_active_delegations(self) -> Dict[str, DelegationInfo]:
        """Get all active delegations."""
        return self._active_delegations.copy()


# TODO: Implement the following features:
# - [ ] Delegation event monitoring via WebSocket/HTTP polling
# - [ ] Automatic delegation refresh before expiration
# - [ ] Multi-chain delegation support (Base, Polygon, etc.)
# - [ ] Integration with Simian Registry contract for on-chain verification
# - [ ] Delegation analytics and reporting
# - [ ] Emergency delegation revocation mechanisms
# - [ ] Rate limiting for verification requests
# - [ ] Fallback verification methods
# - [ ] Delegation change notifications/alerts
# - [ ] Support for time-limited delegations