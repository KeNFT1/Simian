"""
Market scoring module for Simian agent.
Scores markets against intelligence signals to calculate edges.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math

class MarketScorer:
    def __init__(self):
        self.logger = logging.getLogger('MarketScorer')
        
        # Keyword weightings for different types of intelligence
        self.keyword_weights = {
            'high_confidence': [
                'confirmed', 'official', 'announced', 'reported', 'verified',
                'breaking', 'exclusive', 'sources', 'leaked'
            ],
            'medium_confidence': [
                'likely', 'expected', 'projected', 'estimated', 'anticipated',
                'rumors', 'speculation', 'suggests', 'indicates'
            ],
            'market_moving': [
                'fed', 'interest', 'rate', 'inflation', 'gdp', 'unemployment',
                'election', 'vote', 'poll', 'candidate', 'president',
                'ukraine', 'russia', 'china', 'iran', 'sanctions',
                'bitcoin', 'crypto', 'sec', 'regulation', 'etf'
            ]
        }
        
        # Source reliability weights
        self.source_weights = {
            'bbc': 0.9,
            'google_news': 0.8,
            'hackernews': 0.7,
            'reddit': 0.6,
            'twitter': 0.5
        }
    
    def score_markets(self, markets: List[Dict[str, Any]], intelligence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score all markets against intelligence signals."""
        scored_markets = []
        
        for market in markets:
            score = self.score_market(market, intelligence)
            
            # Add scoring information to market
            market['intelligence_score'] = score['total_score']
            market['signal_count'] = score['signal_count']
            market['confidence'] = score['confidence']
            market['edge'] = score['edge']
            market['position_size'] = score['position_size']
            market['matched_signals'] = score['matched_signals']
            
            scored_markets.append(market)
        
        # Sort by edge (highest first)
        scored_markets.sort(key=lambda x: x['edge'], reverse=True)
        
        self.logger.info(f"Scored {len(scored_markets)} markets")
        return scored_markets
    
    def score_market(self, market: Dict[str, Any], intelligence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score a single market against intelligence signals."""
        
        # Extract market keywords
        market_keywords = self.extract_market_keywords(market)
        
        # Find matching intelligence signals
        matching_signals = self.find_matching_signals(market_keywords, intelligence)
        
        if not matching_signals:
            return {
                'total_score': 0.0,
                'signal_count': 0,
                'confidence': 0.0,
                'edge': 0.0,
                'position_size': 0.0,
                'matched_signals': []
            }
        
        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        
        for signal in matching_signals:
            signal_score = self.score_signal(signal, market_keywords)
            source_weight = self.source_weights.get(signal['source'], 0.5)
            recency_weight = self.get_recency_weight(signal.get('timestamp', datetime.now()))
            
            weighted_score = signal_score * source_weight * recency_weight
            total_score += weighted_score
            total_weight += source_weight * recency_weight
        
        # Normalize score
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.0
        
        # Calculate confidence based on signal count and agreement
        confidence = self.calculate_confidence(matching_signals, normalized_score)
        
        # Calculate edge and position size
        edge = self.calculate_edge(normalized_score, confidence, market)
        position_size = self.calculate_position_size(edge, market)
        
        return {
            'total_score': normalized_score,
            'signal_count': len(matching_signals),
            'confidence': confidence,
            'edge': edge,
            'position_size': position_size,
            'matched_signals': [self.signal_summary(s) for s in matching_signals[:5]]  # Top 5 signals
        }
    
    def extract_market_keywords(self, market: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords from market title and description."""
        text = f"{market.get('title', '')} {market.get('description', '')}"
        
        # Clean and tokenize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter for meaningful keywords (length > 2)
        keywords = [word for word in words if len(word) > 2]
        
        # Add category and tags
        if market.get('category'):
            keywords.append(market['category'].lower())
        
        for tag in market.get('tags', []):
            keywords.append(tag.lower())
        
        return list(set(keywords))  # Remove duplicates
    
    def find_matching_signals(self, market_keywords: List[str], intelligence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find intelligence signals that match market keywords."""
        matching_signals = []
        
        for signal in intelligence:
            signal_text = f"{signal.get('title', '')} {signal.get('text', '')}"
            signal_words = re.sub(r'[^\w\s]', ' ', signal_text.lower()).split()
            
            # Check for keyword matches
            matches = []
            for keyword in market_keywords:
                if keyword in signal_words or any(keyword in word for word in signal_words):
                    matches.append(keyword)
            
            # If we have matches, this signal is relevant
            if matches:
                signal_copy = signal.copy()
                signal_copy['matched_keywords'] = matches
                signal_copy['match_score'] = len(matches) / len(market_keywords)
                matching_signals.append(signal_copy)
        
        # Sort by relevance (match score)
        matching_signals.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matching_signals
    
    def score_signal(self, signal: Dict[str, Any], market_keywords: List[str]) -> float:
        """Score an individual intelligence signal."""
        signal_text = f"{signal.get('title', '')} {signal.get('text', '')}"
        signal_words = signal_text.lower().split()
        
        score = 0.0
        
        # Base score from keyword matching
        match_score = signal.get('match_score', 0.0)
        score += match_score * 0.5
        
        # Confidence keywords
        for keyword in self.keyword_weights['high_confidence']:
            if keyword in signal_text.lower():
                score += 0.3
        
        for keyword in self.keyword_weights['medium_confidence']:
            if keyword in signal_text.lower():
                score += 0.1
        
        # Market-moving keywords
        for keyword in self.keyword_weights['market_moving']:
            if keyword in signal_text.lower():
                score += 0.2
        
        # Signal score from source (e.g., upvotes, shares)
        if 'score' in signal and signal['score'] > 0:
            # Normalize score (log scale)
            normalized_source_score = min(0.3, math.log(signal['score'] + 1) / 10)
            score += normalized_source_score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_recency_weight(self, timestamp: datetime) -> float:
        """Calculate recency weight for a signal."""
        if not timestamp:
            return 0.5
        
        hours_old = (datetime.now() - timestamp).total_seconds() / 3600
        
        if hours_old <= 1:
            return 1.0
        elif hours_old <= 6:
            return 0.9
        elif hours_old <= 24:
            return 0.7
        elif hours_old <= 72:
            return 0.5
        elif hours_old <= 168:  # 1 week
            return 0.2
        else:
            return 0.1
    
    def calculate_confidence(self, signals: List[Dict[str, Any]], score: float) -> float:
        """Calculate confidence based on signal count and agreement."""
        if not signals:
            return 0.0
        
        # More signals = higher confidence (with diminishing returns)
        signal_confidence = min(1.0, len(signals) / 10)
        
        # Score magnitude affects confidence
        score_confidence = score
        
        # Source diversity affects confidence
        unique_sources = len(set(signal['source'] for signal in signals))
        source_diversity = min(1.0, unique_sources / 3)
        
        # Combine factors
        confidence = (signal_confidence * 0.4 + 
                     score_confidence * 0.4 + 
                     source_diversity * 0.2)
        
        return confidence
    
    def calculate_edge(self, score: float, confidence: float, market: Dict[str, Any]) -> float:
        """Calculate the expected edge for the market."""
        
        # Base edge from intelligence score and confidence
        base_edge = score * confidence
        
        # Adjust for market efficiency (higher volume = more efficient)
        volume = market.get('volume', 0)
        efficiency_discount = min(0.5, volume / 100000)  # Up to 50% discount for high volume
        
        # Adjust for time to resolution (more time = less edge)
        days = market.get('days_to_resolution', 365)
        if days <= 7:
            time_bonus = 0.2
        elif days <= 30:
            time_bonus = 0.1
        else:
            time_bonus = 0.0
        
        # Calculate final edge
        edge = base_edge * (1 - efficiency_discount) + time_bonus
        
        # Cap edge at reasonable levels
        return min(edge, 0.3)  # Max 30% edge
    
    def calculate_position_size(self, edge: float, market: Dict[str, Any]) -> float:
        """Calculate position size using simplified Kelly criterion."""
        
        # Assume 50-50 odds for simplicity (can be enhanced)
        win_probability = 0.5 + edge
        lose_probability = 1 - win_probability
        
        # Kelly fraction = (bp - q) / b
        # Where b = odds, p = win prob, q = lose prob
        # For even odds: kelly = 2p - 1
        kelly_fraction = 2 * win_probability - 1
        
        # Apply Kelly multiplier (quarter kelly is common)
        kelly_multiplier = 0.25  # This could come from config
        
        # Calculate position size (fraction of bankroll)
        position_fraction = max(0, kelly_fraction * kelly_multiplier)
        
        # Convert to dollar amount (would need bankroll config)
        # For now, return fraction
        return min(position_fraction, 0.1)  # Cap at 10% of bankroll
    
    def signal_summary(self, signal: Dict[str, Any]) -> Dict[str, str]:
        """Create a summary of a signal for logging."""
        return {
            'source': signal['source'],
            'title': signal.get('title', '')[:100],
            'score': signal.get('match_score', 0),
            'keywords': ', '.join(signal.get('matched_keywords', [])[:5])
        }