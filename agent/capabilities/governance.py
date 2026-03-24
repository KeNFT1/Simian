"""
Simian Agent Governance Capability

This module handles autonomous DAO governance participation for Simian agents,
including Snapshot voting, on-chain governance, and proposal analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import time
import json
import hashlib

import aiohttp
from web3 import Web3
from web3.contract import Contract


logger = logging.getLogger(__name__)


class VoteChoice(Enum):
    """Vote choices for governance proposals."""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"
    # For ranked choice voting
    OPTION_1 = "1"
    OPTION_2 = "2"
    OPTION_3 = "3"


class ProposalStatus(Enum):
    """Status of governance proposals."""
    PENDING = "pending"
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    DEFEATED = "defeated"
    EXECUTED = "executed"
    EXPIRED = "expired"


class GovernanceType(Enum):
    """Types of governance systems."""
    SNAPSHOT = "snapshot"          # Off-chain Snapshot governance
    ONCHAIN_GOVERNOR = "governor"  # OpenZeppelin Governor
    COMPOUND = "compound"          # Compound-style governance
    AAVE = "aave"                 # Aave governance
    CUSTOM = "custom"             # Custom governance contract


@dataclass
class ProposalInfo:
    """Information about a governance proposal."""
    proposal_id: str
    title: str
    description: str
    proposer: str
    governance_type: GovernanceType
    space_id: Optional[str] = None  # For Snapshot
    
    # Timing
    created_at: int = 0
    start_time: int = 0
    end_time: int = 0
    execution_time: Optional[int] = None
    
    # Voting info
    choices: List[str] = field(default_factory=list)
    voting_power_required: int = 0
    quorum_required: int = 0
    
    # Current state
    status: ProposalStatus = ProposalStatus.PENDING
    scores: Dict[str, float] = field(default_factory=dict)
    total_votes: int = 0
    
    # Metadata
    ipfs_hash: Optional[str] = None
    discussion_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class VotingDecision:
    """Agent's decision on how to vote."""
    proposal_id: str
    choice: Union[VoteChoice, str, int]
    confidence: float  # 0.0 to 1.0
    reasoning: str
    should_vote: bool
    voting_power: int = 0
    
    # Risk assessment
    risk_level: str = "low"  # low, medium, high
    financial_impact: str = "none"  # none, low, medium, high
    governance_impact: str = "minimal"  # minimal, moderate, significant


class GovernanceStrategy:
    """Base class for governance voting strategies."""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.voting_history: List[VotingDecision] = []
    
    async def analyze_proposal(self, proposal: ProposalInfo) -> VotingDecision:
        """
        Analyze a proposal and return voting decision.
        
        Args:
            proposal: Proposal information
            
        Returns:
            VotingDecision with choice and reasoning
        """
        raise NotImplementedError("Subclasses must implement analyze_proposal")
    
    def get_voting_stats(self) -> Dict[str, Union[int, float]]:
        """Get statistics about voting behavior."""
        if not self.voting_history:
            return {}
        
        total_votes = len(self.voting_history)
        for_votes = sum(1 for vote in self.voting_history if vote.choice == VoteChoice.FOR)
        against_votes = sum(1 for vote in self.voting_history if vote.choice == VoteChoice.AGAINST)
        abstains = sum(1 for vote in self.voting_history if vote.choice == VoteChoice.ABSTAIN)
        
        return {
            'total_votes': total_votes,
            'for_percentage': (for_votes / total_votes) * 100,
            'against_percentage': (against_votes / total_votes) * 100,
            'abstain_percentage': (abstains / total_votes) * 100,
            'average_confidence': sum(vote.confidence for vote in self.voting_history) / total_votes
        }


