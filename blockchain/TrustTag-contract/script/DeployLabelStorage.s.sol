// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagStorage.sol";

contract DeployLabelStorage is Script {
    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address tokenAddress = vm.envAddress("TOKEN_ADDRESS");

        vm.startBroadcast(deployerPrivateKey);

        TagStorage labelStorage = new TagStorage(vm.addr(deployerPrivateKey), tokenAddress);

        vm.stopBroadcast();

        console.log("LabelStorage deployed to:", address(labelStorage));
    }
}
