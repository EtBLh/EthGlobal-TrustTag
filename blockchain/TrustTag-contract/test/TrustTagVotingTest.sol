// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/TrustTagVoting.sol";
import "../src/TrustTagStorage.sol";
import "../src/TrustTagToken.sol";

contract CommitRevealLabelVotingTest is Test {
    TrustTagVoting public voting;
    TrustTagToken public token;
    TrustTagStorage public tagStorage;

    address public owner;
    address public user = address(0x1);
    address public user2 = address(0x2);
    address public user3 = address(0x3);
    address public user4 = address(0x4);

    function setUp() public {
        owner = address(this); // 測試合約本身就是 deployer / owner
        token = new TrustTagToken(owner);
        tagStorage = new TrustTagStorage(owner, address(token));
        voting = new TrustTagVoting(address(token), address(tagStorage), owner);

        token.mint(user, 1000 ether);
        token.mint(user2, 1000 ether);
        token.mint(user3, 1000 ether);
        token.mint(user4, 1000 ether);
        token.mint(address(voting), 1000 ether);

        tagStorage.grantUpdater(address(voting));
        token.approve(address(tagStorage), 1000 ether);
        tagStorage.stake(500 ether);

        vm.startPrank(user);
        token.approve(address(voting), 1000 ether);
        voting.stake(500 ether);
        vm.stopPrank();

        vm.startPrank(user2);
        token.approve(address(voting), 1000 ether);
        voting.stake(100 ether);
        vm.stopPrank();

        vm.startPrank(user3);
        token.approve(address(voting), 1000 ether);
        voting.stake(100 ether);
        vm.stopPrank();

        vm.startPrank(user4);
        token.approve(address(voting), 1000 ether);
        voting.stake(100 ether);
        vm.stopPrank();
    }

    function testProposalLifecycle() public {
        string memory proposalId = "prop1";
        address target = address(0xdead);
        uint256 deadline = block.timestamp + 1 days;

        // Create proposal
        vm.prank(user);
        voting.createProposal(proposalId, target, true, "suspicious activity", deadline);

        bool[] memory votes = new bool[](3);
        uint8[] memory predictions = new uint8[](3);
        bytes32[] memory salts = new bytes32[](3);

        votes[0] = true;
        votes[1] = true;
        votes[2] = false;

        predictions[0] = 80;
        predictions[1] = 60;
        predictions[2] = 30;

        salts[0] = "abc";
        salts[1] = "abcd";
        salts[2] = "abcde";

        bytes32 voteHash = keccak256(abi.encodePacked(votes[0], predictions[0], salts[0]));

        vm.prank(user2);
        voting.commitVote(proposalId, voteHash);

        bytes32 voteHash2 = keccak256(abi.encodePacked(votes[1], predictions[1], salts[1]));

        vm.prank(user3);
        voting.commitVote(proposalId, voteHash2);

        bytes32 voteHash3 = keccak256(abi.encodePacked(votes[2], predictions[2], salts[2]));

        vm.prank(user4);
        voting.commitVote(proposalId, voteHash3);

        // Fast forward time and start reveal
        vm.warp(deadline + 1);
        voting.startRevealPhase(proposalId, block.timestamp + 1 days);

        // Reveal vote (owner only)
        vm.startPrank(address(this));
        voting.revealVote(proposalId, user2, votes[0], predictions[0], salts[0]);
        voting.revealVote(proposalId, user3, votes[1], predictions[1], salts[1]);
        voting.revealVote(proposalId, user4, votes[2], predictions[2], salts[2]);
        vm.stopPrank();

        // Finalize
        address[] memory voters = new address[](3);
        uint256[] memory rewards = new uint256[](3);
        voters[0] = user2;
        voters[1] = user3;
        voters[2] = user4;
        rewards[0] = 10 ether;
        rewards[1] = 30 ether;
        rewards[2] = 0;

        vm.warp(block.timestamp + 2 days);
        voting.finalize(proposalId, voters, rewards);

        // Check tag storage update
        (string memory description, bool malicious) = tagStorage.getTagData(target);
        assertEq(description, "suspicious activity");
        assertEq(malicious, true);
    }
}