class ConservativeStrategy(GovernanceStrategy):
    """Conservative governance strategy - tends to vote against risky proposals."""
    
    def __init__(self, config: Dict):
        super().__init__("conservative", config)
        self.risk_threshold = config.get('risk_threshold', 0.3)
        self.min_confidence = config.get('min_confidence', 0.7)
    
    async def analyze_proposal(self, proposal: ProposalInfo) -> VotingDecision:
        """Conservative analysis focusing on risk assessment."""
        # Basic risk scoring based on proposal characteristics
        risk_score = 0.0
        reasoning_parts = []
        
        # Check proposal type and content
        title_lower = proposal.title.lower()
        description_lower = proposal.description.lower()
        
        # High-risk keywords
        high_risk_keywords = ['upgrade', 'migration', 'emergency', 'fund', 'treasury', 'token', 'mint']
        medium_risk_keywords = ['parameter', 'fee', 'reward', 'incentive', 'grant']
        low_risk_keywords = ['documentation', 'website', 'community', 'partnership']
        
        for keyword in high_risk_keywords:
            if keyword in title_lower or keyword in description_lower:
                risk_score += 0.3
                reasoning_parts.append(f"High-risk keyword detected: {keyword}")
        
        for keyword in medium_risk_keywords:
            if keyword in title_lower or keyword in description_lower:
                risk_score += 0.1
                reasoning_parts.append(f"Medium-risk keyword detected: {keyword}")
        
        for keyword in low_risk_keywords:
            if keyword in title_lower or keyword in description_lower:
                risk_score -= 0.1
                reasoning_parts.append(f"Low-risk keyword detected: {keyword}")
        
        # Time pressure assessment
        time_to_vote = proposal.end_time - int(time.time())
        if time_to_vote < 86400:  # Less than 24 hours
            risk_score += 0.2
            reasoning_parts.append("Short voting period increases risk")
        
        # Proposal age assessment  
        proposal_age = int(time.time()) - proposal.created_at
        if proposal_age < 3600:  # Less than 1 hour old
            risk_score += 0.1
            reasoning_parts.append("Very new proposal, limited review time")
        
        # Quorum and participation
        if proposal.total_votes < proposal.quorum_required * 0.5:
            risk_score += 0.1
            reasoning_parts.append("Low participation may indicate lack of community support")
        
        # Determine vote choice
        risk_score = min(risk_score, 1.0)  # Cap at 1.0
        
        if risk_score > self.risk_threshold:
            choice = VoteChoice.AGAINST
            confidence = min(risk_score, 0.9)
            reasoning = f"Conservative vote AGAINST due to high risk: {', '.join(reasoning_parts)}"
            should_vote = confidence >= self.min_confidence
            risk_level = "high"
        elif risk_score < 0.1:
            choice = VoteChoice.FOR
            confidence = 0.7
            reasoning = f"Low-risk proposal, voting FOR: {', '.join(reasoning_parts) if reasoning_parts else 'No significant risk factors'}"
            should_vote = True
            risk_level = "low"
        else:
            choice = VoteChoice.ABSTAIN
            confidence = 0.5
            reasoning = f"Moderate risk, abstaining: {', '.join(reasoning_parts)}"
            should_vote = False
            risk_level = "medium"
        
        return VotingDecision(
            proposal_id=proposal.proposal_id,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            should_vote=should_vote,
            risk_level=risk_level
        )


