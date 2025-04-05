// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IPermit2 {
    struct PermitTransferFrom {
        address token;
        uint160 amount;
        uint256 nonce;
        uint256 deadline;
    }

    struct SignatureTransferDetails {
        address to;
        uint160 requestedAmount;
    }

    function permitTransferFrom(
        PermitTransferFrom calldata permit,
        SignatureTransferDetails calldata transferDetails,
        address owner,
        bytes calldata signature
    ) external;
}

contract Permit2Transfer is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address user = vm.addr(pk);
        address permit2 = vm.envAddress("PERMIT2_ADDRESS");
        address token = vm.envAddress("TOKEN_ADDRESS");
        address receiver = vm.envAddress("ADDRESS_USER1");

        uint160 amount = 10 ether;
        uint256 deadline = block.timestamp + 1 hours;
        uint256 chainId = block.chainid;

        // ✅ 使用合法格式 nonce（wordPos=0, bitPos=3）
        uint256 nonce = (0 << 8) | 3;

        console.log("Nonce:", nonce);
        console.log("Balance Before:");
        console.log("User:", IERC20(token).balanceOf(user));
        console.log("Receiver:", IERC20(token).balanceOf(receiver));

        IPermit2.PermitTransferFrom memory permit = IPermit2.PermitTransferFrom({
            token: token,
            amount: amount,
            nonce: nonce,
            deadline: deadline
        });

        bytes32 DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256("Permit2"),
                keccak256("1"),
                chainId,
                permit2
            )
        );

        bytes32 PERMIT_TYPEHASH = keccak256(
            "PermitTransferFrom(address token,uint160 amount,uint256 nonce,uint256 deadline)"
        );
        bytes32 structHash = keccak256(
            abi.encode(PERMIT_TYPEHASH, permit.token, permit.amount, permit.nonce, permit.deadline)
        );

        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        bytes memory signature = abi.encodePacked(r, s, v);

        IPermit2.SignatureTransferDetails memory transferDetails = IPermit2.SignatureTransferDetails({
            to: receiver,
            requestedAmount: amount
        });

        vm.startBroadcast(pk);
        IPermit2(permit2).permitTransferFrom(permit, transferDetails, user, signature);
        vm.stopBroadcast();

        console.log("Balance After:");
        console.log("User:", IERC20(token).balanceOf(user));
        console.log("Receiver:", IERC20(token).balanceOf(receiver));
    }
}