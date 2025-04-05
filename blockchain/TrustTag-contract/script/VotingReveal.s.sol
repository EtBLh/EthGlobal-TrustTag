// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagVoting.sol";

contract VotingReveal is Script {
    function run() external {
        uint256 pkAdmin = vm.envUint("PRIVATE_KEY");

        address votingAddr = vm.envAddress("VOTE_ADDRESS");
        address user1 = vm.addr(vm.envUint("PRIVATE_KEY_USER1"));
        address user2 = vm.addr(vm.envUint("PRIVATE_KEY_USER2"));
        address user3 = vm.addr(vm.envUint("PRIVATE_KEY_USER3"));

        TrustTagVoting voting = TrustTagVoting(votingAddr);
        string memory proposalId = "prop1";

        vm.startBroadcast(pkAdmin);
        voting.startRevealPhase(proposalId, block.timestamp + 100);

        voting.revealVote(proposalId, user1, false, 30, "abcde");
        voting.revealVote(proposalId, user2, true, 80, "abc");
        voting.revealVote(proposalId, user3, true, 60, "abcd");
        
        vm.stopBroadcast();
    }
}