class CommunityAlignedStrategy(GovernanceStrategy):
    """Strategy that follows community consensus and delegate recommendations."""
    
    def __init__(self, config: Dict):
        super().__init__("community_aligned", config)
        self.trusted_delegates = config.get('trusted_delegates', [])
        self.consensus_threshold = config.get('consensus_threshold', 0.6)
    
    async def analyze_proposal(self, proposal: ProposalInfo) -> VotingDecision:
        """Analyze based on community sentiment and delegate votes."""
        # Check current vote distribution
        total_voting_power = sum(proposal.scores.values())
        
        if total_voting_power == 0:
            return VotingDecision(
                proposal_id=proposal.proposal_id,
                choice=VoteChoice.ABSTAIN,
                confidence=0.0,
                reasoning="No votes cast yet, waiting for community signal",
                should_vote=False,
                risk_level="low"
            )
        
        # Calculate vote percentages
        for_percentage = proposal.scores.get('For', 0) / total_voting_power
        against_percentage = proposal.scores.get('Against', 0) / total_voting_power
        
        # Follow strong community consensus
        if for_percentage >= self.consensus_threshold:
            choice = VoteChoice.FOR
            confidence = for_percentage
            reasoning = f"Following strong community consensus FOR ({for_percentage:.1%})"
            should_vote = True
        elif against_percentage >= self.consensus_threshold:
            choice = VoteChoice.AGAINST
            confidence = against_percentage
            reasoning = f"Following strong community consensus AGAINST ({against_percentage:.1%})"
            should_vote = True
        else:
            choice = VoteChoice.ABSTAIN
            confidence = 0.5
            reasoning = f"No clear consensus (FOR: {for_percentage:.1%}, AGAINST: {against_percentage:.1%})"
            should_vote = False
        
        # TODO: Check trusted delegate votes
        # TODO: Analyze discussion sentiment
        
        return VotingDecision(
            proposal_id=proposal.proposal_id,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            should_vote=should_vote,
            risk_level="low"
        )


class SnapshotClient:
    """Client for interacting with Snapshot governance."""
    
    def __init__(self, api_url: str = "https://hub.snapshot.org/graphql"):
        self.api_url = api_url
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
    
    async def get_active_proposals(self, space_id: str) -> List[ProposalInfo]:
        """Get active proposals for a Snapshot space."""
        query = """
        query GetProposals($space: String!) {
          proposals(
            where: {
              space: $space,
              state: "active"
            },
            orderBy: "created",
            orderDirection: desc
          ) {
            id
            title
            body
            author
            created
            start
            end
            choices
            scores_total
            scores
            scores_by_strategy
            state
            space {
              id
              name
            }
          }
        }
        """
        
        variables = {"space": space_id}
        
        session = await self._get_session()
        async with session.post(
            self.api_url,
            json={"query": query, "variables": variables}
        ) as response:
            if response.status == 200:
                data = await response.json()
                proposals = []
                
                for prop in data.get('data', {}).get('proposals', []):
                    proposal_info = ProposalInfo(
                        proposal_id=prop['id'],
                        title=prop['title'],
                        description=prop['body'],
                        proposer=prop['author'],
                        governance_type=GovernanceType.SNAPSHOT,
                        space_id=space_id,
                        created_at=prop['created'],
                        start_time=prop['start'],
                        end_time=prop['end'],
                        choices=prop['choices'],
                        scores={choice: score for choice, score in zip(prop['choices'], prop['scores'])},
                        total_votes=prop['scores_total'],
                        status=ProposalStatus.ACTIVE
                    )
                    proposals.append(proposal_info)
                
                return proposals
            else:
                logger.error(f"Snapshot API error: {response.status}")
                return []
    
    async def submit_vote(
        self,
        space_id: str,
        proposal_id: str,
        choice: Union[int, Dict[str, int]],
        voter_address: str,
        private_key: str
    ) -> bool:
        """
        Submit a vote to Snapshot (requires signing).
        
        Note: This is a simplified version. Full implementation would require
        proper message signing with the wallet's private key.
        """
        # TODO: Implement vote signing and submission
        # This involves:
        # 1. Creating the vote message
        # 2. Signing with wallet private key
        # 3. Submitting via Snapshot API
        
        logger.info(f"Would submit vote for proposal {proposal_id}: choice {choice}")
        return True


