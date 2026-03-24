"""
Market scanner for Polymarket and other prediction markets.
Fetches active markets and applies filters.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class MarketScanner:
    def __init__(self, filters: Dict[str, Any]):
        self.filters = filters
        self.logger = logging.getLogger('MarketScanner')
        
        # Gamma API endpoint for Polymarket
        self.gamma_api_base = "https://gamma-api.polymarket.com"
        
        # Market categories to exclude based on filters
        self.excluded_categories = []
        if filters.get('excludeSports', True):
            self.excluded_categories.extend(['sports', 'football', 'basketball', 'baseball', 'soccer'])
        
        if filters.get('excludeMeme', True):
            self.excluded_categories.extend(['gaming', 'entertainment', 'meme', 'celebrity'])
    
    async def fetch_active_markets(self) -> List[Dict[str, Any]]:
        """Fetch active markets from Gamma API and apply filters."""
        all_markets = []
        
        try:
            # Fetch markets from Gamma API
            markets = await self.fetch_gamma_markets()
            all_markets.extend(markets)
            
            # Apply filters
            filtered_markets = self.apply_filters(all_markets)
            
            self.logger.info(f"Scanned {len(all_markets)} markets, {len(filtered_markets)} passed filters")
            return filtered_markets
        
        except Exception as e:
            self.logger.error(f"Market scanning error: {e}")
            return []
    
    async def fetch_gamma_markets(self) -> List[Dict[str, Any]]:
        """Fetch markets from Polymarket Gamma API."""
        markets = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch active events
                url = f"{self.gamma_api_base}/events"
                params = {
                    'active': 'true',
                    'closed': 'false',
                    'limit': 100
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        events = data if isinstance(data, list) else data.get('data', [])
                        
                        for event in events:
                            # Parse event into market format
                            market = self.parse_gamma_event(event)
                            if market:
                                markets.append(market)
                    else:
                        self.logger.error(f"Gamma API error: {resp.status}")
        
        except Exception as e:
            self.logger.error(f"Gamma API fetch error: {e}")
        
        self.logger.info(f"Gamma API: {len(markets)} markets")
        return markets
    
    def parse_gamma_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Gamma API event into our market format."""
        try:
            # Get the first market from the event
            markets = event.get('markets', [])
            if not markets:
                return None
            
            primary_market = markets[0]
            
            # Calculate volume (sum of all outcome volumes)
            volume = 0
            outcomes = primary_market.get('outcomes', [])
            for outcome in outcomes:
                outcome_volume = float(outcome.get('volume', 0))
                volume += outcome_volume
            
            # Get prices for outcomes
            prices = []
            for outcome in outcomes:
                price = float(outcome.get('price', 0))
                prices.append(price)
            
            # Calculate days to resolution
            end_date_str = event.get('endDate') or event.get('end_date')
            if end_date_str:
                try:
                    # Handle different date formats
                    if 'T' in end_date_str:
                        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    else:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    
                    days_to_resolution = (end_date - datetime.now()).days
                except:
                    days_to_resolution = 365  # Default if parsing fails
            else:
                days_to_resolution = 365
            
            return {
                'id': event.get('id') or event.get('slug'),
                'title': event.get('title') or event.get('question'),
                'description': event.get('description', ''),
                'volume': volume,
                'prices': prices,
                'outcomes': [outcome.get('name', '') for outcome in outcomes],
                'category': event.get('category', '').lower(),
                'tags': event.get('tags', []),
                'end_date': end_date_str,
                'days_to_resolution': max(0, days_to_resolution),
                'url': f"https://polymarket.com/event/{event.get('slug', event.get('id'))}",
                'source': 'polymarket',
                'raw_data': event
            }
        
        except Exception as e:
            self.logger.debug(f"Error parsing event {event.get('id')}: {e}")
            return None
    
    def apply_filters(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply market filters to the fetched markets."""
        filtered = []
        
        for market in markets:
            if self.passes_filters(market):
                filtered.append(market)
        
        return filtered
    
    def passes_filters(self, market: Dict[str, Any]) -> bool:
        """Check if a market passes all filters."""
        
        # Volume filter
        min_volume = self.filters.get('minVolume', 0)
        if market['volume'] < min_volume:
            return False
        
        # Price range filter
        price_range = self.filters.get('priceRange', {'min': 0, 'max': 100})
        prices = market.get('prices', [])
        
        if prices:
            # Check if any price is in the acceptable range
            min_price_cents = price_range['min']
            max_price_cents = price_range['max']
            
            has_acceptable_price = False
            for price in prices:
                price_cents = price * 100  # Convert to cents
                if min_price_cents <= price_cents <= max_price_cents:
                    has_acceptable_price = True
                    break
            
            if not has_acceptable_price:
                return False
        
        # Days to resolution filter
        max_days = self.filters.get('maxDaysToResolution', 365)
        if market['days_to_resolution'] > max_days:
            return False
        
        # Category exclusions
        category = market.get('category', '').lower()
        if any(excluded in category for excluded in self.excluded_categories):
            return False
        
        # Check tags for exclusions as well
        tags = [tag.lower() for tag in market.get('tags', [])]
        if any(excluded in ' '.join(tags) for excluded in self.excluded_categories):
            return False
        
        # Check title for exclusions
        title = market.get('title', '').lower()
        if any(excluded in title for excluded in self.excluded_categories):
            return False
        
        return True
    
    def get_market_liquidity_score(self, market: Dict[str, Any]) -> float:
        """Calculate a liquidity score for the market."""
        volume = market.get('volume', 0)
        
        # Simple volume-based scoring
        if volume >= 100000:
            return 1.0
        elif volume >= 50000:
            return 0.8
        elif volume >= 10000:
            return 0.6
        elif volume >= 5000:
            return 0.4
        elif volume >= 1000:
            return 0.2
        else:
            return 0.1
    
    def get_market_urgency_score(self, market: Dict[str, Any]) -> float:
        """Calculate an urgency score based on time to resolution."""
        days = market.get('days_to_resolution', 365)
        
        if days <= 1:
            return 1.0
        elif days <= 7:
            return 0.8
        elif days <= 30:
            return 0.6
        elif days <= 90:
            return 0.4
        elif days <= 180:
            return 0.2
        else:
            return 0.1