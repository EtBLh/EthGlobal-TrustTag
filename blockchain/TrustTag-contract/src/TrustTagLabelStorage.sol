// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * Label Storage Contract
 */
contract LabelStorage is Ownable {
    struct LabelData {
        bytes32 integrityHash;
        string encryptedData;
    }

    mapping(address => LabelData) public labels;

    constructor(address initialOwner) Ownable(initialOwner) {}

    function updateLabel(address targetAddress, bytes32 integrityHash, string calldata encryptedData) external onlyOwner {
        labels[targetAddress] = LabelData(integrityHash, encryptedData);
    }
}