class OnChainGovernanceClient:
    """Client for interacting with on-chain governance contracts."""
    
    def __init__(self, web3: Web3, contract_address: str, contract_abi: List):
        self.w3 = web3
        self.contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    
    async def get_active_proposals(self) -> List[ProposalInfo]:
        """Get active on-chain proposals."""
        # This would depend on the specific governance contract
        # Different contracts (Governor, Compound, etc.) have different interfaces
        
        # Example for OpenZeppelin Governor
        try:
            # Get proposal count and iterate
            # This is a simplified example
            proposals = []
            # TODO: Implement based on specific governance contract
            return proposals
        except Exception as e:
            logger.error(f"Error fetching on-chain proposals: {e}")
            return []
    
    async def submit_vote(
        self,
        proposal_id: str,
        support: bool,
        voter_address: str,
        private_key: str
    ) -> bool:
        """Submit an on-chain vote."""
        try:
            # TODO: Build and send vote transaction
            # This requires:
            # 1. Building the vote transaction
            # 2. Signing with private key
            # 3. Broadcasting to network
            # 4. Waiting for confirmation
            
            logger.info(f"Would submit on-chain vote for proposal {proposal_id}")
            return True
        except Exception as e:
            logger.error(f"Error submitting on-chain vote: {e}")
            return False


