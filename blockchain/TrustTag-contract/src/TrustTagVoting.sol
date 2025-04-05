// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

interface IProtocolToken {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract CommitRevealLabelVoting is Ownable {
    enum Phase { Commit, Reveal, Finished }

    struct VoterCommit {
        bytes32 voteHash;     // 投票的哈希值，計算方式為 keccak256(vote + prediction + salt)
        bool revealed;        // 是否已揭露
        bool voteOption;      // 是否認定為惡意（YES 為 true，NO 為 false），reveal 後紀錄
        uint8 prediction;     // 對於 YES 投票的預測百分比（例如 60 表示預測 60% 投 YES）
        uint256 stake;        // 本次投票所鎖定的 stake
        uint256 reward;       // 投票後獲得的獎勵
        bool claimed;         // 是否已經領取獎勵
    }

    struct Proposal {
        address target;                          // 被提案標註的地址
        bool malicious;                          // 最終判定是否為惡意地址
        string description;                      // Label 描述
        address proposer;                        // 提案者
        uint256 deadline;                        // 提案截止時間
        Phase phase;                             // 提案目前階段
        mapping(address => VoterCommit) commits; // 投票紀錄
        mapping(bool => uint256) voteTally;      // YES/NO 統計數量
        address[] voters;                        // 投票者清單
        uint256 totalStake;                      // 總 stake
        bool finalized;                          // 是否完成結算
        bool winningLabel;                       // 最終標註結果
    }

    IProtocolToken public token;       
    uint256 public proposalCount;                       // 紀錄目前共產生幾個提案
    mapping(uint256 => Proposal) public proposals;      // 依照提案 ID 存放每個提案的詳細資訊
    mapping(address => uint256) public stakes;          // 記錄每個使用者目前已 stake 但尚未參與投票的餘額，可被用來再次投票或提案。

    // 配置參數(規範提案、投票需要的最小 stake、投票不誠實或不揭露時的懲罰方式)
    uint256 public constant STAKE_TO_PROPOSE = 300 ether;
    uint256 public constant STAKE_TO_VOTE = 20 ether;
    uint256 public constant SLASH_FAILED_PROPOSAL = 300 ether;
    uint256 public constant SLASH_UNREVEALED = 10 ether;
    uint256 public constant PROPOSAL_DURATION = 3 days;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event ProposalCreated(uint256 proposalId, string description);
    event VoteCommitted(uint256 proposalId, address voter);
    event VoteRevealed(uint256 proposalId, address voter, bool vote, uint8 prediction);
    event ProposalFinalized(uint256 proposalId, bool label);
    event RewardClaimed(uint256 proposalId, address voter, uint256 amount);

    constructor(address _token, address initialOwner) Ownable(initialOwner) {
        token = IProtocolToken(_token);
    }

    // =============================
    // Stake Functions
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
    // Proposal & Voting
    // =============================

    function createProposal(string calldata description, address target) external {
        require(stakes[msg.sender] >= STAKE_TO_PROPOSE, "Need 300 stake to propose");

        proposalCount++;
        Proposal storage p = proposals[proposalCount];
        p.description = description;
        p.deadline = block.timestamp + PROPOSAL_DURATION;
        p.phase = Phase.Commit;
        p.proposer = msg.sender;
        p.target = target;

        stakes[msg.sender] -= STAKE_TO_PROPOSE;

        emit ProposalCreated(proposalCount, description);
    }

    function commitVote(uint256 proposalId, bytes32 voteHash) external {
        Proposal storage p = proposals[proposalId];
        require(block.timestamp <= p.deadline, "Proposal expired");
        require(p.phase == Phase.Commit, "Not in commit phase");
        require(stakes[msg.sender] >= STAKE_TO_VOTE, "Need 20 stake to vote");
        require(p.commits[msg.sender].voteHash == 0, "Already committed");
        require(voteHash != 0, "Vote hash cannot be zero");

        p.commits[msg.sender] = VoterCommit(voteHash, false, false, 0, STAKE_TO_VOTE, 0, false);
        p.voters.push(msg.sender);
        p.totalStake += STAKE_TO_VOTE;
        stakes[msg.sender] -= STAKE_TO_VOTE;

        emit VoteCommitted(proposalId, msg.sender);
    }

    function startRevealPhase(uint256 proposalId) external onlyOwner {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Commit, "Not in commit phase");
        require(block.timestamp >= p.deadline, "Commit phase not ended");

        p.phase = Phase.Reveal;
        p.deadline = block.timestamp + PROPOSAL_DURATION;
    }

    function revealVote(uint256 proposalId, bool vote, uint8 prediction, bytes32 salt) external {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Reveal, "Not in reveal phase");

        VoterCommit storage c = p.commits[msg.sender];
        require(c.voteHash != 0, "No commitment");
        require(!c.revealed, "Already revealed");

        bytes32 expected = keccak256(abi.encodePacked(vote, prediction, salt));
        require(expected == c.voteHash, "Hash mismatch");

        c.revealed = true;
        c.voteOption = vote;
        c.prediction = prediction;
        p.voteTally[vote] += 1;

        emit VoteRevealed(proposalId, msg.sender, vote, prediction);
    }

    function finalize(uint256 proposalId, address[] calldata voterList, uint256[] calldata rewardList) external onlyOwner {
        Proposal storage p = proposals[proposalId];
        require(p.phase == Phase.Reveal, "Not in reveal phase");
        require(!p.finalized, "Already finalized");
        require(block.timestamp >= p.deadline, "Reveal phase not ended");
        require(voterList.length == rewardList.length, "Length mismatch");

        bool winner = p.voteTally[true] >= p.voteTally[false];
        p.winningLabel = winner;
        p.phase = Phase.Finished;
        p.finalized = true;
        p.malicious = winner;

        for (uint i = 0; i < voterList.length; i++) {
            address voter = voterList[i];
            uint256 reward = rewardList[i];
            VoterCommit storage c = p.commits[voter];

            if (!c.revealed) {
                stakes[voter] = stakes[voter] + c.stake - SLASH_UNREVEALED;
                c.reward = 0;
            }
            else if (c.voteOption != winner) {
                c.reward = 0;
            }
            else {
                c.reward = reward;
                stakes[voter] += c.stake;
            }
        }

        if (p.voteTally[true] == 0 && p.voteTally[false] == 0) {
            // 沒人 reveal 的話，提案者被懲罰
            // stake 已扣，這邊不返還
        } else {
            stakes[p.proposer] += STAKE_TO_PROPOSE;
        }

        emit ProposalFinalized(proposalId, winner);
    }

    function claimReward(uint256 proposalId) external {
        Proposal storage p = proposals[proposalId];
        VoterCommit storage c = p.commits[msg.sender];
        require(p.finalized, "Not finalized");
        require(c.revealed, "Did not reveal");
        require(!c.claimed, "Already claimed");
        require(c.reward > 0, "No reward");

        c.claimed = true;
        require(token.transfer(msg.sender, c.reward), "Reward transfer failed");
        emit RewardClaimed(proposalId, msg.sender, c.reward);
    }

    function getProposalVoters(uint256 proposalId) external view returns (address[] memory) {
        return proposals[proposalId].voters;
    }
}
