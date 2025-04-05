// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagVoting.sol";
import "../src/TrustTagStorage.sol";

contract VotingFinalize is Script {
    function run() external {
        uint256 pkAdmin = vm.envUint("PRIVATE_KEY");
        address votingAddr = vm.envAddress("VOTE_ADDRESS");
        address storageAddr = vm.envAddress("STORAGE_ADDRESS");
        address target = vm.envAddress("TARGET_ADDRESS");

        TrustTagVoting voting = TrustTagVoting(votingAddr);
        TrustTagStorage storageContract = TrustTagStorage(storageAddr);

        address[] memory voters = new address[](3);
        voters[0] = vm.addr(vm.envUint("PRIVATE_KEY_USER1"));
        voters[1] = vm.addr(vm.envUint("PRIVATE_KEY_USER2"));
        voters[2] = vm.addr(vm.envUint("PRIVATE_KEY_USER3"));

        uint256[] memory rewards = new uint256[](3);
        rewards[0] = 0 ether;
        rewards[1] = 10 ether;
        rewards[2] = 30;

        vm.startBroadcast(pkAdmin);
        voting.finalize("prop1", voters, rewards);

        (string memory desc, bool mal) = storageContract.getTagData(target);
        console.log("Final label:", desc, mal);
        vm.stopBroadcast();
    }
}
