// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TrustTagToken is ERC20, Ownable {
    constructor(address initialOwner) ERC20("TrustTag Token", "TAG") Ownable(initialOwner) {
        _mint(initialOwner, 100 * 1_000_000 ether);
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}
