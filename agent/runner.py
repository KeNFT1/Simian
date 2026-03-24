#!/usr/bin/env python3
"""
Simian Agent Runner - Standalone prediction market trading agent
"""

import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

from intelligence import IntelligenceGatherer
from market_scanner import MarketScanner
from scorer import MarketScorer
from executor import PaperTrader, LiveExecutor

class SimianAgent:
    def __init__(self, config_path):
        """Initialize the Simian agent with configuration."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Initialize components
        self.intelligence = IntelligenceGatherer(self.config['intelligenceSources'])
        self.scanner = MarketScanner(self.config['marketFilters'])
        self.scorer = MarketScorer()
        
        # Initialize executor based on config
        if self.config['execution']['autoExecute']:
            self.executor = LiveExecutor(self.config['riskParameters'])
            self.logger.info("🔴 LIVE MODE - Real trades will be executed!")
        else:
            self.executor = PaperTrader(self.config['riskParameters'])
            self.logger.info("📝 PAPER MODE - Simulation only")
    
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required keys
            required_keys = ['marketFilters', 'intelligenceSources', 'riskParameters', 'execution']
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required config key: {key}")
            
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.INFO
        if self.config.get('debug', False):
            log_level = logging.DEBUG
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger('SimianAgent')
    
    async def run_cycle(self):
        """Execute one complete trading cycle."""
        self.logger.info("🐵 Starting Simian agent cycle...")
        
        # Step 1: Gather intelligence
        self.logger.info("🧠 Gathering intelligence...")
        intelligence = await self.intelligence.gather_all()
        
        # Step 2: Scan markets
        self.logger.info("🔍 Scanning markets...")
        markets = await self.scanner.fetch_active_markets()
        
        # Step 3: Score markets against intelligence
        self.logger.info("📊 Scoring markets...")
        scored_markets = self.scorer.score_markets(markets, intelligence)
        
        # Step 4: Filter by edge threshold
        edge_threshold = self.config['riskParameters']['minEdgeThreshold']
        profitable_markets = [
            market for market in scored_markets 
            if market['edge'] >= edge_threshold
        ]
        
        self.logger.info(f"📈 Found {len(profitable_markets)} markets above {edge_threshold:.1%} edge threshold")
        
        # Step 5: Execute trades
        if profitable_markets:
            results = await self.executor.execute_trades(profitable_markets)
            self.log_results(results)
        else:
            self.logger.info("😴 No opportunities found this cycle")
        
        # Step 6: Save results
        self.save_cycle_results({
            'timestamp': datetime.now().isoformat(),
            'intelligence_signals': len(intelligence),
            'markets_scanned': len(markets),
            'markets_scored': len(scored_markets),
            'profitable_markets': len(profitable_markets),
            'trades_executed': len(profitable_markets) if profitable_markets else 0,
            'details': profitable_markets
        })
        
        self.logger.info("✅ Cycle complete")
    
    def log_results(self, results):
        """Log trading results."""
        if not results:
            return
        
        self.logger.info("💰 Trading Results:")
        for result in results:
            status = "✅" if result.get('success') else "❌"
            market_title = result['market']['title'][:50] + "..."
            self.logger.info(f"  {status} {market_title}")
            self.logger.info(f"    Edge: {result['market']['edge']:.1%}, Size: ${result['market']['position_size']}")
    
    def save_cycle_results(self, results):
        """Save cycle results to disk."""
        if not self.config['execution']['autoExecute']:
            # Paper trading - save to simulations directory
            results_dir = Path('data/simulations')
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            filename = results_dir / f"{timestamp}.json"
        else:
            # Live trading - save to live results
            results_dir = Path('data/live')
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            filename = results_dir / f"{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"💾 Results saved to {filename}")
    
    def print_summary(self):
        """Print agent configuration summary."""
        print("\n🐵 Simian Agent Configuration:")
        print("-" * 40)
        
        # Identity
        identity = self.config.get('identity', {})
        if identity.get('collection'):
            print(f"🦍 Identity: {identity.get('collection')} #{identity.get('tokenId')}")
        
        # Template
        template = self.config.get('template', 'custom')
        print(f"📋 Template: {template}")
        
        # Risk parameters
        risk = self.config['riskParameters']
        print(f"💰 Budget: ${risk['budget']}")
        print(f"📊 Max per position: ${risk['maxPerPosition']}")
        print(f"🔄 Max concurrent: {risk['maxConcurrentPositions']}")
        print(f"📈 Min edge: {risk['minEdgeThreshold']:.1%}")
        
        # Market filters
        filters = self.config['marketFilters']
        print(f"💧 Min volume: ${filters['minVolume']:,}")
        price_range = filters['priceRange']
        print(f"💲 Price range: {price_range['min']}¢ - {price_range['max']}¢")
        
        # Intelligence sources
        sources = self.config['intelligenceSources']
        enabled_sources = [name for name, enabled in sources.items() if enabled and name != 'customKeywords']
        print(f"🧠 Intelligence: {', '.join(enabled_sources)}")
        
        # Execution mode
        execution = self.config['execution']
        mode = "🔴 LIVE" if execution['autoExecute'] else "📝 PAPER"
        print(f"⚡ Mode: {mode}")
        print(f"⏰ Interval: {execution['cronInterval']}")
        
        print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description='Simian Agent Runner')
    parser.add_argument('--config', '-c', required=True, 
                       help='Path to agent configuration JSON file')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Print configuration summary and exit')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Load and initialize agent
    agent = SimianAgent(args.config)
    
    if args.debug:
        agent.config['debug'] = True
        agent.setup_logging()
    
    # Print summary if requested
    agent.print_summary()
    
    if args.summary:
        return
    
    # Run the agent
    try:
        import asyncio
        asyncio.run(agent.run_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
    except Exception as e:
        print(f"❌ Agent error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()