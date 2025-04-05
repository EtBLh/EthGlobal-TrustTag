// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract TrustTagStorage is AccessControl {
    struct TagData {
        string description;
        bool malicious;
    }

    IERC20 public token;

    mapping(bytes32 => TagData) public tags;
    mapping(address => uint256) public stakes;

    uint256 public constant MIN_STAKE_REQUIREMENT = 300 ether;

    // 定義角色常數
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event LabelUpdated(bytes32 indexed hashedAddress, string description, bool malicious);

    constructor(address _admin, address _token) {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);      // 管理者
        _grantRole(UPDATER_ROLE, _admin);            // 初始也可以是 updater
        token = IERC20(_token);
    }

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
        bytes32 hashedAddress,
        string calldata description,
        bool malicious
    ) external onlyRole(UPDATER_ROLE) {
        tags[hashedAddress] = TagData(description, malicious);
        emit LabelUpdated(hashedAddress, description, malicious);
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

    function grantUpdater(address updater) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(UPDATER_ROLE, updater);
    }

    function revokeUpdater(address updater) external onlyRole(DEFAULT_ADMIN_ROLE) {
        revokeRole(UPDATER_ROLE, updater);
    }
}
