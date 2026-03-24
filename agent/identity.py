"""
Simian Agent Identity Module

This module handles loading and managing NFT metadata to create unique agent identities.
Each Simian agent inherits the traits, visual characteristics, and personality of its NFT.
"""

import aiohttp
import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class NFTCollection(Enum):
    """Supported NFT collections."""
    BAYC = "Bored Ape Yacht Club"
    MAYC = "Mutant Ape Yacht Club"
    CRYPTOPUNKS = "CryptoPunks"


@dataclass
class NFTTrait:
    """Individual NFT trait/attribute."""
    trait_type: str
    value: Union[str, int, float]
    display_type: Optional[str] = None
    max_value: Optional[Union[int, float]] = None
    trait_count: Optional[int] = None
    
    @property
    def rarity_score(self) -> float:
        """Calculate basic rarity score if trait_count is available."""
        if self.trait_count and self.trait_count > 0:
            return 1.0 / self.trait_count
        return 0.0


@dataclass
class NFTMetadata:
    """Complete NFT metadata and identity information."""
    
    # Core NFT data
    contract_address: str
    token_id: int
    name: str
    description: str
    image_url: str
    external_url: Optional[str] = None
    
    # Traits and attributes
    traits: List[NFTTrait] = field(default_factory=list)
    collection: Optional[NFTCollection] = None
    
    # Metadata about the metadata
    metadata_uri: Optional[str] = None
    last_updated: Optional[int] = None
    
    # Computed identity properties
    personality_hash: str = ""
    rarity_rank: Optional[int] = None
    total_supply: Optional[int] = None
    
    def get_trait_by_type(self, trait_type: str) -> Optional[NFTTrait]:
        """Get a specific trait by its type."""
        for trait in self.traits:
            if trait.trait_type.lower() == trait_type.lower():
                return trait
        return None
    
    def get_trait_value(self, trait_type: str, default: Any = None) -> Any:
        """Get the value of a specific trait."""
        trait = self.get_trait_by_type(trait_type)
        return trait.value if trait else default
    
    def compute_personality_hash(self) -> str:
        """Generate a unique personality hash based on traits."""
        trait_string = ""
        for trait in sorted(self.traits, key=lambda t: t.trait_type):
            trait_string += f"{trait.trait_type}:{trait.value}"
        
        return hashlib.sha256(trait_string.encode()).hexdigest()[:16]
    
    def generate_personality_traits(self) -> Dict[str, Any]:
        """Generate AI personality traits from NFT attributes."""
        personality = {
            'base_identity': self.name or f"#{self.token_id}",
            'collection': self.collection.value if self.collection else "Unknown",
            'visual_hash': self.personality_hash,
            'traits': {}
        }
        
        # Map NFT traits to personality characteristics
        for trait in self.traits:
            trait_type = trait.trait_type.lower()
            value = trait.value
            
            # BAYC/MAYC specific trait mapping
            if trait_type in ['background', 'fur', 'eyes', 'mouth', 'clothes', 'hat', 'earring']:
                personality['traits'][trait_type] = value
                
                # Derive personality characteristics from specific traits
                if trait_type == 'eyes':
                    personality['focus_style'] = self._map_eyes_to_focus(value)
                elif trait_type == 'mouth':
                    personality['communication_style'] = self._map_mouth_to_communication(value)
                elif trait_type == 'clothes':
                    personality['risk_tolerance'] = self._map_clothes_to_risk(value)
                elif trait_type == 'background':
                    personality['market_preference'] = self._map_background_to_market(value)
            
            # CryptoPunks specific trait mapping
            elif trait_type in ['type', 'accessory']:
                personality['traits'][trait_type] = value
                if trait_type == 'type':
                    personality['base_archetype'] = value
        
        return personality
    
    def _map_eyes_to_focus(self, eyes_trait: str) -> str:
        """Map eye traits to focus/attention characteristics."""
        eyes_mapping = {
            'laser eyes': 'hyper_focused',
            'zombie': 'long_term_oriented',
            'sleepy': 'patient',
            'crazy': 'high_volatility_tolerance',
            'sad': 'risk_averse',
            'angry': 'aggressive',
            'bored': 'contrarian',
            'heart': 'community_focused'
        }
        return eyes_mapping.get(eyes_trait.lower(), 'balanced')
    
    def _map_mouth_to_communication(self, mouth_trait: str) -> str:
        """Map mouth traits to communication style."""
        mouth_mapping = {
            'bored unshaven': 'casual',
            'grin': 'optimistic', 
            'phoneme l': 'analytical',
            'phoneme ooo': 'surprised',
            'dumbfounded': 'conservative',
            'rage': 'aggressive',
            'small grin': 'subtle',
            'discomfort': 'cautious'
        }
        return mouth_mapping.get(mouth_trait.lower(), 'neutral')
    
    def _map_clothes_to_risk(self, clothes_trait: str) -> str:
        """Map clothing traits to risk tolerance."""
        clothes_mapping = {
            'prison jumpsuit': 'high_risk',
            'smoking jacket': 'sophisticated',
            'lab coat': 'analytical',
            'leather jacket': 'aggressive',
            'hawaiian': 'relaxed',
            'tuxedo tee': 'contrarian',
            'work vest': 'practical',
            'navy striped tee': 'conservative'
        }
        return clothes_mapping.get(clothes_trait.lower(), 'moderate')
    
    def _map_background_to_market(self, background_trait: str) -> str:
        """Map background traits to market preferences."""
        background_mapping = {
            'new punk blue': 'defi',
            'orange': 'meme_coins',
            'aquamarine': 'stable_coins',
            'yellow': 'commodities',
            'purple': 'nfts',
            'gray': 'traditional_markets',
            'blue': 'crypto_blue_chips'
        }
        return background_mapping.get(background_trait.lower(), 'diversified')


