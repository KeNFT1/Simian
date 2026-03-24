// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
 * @title IDelegationRegistry
 * @dev Interface for delegate.cash delegation registry
 * @notice This interface allows checking and managing delegations for NFTs
 */
interface IDelegationRegistry {
    /**
     * @notice Check if an address is delegated to act on behalf of another for a specific NFT
     * @param delegate The address to check if it's a delegate
     * @param vault The vault address (NFT owner)
     * @param contract_ The contract address of the NFT
     * @param tokenId The token ID of the NFT
     * @return Whether the delegate has permission for this specific NFT
     */
    function checkDelegateForToken(
        address delegate,
        address vault,
        address contract_,
        uint256 tokenId
    ) external view returns (bool);
    
    /**
     * @notice Check if an address is delegated to act on behalf of another for an entire contract
     * @param delegate The address to check if it's a delegate
     * @param vault The vault address (NFT owner)
     * @param contract_ The contract address
     * @return Whether the delegate has permission for this entire contract
     */
    function checkDelegateForContract(
        address delegate,
        address vault,
        address contract_
    ) external view returns (bool);
}

/**
 * @title SimianRegistry
 * @dev Registry contract for Simian AI agents linked to NFT identities
 * @notice This contract manages agent configurations and verifies NFT ownership via delegate.cash
 */
