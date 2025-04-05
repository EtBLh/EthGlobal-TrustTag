// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/TrustTagToken.sol";
import "../src/TrustTagStorage.sol";
import "../src/TrustTagVoting.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";


contract UpdateLabel is Script {
    function run() external {
        // 環境變數
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address tokenAddress = vm.envAddress("TOKEN_ADDRESS");
        address storageAddress = vm.envAddress("STORAGE_ADDRESS");
        address votingAddress = vm.envAddress("VOTE_ADDRESS");
        address target = vm.envAddress("TARGET_ADDRESS");

        IERC20 token = IERC20(tokenAddress);
        TrustTagStorage storageContract = TrustTagStorage(storageAddress);
        TrustTagVoting votingContract = TrustTagVoting(votingAddress);

        vm.startBroadcast(privateKey);
        console.log("Balance:", token.balanceOf(vm.addr(privateKey)));

        // 1️⃣ Approve 給 Storage, Voting 合約
        token.approve(storageAddress, 300 ether);
        token.approve(votingAddress, 10000 ether);

        // 2️⃣ Stake
        storageContract.stake(300 ether);
        votingContract.stake(10000 ether);

        // 3️⃣ Update label（你是 ADMIN 或 UPDATER）
        bytes32 hashedTarget = keccak256(abi.encodePacked(target));
        storageContract.updateLabel(hashedTarget, "GOD ADDRESS", false);

        // 4️⃣ Read back (這裡用 log，呼叫 view function 也可以改寫為 call script 回來印)
        (string memory description, bool malicious) = storageContract.getTagData(target);
        console.log("Tag:", description, malicious);

        vm.stopBroadcast();
    }
}
