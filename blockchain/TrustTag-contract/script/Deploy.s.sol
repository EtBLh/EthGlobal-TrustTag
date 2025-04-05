// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagToken.sol";
import "../src/TrustTagStorage.sol";
import "../src/TrustTagVoting.sol";

contract DeployAllContracts is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Token
        TrustTagToken token = new TrustTagToken(vm.addr(deployerPrivateKey));
        console.log("TrustTagToken deployed at:", address(token));

        // 2. Deploy Storage
        TrustTagStorage storageContract = new TrustTagStorage(vm.addr(deployerPrivateKey), address(token));
        console.log("TrustTagStorage deployed at:", address(storageContract));

        // 3. Deploy Voting
        TrustTagVoting voting = new TrustTagVoting(address(token), address(storageContract), vm.addr(deployerPrivateKey));
        console.log("TrustTagVoting deployed at:", address(voting));

        // 4. Grant Updater Role
        storageContract.grantUpdater(address(voting));
        console.log("Updater role granted to Voting contract");

        vm.stopBroadcast();
    }
}
