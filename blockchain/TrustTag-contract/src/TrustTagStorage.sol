// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TagStorage is Ownable {
    struct TagData {
        string description;
        bool malicious;
    }

    mapping(bytes32 => TagData) public tags;
    mapping(address => uint256) public stakes;

    uint256 public constant MIN_STAKE_REQUIREMENT = 300;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function stake(uint256 amount) external {
        require(
            token.transferFrom(msg.sender, address(this), amount),
            "Stake failed"
        );
        stakes[msg.sender] += amount;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external {
        require(stakes[msg.sender] >= amount, "Insufficient stake");
        stakes[msg.sender] -= amount;
        require(token.transfer(msg.sender, amount), "Unstake failed");
        emit Unstaked(msg.sender, amount);
    }

    function updateLabel(
        address targetAddress,
        string calldata description,
        bool malicious
    ) external onlyOwner {
        bytes32 hashedAddress = keccak256(abi.encodePacked(targetAddress));
        tags[hashedAddress] = TagData(description, malicious);
    }

    function getTagData(
        address targetAddress
    ) external view returns (string memory, bool) {
        require(
            stakes[msg.sender] >= MIN_STAKE_REQUIREMENT,
            "Insufficient stake to access data"
        );

        bytes32 hashedAddress = keccak256(abi.encodePacked(targetAddress));
        TagData memory data = tags[hashedAddress];

        return (data.description, data.malicious);
    }
}
