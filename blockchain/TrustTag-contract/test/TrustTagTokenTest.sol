// test/TrustTagToken.t.sol
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/TrustTagToken.sol";

contract TrustTagTokenTest is Test {
    TrustTagToken public token;
    address public owner;
    address public user;

    function setUp() public {
        owner = address(this); // 測試合約本身就是 deployer / owner
        user = address(0xBEEF); // 隨便一個測試地址
        token = new TrustTagToken(owner);
    }

    function test_NameSymbolDecimals() public {
        assertEq(token.name(), "TrustTag Token");
        assertEq(token.symbol(), "TAG");
        assertEq(token.decimals(), 18);
    }

    function test_InitialSupply() public {
        uint256 expectedSupply = 100 * 1_000_000 * 1e18;
        assertEq(token.totalSupply(), expectedSupply);
        assertEq(token.balanceOf(owner), expectedSupply);
    }

    function test_MintToUser() public {
        uint256 amount = 1_000 * 1e18;
        token.mint(user, amount);
        assertEq(token.balanceOf(user), amount);
    }

    function test_RevertIfNonOwnerMints() public {
        vm.prank(user); // 模擬 user 呼叫
        vm.expectRevert();
        token.mint(user, 1e18);
    }
}
