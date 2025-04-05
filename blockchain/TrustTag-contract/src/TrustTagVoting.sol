// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IProtocolToken {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract CommitRevealLabelVoting is Ownable {
    enum Phase { Commit, Reveal, Finished }

    struct VoterCommit {
        bytes32 voteHash;     // 投票的哈希值 (keccak256(vote + salt))
        bool revealed;        // 是否已揭露
        uint8 voteOption;     // 實際投票選項（reveal 後記錄）
        uint256 stake;        // 為這次投票所鎖定的代幣數量
    }

    struct Proposal {
        string description;                      // 提案內容描述
        address proposer;                        // 提案人地址
        uint256 deadline;                        // 投票截止時間（目前未實作自動過期）
        Phase phase;                             // 當前提案所處階段
        mapping(address => VoterCommit) commits; // 各 voter 的加密投票紀錄
        mapping(uint8 => uint256) voteTally;     // 每個選項的揭露票數統計
        address[] voters;                        // 投票參與者清單（為了迴圈使用）
        uint256 totalStake;                      // 該提案鎖定的總 stake 數
        bool finalized;                          // 是否已完成結算
        uint8 winningLabel;                      // 得票最多的 label 結果
    }

    IProtocolToken public token;       
    uint256 public proposalCount;                       // 紀錄目前共產生幾個提案
    mapping(uint256 => Proposal) public proposals;      // 依照提案 ID 存放每個提案的詳細資訊
    mapping(address => uint256) public stakes;          // 記錄每個使用者目前已 stake 但尚未參與投票的餘額，可被用來再次投票或提案。

    // 配置參數(規範提案、投票需要的最小 stake、投票不誠實或不揭露時的懲罰方式)
    uint256 public constant STAKE_TO_PROPOSE = 300 ether;
    uint256 public constant STAKE_TO_VOTE = 20 ether;
    uint256 public constant SLASH_FAILED_PROPOSAL = 300 ether;
    uint256 public constant SLASH_WRONG_VOTE = 20 ether;
    uint256 public constant SLASH_UNREVEALED = 10 ether;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event ProposalCreated(uint256 proposalId, string description);
    event VoteCommitted(uint256 proposalId, address voter);
    event VoteRevealed(uint256 proposalId, address voter, uint8 vote);
    event ProposalFinalized(uint256 proposalId, uint8 winningLabel);

    constructor(address _token, address initialOwner) Ownable(initialOwner) {
        token = IProtocolToken(_token);
    }

    // =============================
    // 💰 Stake Functions
    // =============================

    function stake(uint256 amount) external {
        require(token.transferFrom(msg.sender, address(this), amount), "Stake failed");
        stakes[msg.sender] += amount;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external {
        require(stakes[msg.sender] >= amount, "Insufficient stake");
        stakes[msg.sender] -= amount;
        require(token.transfer(msg.sender, amount), "Unstake failed");
        emit Unstaked(msg.sender, amount);
    }

    // =============================
    // 📌 Proposal & Voting
    // =============================

    function createProposal(string calldata description, uint256 duration) external {
        require(stakes[msg.sender] >= STAKE_TO_PROPOSE, "Need 300 stake to propose");

        proposalCount++;
        Proposal storage p = proposals[proposalCount];
        p.description = description;
        p.deadline = block.timestamp + duration;
        p.phase = Phase.Commit;
        p.proposer = msg.sender;

        stakes[msg.sender] -= STAKE_TO_PROPOSE;

        emit ProposalCreated(proposalCount, description);
    }

    function commitVote(uint256 proposalId, bytes32 voteHash) external {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Commit, "Not in commit phase");
        require(stakes[msg.sender] >= STAKE_TO_VOTE, "Need 20 stake to vote");
        require(p.commits[msg.sender].voteHash == 0, "Already committed");

        p.commits[msg.sender] = VoterCommit(voteHash, false, 0, STAKE_TO_VOTE);
        p.voters.push(msg.sender);
        p.totalStake += STAKE_TO_VOTE;

        stakes[msg.sender] -= STAKE_TO_VOTE;

        emit VoteCommitted(proposalId, msg.sender);
    }

    function startRevealPhase(uint256 proposalId) external onlyOwner {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Commit, "Not in commit phase");
        p.phase = Phase.Reveal;
    }

    function revealVote(uint256 proposalId, uint8 vote, bytes32 salt) external {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Reveal, "Not in reveal phase");

        VoterCommit storage c = p.commits[msg.sender];
        require(c.voteHash != 0, "No commitment");
        require(!c.revealed, "Already revealed");

        bytes32 expected = keccak256(abi.encodePacked(vote, salt));
        require(expected == c.voteHash, "Hash mismatch");

        c.revealed = true;
        c.voteOption = vote;
        p.voteTally[vote] += 1;

        emit VoteRevealed(proposalId, msg.sender, vote);
    }

    function finalize(uint256 proposalId) external onlyOwner {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Reveal, "Not in reveal phase");
        require(!p.finalized, "Already finalized");

        // 找出最多票的 label（若平票只取第一個）
        uint8 winner = 0;
        uint256 maxVotes = 0;
        for (uint8 i = 1; i <= 10; i++) {
            if (p.voteTally[i] > maxVotes) {
                maxVotes = p.voteTally[i];
                winner = i;
            }
        }

        p.winningLabel = winner;
        p.phase = Phase.Finished;
        p.finalized = true;

        // 奬勵與處罰
        for (uint i = 0; i < p.voters.length; i++) {
            address voter = p.voters[i];
            VoterCommit storage c = p.commits[voter];

            if (!c.revealed) {
                // 沒 reveal 被扣 10
                continue;
            }

            if (c.voteOption == winner) {
                // 投對票 → 奬勵退還 stake
                token.transfer(voter, c.stake);
            } else {
                // 投錯票 → stake 被懲罰
                continue;
            }
        }

        // 若沒人 reveal，提案者失敗 → 懲罰 300
        if (maxVotes == 0) {
            // proposer stake 已扣，不退還
        } else {
            // 提案者成功，可設計獎勵（此範例未退還 proposer 的 stake）
        }

        emit ProposalFinalized(proposalId, winner);
    }
}
