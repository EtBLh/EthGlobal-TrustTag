<!-- 先下載和約工具 -->
curl -L https://foundry.paradigm.xyz/ | bash

<!-- 編譯和約 -->
cd blockchain/TrustTag-contract
foundryup
forge install OpenZeppelin/openzeppelin-contracts