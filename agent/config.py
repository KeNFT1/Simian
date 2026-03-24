"""
Simian Agent Configuration Module

This module handles the configuration and initialization of Simian AI agents,
including capability settings, risk parameters, and operational constraints.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import IntFlag
import json
import os
from pathlib import Path


class AgentCapability(IntFlag):
    """Agent capability flags matching the smart contract bitmask."""
    TRADE = 1      # 0b00000001
    SOCIAL = 2     # 0b00000010  
    GOVERN = 4     # 0b00000100
    CLAIM = 8      # 0b00001000


@dataclass
class RiskParameters:
    """Risk management parameters for agent operations."""
    
    # Trading risk parameters
    max_position_size_usd: float = 1000.0
    max_daily_trades: int = 10
    stop_loss_percentage: float = 0.05  # 5%
    take_profit_percentage: float = 0.20  # 20%
    min_confidence_threshold: float = 0.7
    max_slippage_tolerance: float = 0.01  # 1%
    
    # Social risk parameters
    max_posts_per_day: int = 5
    sentiment_filter_enabled: bool = True
    profanity_filter_enabled: bool = True
    
    # Governance risk parameters
    min_proposal_score: float = 0.6
    auto_vote_threshold: float = 0.8
    max_gas_price_gwei: int = 100
    
    # General parameters
    emergency_stop_enabled: bool = True
    max_daily_gas_spend_usd: float = 50.0


@dataclass
class AgentConfig:
    """Complete configuration for a Simian AI agent."""
    
    # NFT Identity
    nft_contract: str
    token_id: int
    owner_address: str
    delegate_address: str
    
    # Agent settings
    agent_id: str
    capabilities: int  # Bitmask of enabled capabilities
    risk_params: RiskParameters = field(default_factory=RiskParameters)
    
    # Operational settings
    is_active: bool = True
    created_at: int = 0
    last_active_at: int = 0
    metadata_uri: Optional[str] = None
    
    # API keys and endpoints (stored securely)
    api_keys: Dict[str, str] = field(default_factory=dict)
    endpoints: Dict[str, str] = field(default_factory=dict)
    
    # Agent personality (loaded from NFT traits)
    personality_traits: Dict[str, Union[str, int, float]] = field(default_factory=dict)
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if the agent has a specific capability enabled."""
        return bool(self.capabilities & capability)
    
    def enable_capability(self, capability: AgentCapability) -> None:
        """Enable a specific capability."""
        self.capabilities |= capability
    
    def disable_capability(self, capability: AgentCapability) -> None:
        """Disable a specific capability."""
        self.capabilities &= ~capability
    
    def get_enabled_capabilities(self) -> List[AgentCapability]:
        """Get list of all enabled capabilities."""
        enabled = []
        for capability in AgentCapability:
            if self.has_capability(capability):
                enabled.append(capability)
        return enabled
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization."""
        return {
            'nft_contract': self.nft_contract,
            'token_id': self.token_id,
            'owner_address': self.owner_address,
            'delegate_address': self.delegate_address,
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'risk_params': self.risk_params.__dict__,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_active_at': self.last_active_at,
            'metadata_uri': self.metadata_uri,
            'endpoints': self.endpoints,
            'personality_traits': self.personality_traits
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentConfig':
        """Create config from dictionary."""
        risk_params = RiskParameters(**data.get('risk_params', {}))
        
        return cls(
            nft_contract=data['nft_contract'],
            token_id=data['token_id'],
            owner_address=data['owner_address'],
            delegate_address=data['delegate_address'],
            agent_id=data['agent_id'],
            capabilities=data['capabilities'],
            risk_params=risk_params,
            is_active=data.get('is_active', True),
            created_at=data.get('created_at', 0),
            last_active_at=data.get('last_active_at', 0),
            metadata_uri=data.get('metadata_uri'),
            endpoints=data.get('endpoints', {}),
            personality_traits=data.get('personality_traits', {})
        )
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'AgentConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class ConfigManager:
    """Manages agent configurations and provides utility functions."""
    
    def __init__(self, config_dir: Union[str, Path] = "./configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
    def create_default_config(
        self,
        nft_contract: str,
        token_id: int,
        owner_address: str,
        delegate_address: str,
        capabilities: int = AgentCapability.TRADE | AgentCapability.CLAIM
    ) -> AgentConfig:
        """Create a default agent configuration."""
        agent_id = f"{nft_contract.lower()}_{token_id}"
        
        return AgentConfig(
            nft_contract=nft_contract,
            token_id=token_id,
            owner_address=owner_address,
            delegate_address=delegate_address,
            agent_id=agent_id,
            capabilities=capabilities
        )
    
    def save_config(self, config: AgentConfig) -> Path:
        """Save agent configuration to file."""
        filepath = self.config_dir / f"{config.agent_id}.json"
        config.save_to_file(filepath)
        return filepath
    
    def load_config(self, agent_id: str) -> AgentConfig:
        """Load agent configuration from file."""
        filepath = self.config_dir / f"{agent_id}.json"
        return AgentConfig.load_from_file(filepath)
    
    def list_configs(self) -> List[str]:
        """List all available agent configurations."""
        return [f.stem for f in self.config_dir.glob("*.json")]
    
    def delete_config(self, agent_id: str) -> bool:
        """Delete an agent configuration."""
        filepath = self.config_dir / f"{agent_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False


# Default endpoint configurations
DEFAULT_ENDPOINTS = {
    'ethereum_rpc': 'https://eth-mainnet.g.alchemy.com/v2/',
    'base_rpc': 'https://base-mainnet.g.alchemy.com/v2/',
    'polygon_rpc': 'https://polygon-mainnet.g.alchemy.com/v2/',
    'opensea_api': 'https://api.opensea.io/api/v1',
    'delegate_registry': '0x00000000000076A84feF008CDAbe6409d2FE638B',  # delegate.cash registry
    'polymarket_api': 'https://gamma-api.polymarket.com',
    'snapshot_api': 'https://hub.snapshot.org/graphql',
}

# Supported NFT collections
SUPPORTED_COLLECTIONS = {
    'BAYC': {
        'contract': '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',
        'name': 'Bored Ape Yacht Club'
    },
    'MAYC': {
        'contract': '0x60E4d786628Fea6478F785A6d7e704777c86a7c6',
        'name': 'Mutant Ape Yacht Club'  
    },
    'CRYPTOPUNKS': {
        'contract': '0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB',
        'name': 'CryptoPunks'
    }
}


# TODO: Implement the following features:
# - [ ] Encrypted storage for API keys and sensitive data
# - [ ] Configuration validation and schema enforcement
# - [ ] Migration system for config format updates
# - [ ] Integration with smart contract for on-chain config sync
# - [ ] Dynamic configuration updates via secure channels
# - [ ] Audit logging for configuration changes
# - [ ] Backup and recovery mechanisms
# - [ ] Multi-environment support (dev, staging, prod)