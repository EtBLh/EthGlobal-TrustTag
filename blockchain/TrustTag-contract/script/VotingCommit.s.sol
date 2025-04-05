// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagToken.sol";
import "../src/TrustTagVoting.sol";

contract VotingCommit is Script {
    function run() external {
        uint256 admin = vm.envUint("PRIVATE_KEY");
        uint256 pkUser1 = vm.envUint("PRIVATE_KEY_USER1");
        uint256 pkUser2 = vm.envUint("PRIVATE_KEY_USER2");
        uint256 pkUser3 = vm.envUint("PRIVATE_KEY_USER3");

        address tokenAddr = vm.envAddress("TOKEN_ADDRESS");
        address votingAddr = vm.envAddress("VOTE_ADDRESS");
        address target = vm.envAddress("TARGET_ADDRESS");

        TrustTagToken token = TrustTagToken(tokenAddr);
        TrustTagVoting voting = TrustTagVoting(votingAddr);

        vm.startBroadcast(admin);
        token.mint(vm.addr(pkUser1), 1000000 ether);
        token.mint(vm.addr(pkUser2), 1000000 ether);
        token.mint(vm.addr(pkUser3), 1000000 ether);
        _sendEth(vm.addr(pkUser1), 0.0001 ether);
        _sendEth(vm.addr(pkUser2), 0.0001 ether);
        _sendEth(vm.addr(pkUser3), 0.0001 ether);
        vm.stopBroadcast();

        // Stake and approve by users
        _stakeForUser(pkUser1, token, voting);
        _stakeForUser(pkUser2, token, voting);
        _stakeForUser(pkUser3, token, voting);

        string memory proposalId = "prop1";
        vm.broadcast(pkUser1);
        voting.createProposal(proposalId, target, true, "suspicious address", block.timestamp + 100);

        _commitVote(pkUser1, voting, proposalId, false, 30, "abcde");
        _commitVote(pkUser2, voting, proposalId, true, 80, "abc");
        _commitVote(pkUser3, voting, proposalId, true, 60, "abcd");
    }

    function _stakeForUser(uint256 pk, TrustTagToken token, TrustTagVoting voting) internal {
        vm.startBroadcast(pk);
        token.approve(address(voting), 1000 ether);
        voting.stake(1000 ether);
        vm.stopBroadcast();
    }

    function _commitVote(uint256 pk, TrustTagVoting voting, string memory proposalId, bool vote, uint8 prediction, string memory saltStr) internal {
        vm.startBroadcast(pk);
        bytes32 salt = bytes32(bytes(saltStr));
        bytes32 voteHash = keccak256(abi.encodePacked(vote, prediction, salt));
        voting.commitVote(proposalId, voteHash);
        vm.stopBroadcast();
    }

    function _sendEth(address to, uint256 amount) internal {
        (bool sent, ) = to.call{value: amount}("");
        require(sent, "ETH transfer failed");
    }
}