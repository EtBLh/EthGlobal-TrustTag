// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagLabelStorage.sol";

contract DeployLabelStorage is Script {
    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        LabelStorage labelStorage = new LabelStorage(
            vm.addr(deployerPrivateKey)
        );

        vm.stopBroadcast();

        console.log("LabelStorage deployed to:", address(labelStorage));
    }
}