class SimianGovernanceAgent:
    """Main governance agent that manages voting across different DAOs."""
    
    def __init__(
        self,
        agent_id: str,
        strategies: List[GovernanceStrategy],
        config: Dict
    ):
        self.agent_id = agent_id
        self.strategies = strategies
        self.config = config
        
        # Governance clients
        self.snapshot_client = SnapshotClient()
        self.onchain_clients: Dict[str, OnChainGovernanceClient] = {}
        
        # Tracked DAOs and spaces
        self.snapshot_spaces = config.get('snapshot_spaces', [])
        self.onchain_contracts = config.get('onchain_contracts', {})
        
        # Voting state
        self.voted_proposals: set = set()
        self.pending_votes: Dict[str, VotingDecision] = {}
        
        self.is_active = False
    
    async def start_governance_monitoring(self):
        """Start monitoring governance proposals and voting."""
        self.is_active = True
        logger.info(f"Governance agent {self.agent_id} started")
        
        while self.is_active:
            try:
                await self._governance_cycle()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Governance cycle error: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    def stop_governance_monitoring(self):
        """Stop governance monitoring."""
        self.is_active = False
        logger.info(f"Governance agent {self.agent_id} stopped")
    
    async def _governance_cycle(self):
        """Execute one governance monitoring cycle."""
        # Check Snapshot spaces
        for space_id in self.snapshot_spaces:
            await self._process_snapshot_space(space_id)
        
        # Check on-chain governance
        for contract_name, contract_info in self.onchain_contracts.items():
            await self._process_onchain_governance(contract_name, contract_info)
    
    async def _process_snapshot_space(self, space_id: str):
        """Process proposals in a Snapshot space."""
        try:
            proposals = await self.snapshot_client.get_active_proposals(space_id)
            
            for proposal in proposals:
                if proposal.proposal_id not in self.voted_proposals:
                    await self._analyze_and_vote_proposal(proposal)
        except Exception as e:
            logger.error(f"Error processing Snapshot space {space_id}: {e}")
    
    async def _process_onchain_governance(self, contract_name: str, contract_info: Dict):
        """Process on-chain governance proposals."""
        try:
            if contract_name not in self.onchain_clients:
                # Initialize client if not exists
                # TODO: Create OnChainGovernanceClient based on contract_info
                pass
            
            # client = self.onchain_clients[contract_name]
            # proposals = await client.get_active_proposals()
            # 
            # for proposal in proposals:
            #     if proposal.proposal_id not in self.voted_proposals:
            #         await self._analyze_and_vote_proposal(proposal)
        except Exception as e:
            logger.error(f"Error processing on-chain governance {contract_name}: {e}")
    
    async def _analyze_and_vote_proposal(self, proposal: ProposalInfo):
        """Analyze proposal with all strategies and vote if consensus."""
        decisions = []
        
        # Get decisions from all strategies
        for strategy in self.strategies:
            try:
                decision = await strategy.analyze_proposal(proposal)
                decisions.append((strategy, decision))
                logger.info(f"Strategy {strategy.name} decision for {proposal.proposal_id}: {decision.choice.value} (confidence: {decision.confidence})")
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed for proposal {proposal.proposal_id}: {e}")
        
        # Combine decisions (weighted by confidence)
        if decisions:
            final_decision = self._combine_decisions(decisions)
            
            if final_decision.should_vote:
                success = await self._execute_vote(proposal, final_decision)
                
                if success:
                    self.voted_proposals.add(proposal.proposal_id)
                    
                    # Record decision for each strategy
                    for strategy, decision in decisions:
                        strategy.voting_history.append(decision)
                    
                    logger.info(f"Voted on proposal {proposal.proposal_id}: {final_decision.choice.value}")
                else:
                    logger.error(f"Failed to vote on proposal {proposal.proposal_id}")
            else:
                logger.info(f"Decided not to vote on proposal {proposal.proposal_id}: {final_decision.reasoning}")
    
    def _combine_decisions(self, decisions: List[Tuple[GovernanceStrategy, VotingDecision]]) -> VotingDecision:
        """Combine decisions from multiple strategies."""
        if len(decisions) == 1:
            return decisions[0][1]
        
        # Weight by confidence and strategy priority
        weighted_votes = {}
        total_weight = 0
        
        for strategy, decision in decisions:
            if decision.should_vote:
                weight = decision.confidence
                choice = decision.choice
                
                if choice not in weighted_votes:
                    weighted_votes[choice] = 0
                
                weighted_votes[choice] += weight
                total_weight += weight
        
        if not weighted_votes:
            # No strategies want to vote
            return VotingDecision(
                proposal_id=decisions[0][1].proposal_id,
                choice=VoteChoice.ABSTAIN,
                confidence=0.0,
                reasoning="No strategies recommend voting",
                should_vote=False
            )
        
        # Find highest weighted choice
        best_choice = max(weighted_votes.keys(), key=lambda c: weighted_votes[c])
        confidence = weighted_votes[best_choice] / total_weight
        
        # Collect reasoning from supporting strategies
        supporting_reasons = [
            decision.reasoning 
            for _, decision in decisions 
            if decision.choice == best_choice and decision.should_vote
        ]
        
        return VotingDecision(
            proposal_id=decisions[0][1].proposal_id,
            choice=best_choice,
            confidence=confidence,
            reasoning=f"Combined decision: {'; '.join(supporting_reasons)}",
            should_vote=confidence >= 0.6  # Require 60% confidence
        )
    
    async def _execute_vote(self, proposal: ProposalInfo, decision: VotingDecision) -> bool:
        """Execute the voting decision."""
        if proposal.governance_type == GovernanceType.SNAPSHOT:
            # Convert choice to Snapshot format
            if isinstance(decision.choice, VoteChoice):
                if decision.choice == VoteChoice.FOR:
                    choice = 1
                elif decision.choice == VoteChoice.AGAINST:
                    choice = 2
                else:
                    choice = 3  # Abstain
            else:
                choice = decision.choice
            
            return await self.snapshot_client.submit_vote(
                space_id=proposal.space_id,
                proposal_id=proposal.proposal_id,
                choice=choice,
                voter_address=self.config.get('wallet_address'),
                private_key=self.config.get('private_key')
            )
        else:
            # On-chain governance
            # TODO: Implement on-chain voting
            logger.info(f"Would execute on-chain vote: {decision.choice.value}")
            return True


# TODO: Implement the following features:
# - [ ] Wallet integration for actual vote signing and submission
# - [ ] Advanced proposal analysis using NLP and sentiment analysis
# - [ ] Integration with governance forums and discussion platforms
# - [ ] Delegation management (delegating voting power to others)
# - [ ] Proposal creation and submission capabilities
# - [ ] Multi-DAO coordination and conflict resolution
# - [ ] Governance performance tracking and analytics
# - [ ] Emergency response protocols for critical proposals
# - [ ] Integration with Simian delegation verification
# - [ ] Custom governance contract support
# - [ ] Vote outcome prediction and impact analysis
# - [ ] Automated governance reporting and transparency