"""
Simian Agent Social Capability

This module handles autonomous social media presence and community engagement
for Simian agents, reflecting their NFT identity and personality.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import time
import json
import re
import hashlib
import random

import aiohttp


logger = logging.getLogger(__name__)


class SocialPlatform(Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    FARCASTER = "farcaster"
    LENS = "lens"
    DISCORD = "discord"
    TELEGRAM = "telegram"


class PostType(Enum):
    """Types of social media posts."""
    ORIGINAL = "original"
    REPLY = "reply"
    RETWEET = "retweet"
    QUOTE_TWEET = "quote_tweet"
    THREAD = "thread"


class ContentCategory(Enum):
    """Categories of content."""
    ALPHA = "alpha"                    # Trading insights, market signals
    COMMUNITY = "community"            # Community engagement, greetings
    GOVERNANCE = "governance"          # DAO proposals, voting updates
    MARKET_COMMENTARY = "market"       # Market analysis, predictions
    NFT_CULTURE = "nft_culture"       # NFT culture, art, memes
    PERSONAL = "personal"             # Personality-driven content
    EDUCATIONAL = "educational"        # Teaching, explaining concepts
    ANNOUNCEMENT = "announcement"      # Important updates


@dataclass
class SocialPost:
    """Social media post information."""
    post_id: str
    platform: SocialPlatform
    post_type: PostType
    content: str
    media_urls: List[str] = field(default_factory=list)
    
    # Metadata
    author: str = ""
    created_at: int = 0
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    
    # Threading
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    
    # Categories and tags
    category: Optional[ContentCategory] = None
    tags: List[str] = field(default_factory=list)
    
    # Performance tracking
    engagement_rate: float = 0.0
    reach: int = 0


@dataclass
class ContentTemplate:
    """Template for generating content."""
    name: str
    category: ContentCategory
    template: str
    variables: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    min_confidence: float = 0.5


@dataclass
class SocialPersonality:
    """Social media personality configuration."""
    base_archetype: str                    # core, degen, diamond_hands, etc.
    communication_style: str              # casual, analytical, aggressive, etc.
    risk_tolerance: str                    # conservative, moderate, aggressive
    market_stance: str                     # bullish, bearish, neutral
    humor_level: float = 0.5              # 0.0 = serious, 1.0 = very humorous
    emoji_usage: float = 0.3              # 0.0 = none, 1.0 = lots
    posting_frequency: str = "moderate"    # low, moderate, high
    
    # Content preferences
    preferred_topics: List[str] = field(default_factory=list)
    avoided_topics: List[str] = field(default_factory=list)
    
    # Engagement style
    reply_probability: float = 0.2
    retweet_probability: float = 0.1
    quote_tweet_probability: float = 0.05


class ContentGenerator:
    """Generates social media content based on NFT personality and market data."""
    
    def __init__(self, personality: SocialPersonality):
        self.personality = personality
        self.templates = self._load_content_templates()
        self.recent_posts: List[SocialPost] = []
        
        # Content tracking
        self.last_post_time = 0
        self.daily_post_count = 0
        self.current_date = ""
    
    def _load_content_templates(self) -> Dict[ContentCategory, List[ContentTemplate]]:
        """Load content templates organized by category."""
        templates = {
            ContentCategory.ALPHA: [
                ContentTemplate(
                    name="market_signal",
                    category=ContentCategory.ALPHA,
                    template="🔍 {market_insight} {confidence_level}\n\nNot financial advice, just an ape with {personality_trait} 🦍",
                    variables=["market_insight", "confidence_level", "personality_trait"],
                    personality_traits=["analytical", "aggressive"]
                ),
                ContentTemplate(
                    name="trade_update", 
                    category=ContentCategory.ALPHA,
                    template="📈 Just {action} {asset} at {price}\n\n{reasoning}\n\n#{tag} #{platform}",
                    variables=["action", "asset", "price", "reasoning", "tag", "platform"],
                    personality_traits=["risk_tolerant", "transparent"]
                )
            ],
            
            ContentCategory.COMMUNITY: [
                ContentTemplate(
                    name="gm_post",
                    category=ContentCategory.COMMUNITY,
                    template="GM {community} fam! ☀️\n\n{daily_vibe} {market_mood}\n\nWhat's everyone {action} today?",
                    variables=["community", "daily_vibe", "market_mood", "action"],
                    personality_traits=["social", "optimistic"]
                ),
                ContentTemplate(
                    name="community_support",
                    category=ContentCategory.COMMUNITY,
                    template="Shoutout to the {community} community! 🙌\n\n{support_message}\n\nTogether we {collective_action} 💪",
                    variables=["community", "support_message", "collective_action"],
                    personality_traits=["supportive", "loyal"]
                )
            ],
            
            ContentCategory.GOVERNANCE: [
                ContentTemplate(
                    name="vote_announcement",
                    category=ContentCategory.GOVERNANCE,
                    template="🗳️ Voted {vote_choice} on {proposal_name}\n\n{reasoning}\n\n{governance_stance} #DAO #Governance",
                    variables=["vote_choice", "proposal_name", "reasoning", "governance_stance"],
                    personality_traits=["civic", "analytical"]
                ),
                ContentTemplate(
                    name="governance_reminder",
                    category=ContentCategory.GOVERNANCE,
                    template="⏰ Don't forget to vote on {proposal}!\n\n{brief_summary}\n\nYour voice matters in {dao_name} 🏛️",
                    variables=["proposal", "brief_summary", "dao_name"],
                    personality_traits=["civic", "helpful"]
                )
            ],
            
            ContentCategory.NFT_CULTURE: [
                ContentTemplate(
                    name="ape_pride",
                    category=ContentCategory.NFT_CULTURE,
                    template="🦍 Ape #{token_id} reporting for duty!\n\n{ape_characteristic} gang {emoji}\n\n{nft_flex} #BAYC #NFT",
                    variables=["token_id", "ape_characteristic", "emoji", "nft_flex"],
                    personality_traits=["proud", "community_focused"]
                ),
                ContentTemplate(
                    name="nft_appreciation",
                    category=ContentCategory.NFT_CULTURE,
                    template="🎨 The art speaks to the soul\n\n{art_observation}\n\n{collection_name} continues to inspire 🌟",
                    variables=["art_observation", "collection_name"],
                    personality_traits=["artistic", "appreciative"]
                )
            ],
            
            ContentCategory.MARKET_COMMENTARY: [
                ContentTemplate(
                    name="market_observation",
                    category=ContentCategory.MARKET_COMMENTARY,
                    template="📊 {market_observation}\n\n{analysis}\n\n{prediction} {emoji}",
                    variables=["market_observation", "analysis", "prediction", "emoji"],
                    personality_traits=["analytical", "observant"]
                )
            ]
        }
        
        return templates
    
    async def generate_content(
        self, 
        category: ContentCategory, 
        context_data: Dict[str, Any] = None
    ) -> Optional[str]:
        """Generate content for a specific category."""
        if category not in self.templates:
            return None
        
        # Filter templates by personality compatibility
        compatible_templates = []
        for template in self.templates[category]:
            if self._is_personality_compatible(template):
                compatible_templates.append(template)
        
        if not compatible_templates:
            return None
        
        # Select template
        template = random.choice(compatible_templates)
        
        # Generate content from template
        return await self._fill_template(template, context_data or {})
    
    def _is_personality_compatible(self, template: ContentTemplate) -> bool:
        """Check if template matches agent personality."""
        # Simple compatibility check - could be made more sophisticated
        if not template.personality_traits:
            return True
        
        # Map personality attributes to traits
        personality_traits = []
        
        if self.personality.communication_style == "analytical":
            personality_traits.append("analytical")
        if self.personality.risk_tolerance == "aggressive":
            personality_traits.append("aggressive")
            personality_traits.append("risk_tolerant")
        if self.personality.humor_level > 0.7:
            personality_traits.append("humorous")
        if self.personality.posting_frequency == "high":
            personality_traits.append("social")
        
        # Check for overlap
        return any(trait in personality_traits for trait in template.personality_traits)
    
    async def _fill_template(self, template: ContentTemplate, context_data: Dict[str, Any]) -> str:
        """Fill template with actual content."""
        content = template.template
        
        # Generate content for each variable
        for variable in template.variables:
            value = await self._generate_variable_content(variable, template.category, context_data)
            content = content.replace(f"{{{variable}}}", value)
        
        # Add personality touches
        content = self._add_personality_touches(content)
        
        return content
    
    async def _generate_variable_content(
        self, 
        variable: str, 
        category: ContentCategory,
        context: Dict[str, Any]
    ) -> str:
        """Generate content for a specific variable."""
        # Check if provided in context
        if variable in context:
            return str(context[variable])
        
        # Generate based on variable type and personality
        generators = {
            'market_insight': self._generate_market_insight,
            'confidence_level': self._generate_confidence_level,
            'personality_trait': self._generate_personality_trait,
            'daily_vibe': self._generate_daily_vibe,
            'market_mood': self._generate_market_mood,
            'community': self._get_community_name,
            'action': self._generate_action_word,
            'emoji': self._generate_emoji,
            'tag': self._generate_hashtag,
            'platform': lambda: "Simian"
        }
        
        generator = generators.get(variable)
        if generator:
            if asyncio.iscoroutinefunction(generator):
                return await generator()
            else:
                return generator()
        
        return f"[{variable}]"  # Placeholder if no generator
    
    def _generate_market_insight(self) -> str:
        """Generate market insight based on personality."""
        insights = {
            "analytical": [
                "Technical indicators suggest potential breakout",
                "Volume patterns indicate accumulation phase",
                "RSI divergence forming on daily chart"
            ],
            "aggressive": [
                "Feeling bullish on this setup",
                "Time to go full send mode",
                "This is the opportunity we've been waiting for"
            ],
            "conservative": [
                "Cautiously optimistic about current levels",
                "Risk/reward looking favorable here",
                "Good entry point for long-term holders"
            ]
        }
        
        style = self.personality.communication_style
        options = insights.get(style, insights["analytical"])
        return random.choice(options)
    
    def _generate_confidence_level(self) -> str:
        """Generate confidence indicator."""
        levels = ["🟢 High confidence", "🟡 Medium confidence", "🔵 Low confidence"]
        # Bias based on personality
        if self.personality.risk_tolerance == "aggressive":
            return random.choices(levels, weights=[0.6, 0.3, 0.1])[0]
        else:
            return random.choices(levels, weights=[0.2, 0.5, 0.3])[0]
    
    def _generate_personality_trait(self) -> str:
        """Generate personality-based trait description."""
        traits = {
            "analytical": "diamond brain",
            "aggressive": "diamond hands", 
            "conservative": "steady hands",
            "social": "strong community spirit"
        }
        return traits.get(self.personality.communication_style, "strong conviction")
    
    def _generate_daily_vibe(self) -> str:
        """Generate daily vibe check."""
        vibes = ["Feeling bullish", "Staying comfy", "Building mode activated", "Ready to grind"]
        return random.choice(vibes)
    
    def _generate_market_mood(self) -> str:
        """Generate market mood assessment."""
        moods = ["📈", "📉", "🦀 (crabbing)", "🚀", "💎", "🔥"]
        return random.choice(moods)
    
    def _get_community_name(self) -> str:
        """Get community name based on NFT collection."""
        communities = {
            "BAYC": "BAYC",
            "MAYC": "MAYC", 
            "CRYPTOPUNKS": "CryptoPunks"
        }
        # Default to BAYC for now
        return "BAYC"
    
    def _generate_action_word(self) -> str:
        """Generate action word."""
        actions = ["building", "hodling", "researching", "analyzing", "trading", "vibing"]
        return random.choice(actions)
    
    def _generate_emoji(self) -> str:
        """Generate emoji based on personality and context."""
        if self.personality.emoji_usage < 0.3:
            return ""
        
        emojis = ["🚀", "💎", "🦍", "🔥", "📈", "⚡", "🌙", "🎯"]
        return random.choice(emojis)
    
    def _generate_hashtag(self) -> str:
        """Generate relevant hashtag."""
        tags = ["crypto", "NFT", "DeFi", "WAGMI", "HODL", "alpha"]
        return random.choice(tags)
    
    def _add_personality_touches(self, content: str) -> str:
        """Add personality-specific touches to content."""
        # Add emojis based on usage preference
        if self.personality.emoji_usage > 0.5 and random.random() < 0.3:
            emoji = self._generate_emoji()
            if emoji and emoji not in content:
                content += f" {emoji}"
        
        # Add casual language for casual communicators
        if self.personality.communication_style == "casual":
            content = content.replace("I am", "I'm")
            content = content.replace("you are", "you're")
        
        return content
    
    def should_post(self) -> bool:
        """Determine if agent should post now based on personality and timing."""
        current_time = int(time.time())
        current_date = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
        
        # Reset daily counter if new day
        if current_date != self.current_date:
            self.daily_post_count = 0
            self.current_date = current_date
        
        # Check frequency limits
        max_daily_posts = {
            "low": 2,
            "moderate": 5,
            "high": 10
        }.get(self.personality.posting_frequency, 5)
        
        if self.daily_post_count >= max_daily_posts:
            return False
        
        # Check time since last post
        min_interval = {
            "low": 4 * 3600,      # 4 hours
            "moderate": 2 * 3600,  # 2 hours  
            "high": 30 * 60       # 30 minutes
        }.get(self.personality.posting_frequency, 2 * 3600)
        
        if current_time - self.last_post_time < min_interval:
            return False
        
        return True


class TwitterClient:
    """Twitter API client for posting and engagement."""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limits = {
            'tweet': {'remaining': 300, 'reset_time': 0},
            'reply': {'remaining': 300, 'reset_time': 0}
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session with auth headers."""
        if not self.session:
            headers = {
                'Authorization': f"Bearer {self.api_keys.get('bearer_token')}",
                'Content-Type': 'application/json'
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def post_tweet(self, content: str, reply_to: Optional[str] = None) -> Optional[str]:
        """Post a tweet and return tweet ID."""
        if not self._check_rate_limit('tweet'):
            logger.warning("Tweet rate limit exceeded")
            return None
        
        session = await self._get_session()
        url = "https://api.twitter.com/2/tweets"
        
        data = {"text": content}
        if reply_to:
            data["reply"] = {"in_reply_to_tweet_id": reply_to}
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    tweet_id = result['data']['id']
                    logger.info(f"Tweet posted: {tweet_id}")
                    return tweet_id
                else:
                    logger.error(f"Twitter API error: {response.status} - {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            return None
    
    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if we're within rate limits."""
        if endpoint not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[endpoint]
        current_time = int(time.time())
        
        # Reset if past reset time
        if current_time >= limit_info['reset_time']:
            limit_info['remaining'] = 300  # Reset to max
            limit_info['reset_time'] = current_time + 900  # 15 minutes
        
        if limit_info['remaining'] > 0:
            limit_info['remaining'] -= 1
            return True
        
        return False


class SimianSocialAgent:
    """Main social media agent for autonomous posting and engagement."""
    
    def __init__(
        self,
        agent_id: str,
        personality: SocialPersonality,
        platform_clients: Dict[SocialPlatform, Any],
        config: Dict
    ):
        self.agent_id = agent_id
        self.personality = personality
        self.platform_clients = platform_clients
        self.config = config
        
        # Content generation
        self.content_generator = ContentGenerator(personality)
        
        # Social state
        self.posted_content: List[SocialPost] = []
        self.engagement_targets: List[str] = []
        
        self.is_active = False
    
    async def start_social_activity(self):
        """Start autonomous social media activity."""
        self.is_active = True
        logger.info(f"Social agent {self.agent_id} started")
        
        while self.is_active:
            try:
                await self._social_cycle()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.error(f"Social cycle error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def stop_social_activity(self):
        """Stop social media activity."""
        self.is_active = False
        logger.info(f"Social agent {self.agent_id} stopped")
    
    async def _social_cycle(self):
        """Execute one social media cycle."""
        # Check if we should post
        if self.content_generator.should_post():
            await self._create_and_post_content()
        
        # Check for engagement opportunities
        await self._check_engagement_opportunities()
    
    async def _create_and_post_content(self):
        """Create and post new content."""
        # Determine content category based on recent activity and context
        category = self._select_content_category()
        
        # Generate content
        content = await self.content_generator.generate_content(category)
        
        if content:
            # Post to platforms
            for platform, client in self.platform_clients.items():
                success = await self._post_to_platform(platform, content, client)
                
                if success:
                    # Track the post
                    post = SocialPost(
                        post_id=f"{platform.value}_{int(time.time())}",
                        platform=platform,
                        post_type=PostType.ORIGINAL,
                        content=content,
                        category=category,
                        created_at=int(time.time())
                    )
                    self.posted_content.append(post)
                    self.content_generator.daily_post_count += 1
                    self.content_generator.last_post_time = int(time.time())
    
    def _select_content_category(self) -> ContentCategory:
        """Select content category based on personality and context."""
        # Weight categories by personality preferences
        category_weights = {
            ContentCategory.COMMUNITY: 0.3,
            ContentCategory.ALPHA: 0.2,
            ContentCategory.NFT_CULTURE: 0.2,
            ContentCategory.MARKET_COMMENTARY: 0.15,
            ContentCategory.GOVERNANCE: 0.1,
            ContentCategory.PERSONAL: 0.05
        }
        
        # Adjust weights based on personality
        if self.personality.communication_style == "analytical":
            category_weights[ContentCategory.ALPHA] += 0.2
            category_weights[ContentCategory.MARKET_COMMENTARY] += 0.15
        
        if self.personality.base_archetype == "community_focused":
            category_weights[ContentCategory.COMMUNITY] += 0.2
        
        # Select category
        categories = list(category_weights.keys())
        weights = list(category_weights.values())
        
        return random.choices(categories, weights=weights)[0]
    
    async def _post_to_platform(
        self, 
        platform: SocialPlatform, 
        content: str, 
        client: Any
    ) -> bool:
        """Post content to a specific platform."""
        try:
            if platform == SocialPlatform.TWITTER:
                tweet_id = await client.post_tweet(content)
                return tweet_id is not None
            
            # Add other platform implementations here
            logger.info(f"Would post to {platform.value}: {content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error posting to {platform.value}: {e}")
            return False
    
    async def _check_engagement_opportunities(self):
        """Check for opportunities to engage with community content."""
        # This could include:
        # - Replying to mentions
        # - Retweeting relevant content
        # - Participating in discussions
        # - Supporting community members
        
        # TODO: Implement engagement logic
        pass
    
    def get_social_stats(self) -> Dict[str, Any]:
        """Get social media performance statistics."""
        if not self.posted_content:
            return {}
        
        total_posts = len(self.posted_content)
        total_engagement = sum(
            post.likes + post.retweets + post.replies 
            for post in self.posted_content
        )
        
        category_counts = {}
        for post in self.posted_content:
            if post.category:
                category_counts[post.category.value] = category_counts.get(post.category.value, 0) + 1
        
        return {
            'total_posts': total_posts,
            'total_engagement': total_engagement,
            'avg_engagement': total_engagement / total_posts if total_posts > 0 else 0,
            'category_distribution': category_counts,
            'posting_frequency': self.personality.posting_frequency,
            'last_post': max((post.created_at for post in self.posted_content), default=0)
        }


# TODO: Implement the following features:
# - [ ] Advanced content generation using AI language models
# - [ ] Image/media generation and posting capabilities  
# - [ ] Sentiment analysis for engagement optimization
# - [ ] Community interaction and relationship building
# - [ ] Multi-platform content adaptation and scheduling
# - [ ] Influencer identification and networking
# - [ ] Content performance analysis and optimization
# - [ ] Trending topic identification and participation
# - [ ] Crisis management and reputation protection
# - [ ] Integration with NFT metadata for visual content
# - [ ] Automated customer support and FAQ responses
# - [ ] Social media advertising and promotion campaigns