class NFTIdentityLoader:
    """Loads and manages NFT identity data from various sources."""
    
    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./nft_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_path(self, contract_address: str, token_id: int) -> Path:
        """Get cache file path for NFT metadata."""
        return self.cache_dir / f"{contract_address.lower()}_{token_id}.json"
    
    def _load_from_cache(self, contract_address: str, token_id: int) -> Optional[NFTMetadata]:
        """Load NFT metadata from cache if available."""
        cache_path = self._get_cache_path(contract_address, token_id)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                return self._parse_metadata_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load cache for {contract_address}:{token_id}: {e}")
        return None
    
    def _save_to_cache(self, metadata: NFTMetadata) -> None:
        """Save NFT metadata to cache."""
        cache_path = self._get_cache_path(metadata.contract_address, metadata.token_id)
        try:
            with open(cache_path, 'w') as f:
                json.dump(self._metadata_to_dict(metadata), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    async def load_nft_identity(
        self, 
        contract_address: str, 
        token_id: int,
        force_refresh: bool = False
    ) -> NFTMetadata:
        """
        Load complete NFT identity from various sources.
        
        Args:
            contract_address: NFT contract address
            token_id: Token ID
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            NFTMetadata object with complete identity information
        """
        # Try cache first unless force_refresh
        if not force_refresh:
            cached = self._load_from_cache(contract_address, token_id)
            if cached:
                logger.info(f"Loaded {contract_address}:{token_id} from cache")
                return cached
        
        # Fetch from various sources
        metadata = None
        
        # Try OpenSea API first
        try:
            metadata = await self._fetch_from_opensea(contract_address, token_id)
            logger.info(f"Fetched {contract_address}:{token_id} from OpenSea")
        except Exception as e:
            logger.warning(f"OpenSea fetch failed: {e}")
        
        # Fallback to on-chain metadata
        if not metadata:
            try:
                metadata = await self._fetch_from_chain(contract_address, token_id)
                logger.info(f"Fetched {contract_address}:{token_id} from chain")
            except Exception as e:
                logger.error(f"On-chain fetch failed: {e}")
                raise
        
        # Post-process and enhance metadata
        metadata = await self._enhance_metadata(metadata)
        
        # Cache the result
        self._save_to_cache(metadata)
        
        return metadata
    
    async def _fetch_from_opensea(self, contract_address: str, token_id: int) -> NFTMetadata:
        """Fetch NFT metadata from OpenSea API."""
        session = await self._get_session()
        url = f"https://api.opensea.io/api/v1/asset/{contract_address}/{token_id}/"
        
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"OpenSea API error: {response.status}")
            
            data = await response.json()
            return self._parse_opensea_response(data)
    
    async def _fetch_from_chain(self, contract_address: str, token_id: int) -> NFTMetadata:
        """Fetch NFT metadata from on-chain sources."""
        # TODO: Implement on-chain metadata fetching
        # This would involve:
        # 1. Calling tokenURI() on the contract
        # 2. Fetching the metadata from IPFS/HTTP
        # 3. Parsing the JSON metadata
        raise NotImplementedError("On-chain fetching not yet implemented")
    
    def _parse_opensea_response(self, data: Dict[str, Any]) -> NFTMetadata:
        """Parse OpenSea API response into NFTMetadata."""
        traits = []
        for trait in data.get('traits', []):
            traits.append(NFTTrait(
                trait_type=trait.get('trait_type', ''),
                value=trait.get('value', ''),
                display_type=trait.get('display_type'),
                max_value=trait.get('max_value'),
                trait_count=trait.get('trait_count')
            ))
        
        # Determine collection
        collection = None
        collection_name = data.get('collection', {}).get('name', '')
        if 'Bored Ape' in collection_name:
            collection = NFTCollection.BAYC
        elif 'Mutant Ape' in collection_name:
            collection = NFTCollection.MAYC
        elif 'CryptoPunks' in collection_name:
            collection = NFTCollection.CRYPTOPUNKS
        
        metadata = NFTMetadata(
            contract_address=data.get('asset_contract', {}).get('address', ''),
            token_id=int(data.get('token_id', 0)),
            name=data.get('name', ''),
            description=data.get('description', ''),
            image_url=data.get('image_url', ''),
            external_url=data.get('external_link'),
            traits=traits,
            collection=collection,
            metadata_uri=data.get('token_metadata'),
            total_supply=data.get('asset_contract', {}).get('total_supply')
        )
        
        return metadata
    
    async def _enhance_metadata(self, metadata: NFTMetadata) -> NFTMetadata:
        """Enhance metadata with computed properties."""
        # Generate personality hash
        metadata.personality_hash = metadata.compute_personality_hash()
        
        # TODO: Add more enhancements:
        # - Fetch rarity rankings from rarity tools
        # - Load floor price data
        # - Compute trait rarity scores
        # - Generate AI personality profile
        
        return metadata
    
    def _parse_metadata_dict(self, data: Dict[str, Any]) -> NFTMetadata:
        """Parse metadata from dictionary (cache)."""
        traits = []
        for trait_data in data.get('traits', []):
            traits.append(NFTTrait(**trait_data))
        
        collection = None
        if data.get('collection'):
            collection = NFTCollection(data['collection'])
        
        return NFTMetadata(
            contract_address=data['contract_address'],
            token_id=data['token_id'],
            name=data['name'],
            description=data['description'],
            image_url=data['image_url'],
            external_url=data.get('external_url'),
            traits=traits,
            collection=collection,
            metadata_uri=data.get('metadata_uri'),
            last_updated=data.get('last_updated'),
            personality_hash=data.get('personality_hash', ''),
            rarity_rank=data.get('rarity_rank'),
            total_supply=data.get('total_supply')
        )
    
    def _metadata_to_dict(self, metadata: NFTMetadata) -> Dict[str, Any]:
        """Convert NFTMetadata to dictionary for caching."""
        return {
            'contract_address': metadata.contract_address,
            'token_id': metadata.token_id,
            'name': metadata.name,
            'description': metadata.description,
            'image_url': metadata.image_url,
            'external_url': metadata.external_url,
            'traits': [trait.__dict__ for trait in metadata.traits],
            'collection': metadata.collection.value if metadata.collection else None,
            'metadata_uri': metadata.metadata_uri,
            'last_updated': metadata.last_updated,
            'personality_hash': metadata.personality_hash,
            'rarity_rank': metadata.rarity_rank,
            'total_supply': metadata.total_supply
        }


# TODO: Implement the following features:
# - [ ] On-chain metadata fetching via Web3.py
# - [ ] IPFS metadata resolution
# - [ ] Rarity.tools integration for rarity rankings
# - [ ] Floor price tracking integration
# - [ ] Advanced personality generation using AI models
# - [ ] Cross-collection trait mapping and analysis
# - [ ] Metadata validation and schema enforcement
# - [ ] Real-time metadata updates via webhooks
# - [ ] Image analysis for visual trait extraction
# - [ ] Social sentiment analysis for NFT reputation