contract SimianRegistry is ReentrancyGuard, Ownable {
    
    // Agent capability bitmask flags
    uint8 public constant CAPABILITY_TRADE = 1;     // 0b00000001
    uint8 public constant CAPABILITY_SOCIAL = 2;    // 0b00000010
    uint8 public constant CAPABILITY_GOVERN = 4;    // 0b00000100
    uint8 public constant CAPABILITY_CLAIM = 8;     // 0b00001000
    
    // Supported NFT collections
    struct SupportedCollection {
        address contractAddress;
        string name;
        bool active;
    }
    
    // Agent configuration struct
    struct AgentConfig {
        address nftContract;        // The NFT contract address
        uint256 tokenId;           // The specific token ID
        address owner;             // The NFT owner (vault)
        address delegate;          // The delegated agent address
        uint8 capabilities;        // Bitmask of enabled capabilities
        uint256 createdAt;         // Timestamp of agent creation
        uint256 lastActiveAt;      // Last time agent was active
        bool isActive;             // Whether the agent is currently active
        string metadataURI;        // URI for agent metadata/config
    }
    
    // Delegation registry contract
    IDelegationRegistry public immutable delegationRegistry;
    
    // Mappings
    mapping(bytes32 => AgentConfig) public agentConfigs;  // keccak256(nftContract, tokenId) => AgentConfig
    mapping(address => SupportedCollection) public supportedCollections;
    mapping(address => bytes32[]) public ownerToAgents;   // owner => agent IDs
    mapping(address => bytes32) public delegateToAgent;   // delegate => agent ID
    
    // Supported collection addresses array for enumeration
    address[] public collectionAddresses;
    
    // Events
    event AgentCreated(
        bytes32 indexed agentId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address owner,
        address delegate,
        uint8 capabilities
    );
    
    event CapabilitiesUpdated(
        bytes32 indexed agentId,
        uint8 oldCapabilities,
        uint8 newCapabilities
    );
    
    event AgentDeactivated(bytes32 indexed agentId, address indexed owner);
    
    event AgentReactivated(bytes32 indexed agentId, address indexed owner);
    
    event DelegateUpdated(
        bytes32 indexed agentId,
        address indexed oldDelegate,
        address indexed newDelegate
    );
    
    event CollectionAdded(address indexed contractAddress, string name);
    
    event CollectionStatusUpdated(address indexed contractAddress, bool active);
    
    /**
     * @dev Constructor
     * @param _delegationRegistry Address of the delegate.cash registry contract
     */
    constructor(address _delegationRegistry) {
        require(_delegationRegistry != address(0), "Invalid delegation registry");
        delegationRegistry = IDelegationRegistry(_delegationRegistry);
    }
    
    /**
     * @notice Create a new AI agent for an NFT
     * @param nftContract The contract address of the NFT
     * @param tokenId The token ID of the NFT
     * @param delegate The address that will act as the AI agent
     * @param capabilities Bitmask of capabilities to enable
     * @param metadataURI URI for agent metadata/configuration
     */
    function createAgent(
        address nftContract,
        uint256 tokenId,
        address delegate,
        uint8 capabilities,
        string calldata metadataURI
    ) external nonReentrant {
        require(nftContract != address(0), "Invalid NFT contract");
        require(delegate != address(0), "Invalid delegate address");
        require(supportedCollections[nftContract].active, "Collection not supported");
        require(capabilities > 0 && capabilities <= 15, "Invalid capabilities"); // Max 4 bits
        
        // Verify NFT ownership
        IERC721 nft = IERC721(nftContract);
        address nftOwner = nft.ownerOf(tokenId);
        require(nftOwner == msg.sender, "Not the NFT owner");
        
        // Generate unique agent ID
        bytes32 agentId = keccak256(abi.encodePacked(nftContract, tokenId));
        require(!agentConfigs[agentId].isActive, "Agent already exists for this NFT");
        require(delegateToAgent[delegate] == bytes32(0), "Delegate already assigned");
        
        // Create agent configuration
        agentConfigs[agentId] = AgentConfig({
            nftContract: nftContract,
            tokenId: tokenId,
            owner: msg.sender,
            delegate: delegate,
            capabilities: capabilities,
            createdAt: block.timestamp,
            lastActiveAt: block.timestamp,
            isActive: true,
            metadataURI: metadataURI
        });
        
        // Update mappings
        ownerToAgents[msg.sender].push(agentId);
        delegateToAgent[delegate] = agentId;
        
        emit AgentCreated(agentId, nftContract, tokenId, msg.sender, delegate, capabilities);
    }
    
    /**
     * @notice Update agent capabilities
     * @param agentId The unique agent identifier
     * @param newCapabilities New capability bitmask
     */
    function updateCapabilities(bytes32 agentId, uint8 newCapabilities) external {
        AgentConfig storage config = agentConfigs[agentId];
        require(config.owner == msg.sender, "Not the agent owner");
        require(config.isActive, "Agent not active");
        require(newCapabilities > 0 && newCapabilities <= 15, "Invalid capabilities");
        
        uint8 oldCapabilities = config.capabilities;
        config.capabilities = newCapabilities;
        config.lastActiveAt = block.timestamp;
        
        emit CapabilitiesUpdated(agentId, oldCapabilities, newCapabilities);
    }
    
    /**
     * @notice Deactivate an agent
     * @param agentId The unique agent identifier
     */
    function deactivateAgent(bytes32 agentId) external {
        AgentConfig storage config = agentConfigs[agentId];
        require(config.owner == msg.sender, "Not the agent owner");
        require(config.isActive, "Agent already inactive");
        
        config.isActive = false;
        delete delegateToAgent[config.delegate];
        
        emit AgentDeactivated(agentId, msg.sender);
    }
    
    /**
     * @notice Reactivate an agent with a new delegate
     * @param agentId The unique agent identifier
     * @param newDelegate The new delegate address
     */
    function reactivateAgent(bytes32 agentId, address newDelegate) external {
        AgentConfig storage config = agentConfigs[agentId];
        require(config.owner == msg.sender, "Not the agent owner");
        require(!config.isActive, "Agent already active");
        require(newDelegate != address(0), "Invalid delegate");
        require(delegateToAgent[newDelegate] == bytes32(0), "Delegate already assigned");
        
        address oldDelegate = config.delegate;
        config.delegate = newDelegate;
        config.isActive = true;
        config.lastActiveAt = block.timestamp;
        delegateToAgent[newDelegate] = agentId;
        
        emit AgentReactivated(agentId, msg.sender);
        emit DelegateUpdated(agentId, oldDelegate, newDelegate);
    }
    
    /**
     * @notice Verify that a delegate has permission to act for a specific NFT
     * @param delegate The delegate address to verify
     * @param nftContract The NFT contract address
     * @param tokenId The NFT token ID
     * @param owner The NFT owner address
     * @return isValid Whether the delegation is valid
     */
    function verifyDelegation(
        address delegate,
        address nftContract,
        uint256 tokenId,
        address owner
    ) external view returns (bool isValid) {
        // Check token-specific delegation first
        if (delegationRegistry.checkDelegateForToken(delegate, owner, nftContract, tokenId)) {
            return true;
        }
        
        // Check contract-wide delegation
        if (delegationRegistry.checkDelegateForContract(delegate, owner, nftContract)) {
            return true;
        }
        
        return false;
    }
    
    /**
     * @notice Check if an agent has a specific capability
     * @param agentId The unique agent identifier
     * @param capability The capability flag to check
     * @return hasCapability Whether the agent has this capability
     */
    function hasCapability(bytes32 agentId, uint8 capability) external view returns (bool hasCapability) {
        AgentConfig storage config = agentConfigs[agentId];
        require(config.isActive, "Agent not active");
        return (config.capabilities & capability) == capability;
    }
    
    /**
     * @notice Get agent configuration by ID
     * @param agentId The unique agent identifier
     * @return config The agent configuration
     */
    function getAgentConfig(bytes32 agentId) external view returns (AgentConfig memory config) {
        return agentConfigs[agentId];
    }
    
    /**
     * @notice Get all agent IDs for an owner
     * @param owner The NFT owner address
     * @return agentIds Array of agent identifiers
     */
    function getOwnerAgents(address owner) external view returns (bytes32[] memory agentIds) {
        return ownerToAgents[owner];
    }
    
    /**
     * @notice Add a supported NFT collection (owner only)
     * @param contractAddress The NFT contract address
     * @param name Human-readable collection name
     */
    function addSupportedCollection(address contractAddress, string calldata name) external onlyOwner {
        require(contractAddress != address(0), "Invalid contract address");
        require(!supportedCollections[contractAddress].active, "Collection already supported");
        
        supportedCollections[contractAddress] = SupportedCollection({
            contractAddress: contractAddress,
            name: name,
            active: true
        });
        
        collectionAddresses.push(contractAddress);
        
        emit CollectionAdded(contractAddress, name);
    }
    
    /**
     * @notice Update collection active status (owner only)
     * @param contractAddress The NFT contract address
     * @param active Whether the collection should be active
     */
    function setCollectionStatus(address contractAddress, bool active) external onlyOwner {
        require(contractAddress != address(0), "Invalid contract address");
        supportedCollections[contractAddress].active = active;
        
        emit CollectionStatusUpdated(contractAddress, active);
    }
    
    /**
     * @notice Get all supported collections
     * @return collections Array of collection addresses
     */
    function getSupportedCollections() external view returns (address[] memory collections) {
        return collectionAddresses;
    }
    
    /**
     * @notice Generate agent ID for an NFT
     * @param nftContract The NFT contract address
     * @param tokenId The NFT token ID
     * @return agentId The unique agent identifier
     */
    function generateAgentId(address nftContract, uint256 tokenId) external pure returns (bytes32 agentId) {
        return keccak256(abi.encodePacked(nftContract, tokenId));
    }
}