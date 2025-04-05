<!-- 先下載和約工具 -->
curl -L https://foundry.paradigm.xyz/ | bash

<!-- 編譯和約 -->
cd blockchain/TrustTag-contract
git submodule update --init --recursive
foundryup
forge install OpenZeppelin/openzeppelin-contracts
forge build


TODO
test tee: 用假資料 how to test
前端串



塞一些 demo用資料