"""
Intelligence gathering module for Simian agent.
Collects information from free sources: HackerNews, Reddit, BBC RSS, Google News RSS.
"""

import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

class IntelligenceGatherer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('Intelligence')
        
        # Sources configuration
        self.sources = {
            'hackernews': {
                'enabled': config.get('hackernews', False),
                'urls': [
                    'https://hacker-news.firebaseio.com/v0/topstories.json',
                    'https://hacker-news.firebaseio.com/v0/newstories.json'
                ]
            },
            'reddit': {
                'enabled': config.get('reddit', False),
                'urls': [
                    'https://www.reddit.com/r/news/.json?limit=50',
                    'https://www.reddit.com/r/worldnews/.json?limit=50',
                    'https://www.reddit.com/r/politics/.json?limit=25'
                ]
            },
            'bbc': {
                'enabled': config.get('bbc', False),
                'urls': [
                    'http://feeds.bbci.co.uk/news/rss.xml',
                    'http://feeds.bbci.co.uk/news/world/rss.xml',
                    'http://feeds.bbci.co.uk/news/business/rss.xml'
                ]
            },
            'googleNews': {
                'enabled': config.get('googleNews', False),
                'urls': [
                    'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
                    'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en'  # World
                ]
            },
            'nitter': {
                'enabled': config.get('nitter', False),
                'urls': [
                    # Using RSS feeds from trending topics
                ]
            }
        }
        
        self.custom_keywords = config.get('customKeywords', [])
    
    async def gather_all(self) -> List[Dict[str, Any]]:
        """Gather intelligence from all enabled sources."""
        all_intelligence = []
        
        tasks = []
        
        if self.sources['hackernews']['enabled']:
            tasks.append(self.gather_hackernews())
        
        if self.sources['reddit']['enabled']:
            tasks.append(self.gather_reddit())
        
        if self.sources['bbc']['enabled']:
            tasks.append(self.gather_bbc_rss())
        
        if self.sources['googleNews']['enabled']:
            tasks.append(self.gather_google_news())
        
        if self.sources['nitter']['enabled']:
            tasks.append(self.gather_twitter_trends())
        
        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Intelligence gathering error: {result}")
                else:
                    all_intelligence.extend(result)
        
        # Filter by custom keywords if provided
        if self.custom_keywords:
            filtered = self.filter_by_keywords(all_intelligence)
            self.logger.info(f"Filtered {len(all_intelligence)} -> {len(filtered)} items by keywords")
            return filtered
        
        self.logger.info(f"Gathered {len(all_intelligence)} intelligence items")
        return all_intelligence
    
    async def gather_hackernews(self) -> List[Dict[str, Any]]:
        """Gather trending stories from HackerNews."""
        intelligence = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get top stories
                async with session.get('https://hacker-news.firebaseio.com/v0/topstories.json') as resp:
                    if resp.status == 200:
                        story_ids = await resp.json()
                        
                        # Get top 20 stories
                        for story_id in story_ids[:20]:
                            try:
                                async with session.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json') as story_resp:
                                    if story_resp.status == 200:
                                        story = await story_resp.json()
                                        if story and story.get('title'):
                                            intelligence.append({
                                                'source': 'hackernews',
                                                'title': story['title'],
                                                'text': story.get('text', ''),
                                                'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                                                'score': story.get('score', 0),
                                                'timestamp': datetime.fromtimestamp(story.get('time', 0)),
                                                'type': 'news'
                                            })
                            except Exception as e:
                                self.logger.debug(f"Error fetching HN story {story_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"HackerNews gathering error: {e}")
        
        self.logger.info(f"HackerNews: {len(intelligence)} items")
        return intelligence
    
    async def gather_reddit(self) -> List[Dict[str, Any]]:
        """Gather trending posts from Reddit."""
        intelligence = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for url in self.sources['reddit']['urls']:
                    try:
                        headers = {'User-Agent': 'SimianAgent/1.0 (Intelligence Gathering)'}
                        async with session.get(url, headers=headers) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                
                                for post in data.get('data', {}).get('children', []):
                                    post_data = post.get('data', {})
                                    if post_data.get('title') and not post_data.get('is_self'):
                                        intelligence.append({
                                            'source': 'reddit',
                                            'title': post_data['title'],
                                            'text': post_data.get('selftext', ''),
                                            'url': post_data.get('url', ''),
                                            'score': post_data.get('score', 0),
                                            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)),
                                            'subreddit': post_data.get('subreddit', ''),
                                            'type': 'social'
                                        })
                    except Exception as e:
                        self.logger.debug(f"Error fetching Reddit {url}: {e}")
        
        except Exception as e:
            self.logger.error(f"Reddit gathering error: {e}")
        
        self.logger.info(f"Reddit: {len(intelligence)} items")
        return intelligence
    
    async def gather_bbc_rss(self) -> List[Dict[str, Any]]:
        """Gather news from BBC RSS feeds."""
        intelligence = []
        
        try:
            for url in self.sources['bbc']['urls']:
                try:
                    feed = feedparser.parse(url)
                    
                    for entry in feed.entries[:20]:  # Limit to recent items
                        intelligence.append({
                            'source': 'bbc',
                            'title': entry.title,
                            'text': entry.get('summary', ''),
                            'url': entry.link,
                            'timestamp': datetime(*entry.published_parsed[:6]) if entry.get('published_parsed') else datetime.now(),
                            'type': 'news'
                        })
                
                except Exception as e:
                    self.logger.debug(f"Error parsing BBC RSS {url}: {e}")
        
        except Exception as e:
            self.logger.error(f"BBC RSS gathering error: {e}")
        
        self.logger.info(f"BBC RSS: {len(intelligence)} items")
        return intelligence
    
    async def gather_google_news(self) -> List[Dict[str, Any]]:
        """Gather news from Google News RSS."""
        intelligence = []
        
        try:
            for url in self.sources['googleNews']['urls']:
                try:
                    feed = feedparser.parse(url)
                    
                    for entry in feed.entries[:25]:  # Limit to recent items
                        intelligence.append({
                            'source': 'google_news',
                            'title': entry.title,
                            'text': entry.get('summary', ''),
                            'url': entry.link,
                            'timestamp': datetime(*entry.published_parsed[:6]) if entry.get('published_parsed') else datetime.now(),
                            'type': 'news'
                        })
                
                except Exception as e:
                    self.logger.debug(f"Error parsing Google News RSS {url}: {e}")
        
        except Exception as e:
            self.logger.error(f"Google News gathering error: {e}")
        
        self.logger.info(f"Google News: {len(intelligence)} items")
        return intelligence
    
    async def gather_twitter_trends(self) -> List[Dict[str, Any]]:
        """Gather trending topics (placeholder for future implementation)."""
        intelligence = []
        
        # This would require access to Twitter/X API or RSS feeds
        # For now, return empty list since free access is limited
        self.logger.info("Twitter/X trends: Not implemented (requires API access)")
        
        return intelligence
    
    def filter_by_keywords(self, intelligence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter intelligence items by custom keywords."""
        if not self.custom_keywords:
            return intelligence
        
        filtered = []
        keywords = [kw.lower() for kw in self.custom_keywords]
        
        for item in intelligence:
            title_text = (item.get('title', '') + ' ' + item.get('text', '')).lower()
            
            # Check if any keyword matches
            if any(keyword in title_text for keyword in keywords):
                item['matched_keywords'] = [kw for kw in keywords if kw in title_text]
                filtered.append(item)
        
        return filtered
    
    def get_recent_signals(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get intelligence signals from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # This would typically query a database or cache
        # For now, return empty list
        return []