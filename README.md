<!-- 編譯和約 -->
cd blockchain/TrustTag-contract
curl -L https://foundry.paradigm.xyz/ | bash

foundryup
forge install OpenZeppelin/openzeppelin-contracts