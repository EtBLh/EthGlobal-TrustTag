import Web3 from 'web3';
import { MiniKit } from '@worldcoin/minikit-js'
import VoteContractABI from '../../blockchain/TrustTag-contract/out/TrustTagVoting.sol/TrustTagVoting.json';
import LabelContractABI from '../../blockchain/TrustTag-contract/out/TrustTagStorage.sol/TrustTagStorage.json';
import { Abi } from 'viem';
const labelAbi = LabelContractABI.abi as Abi;
const voteAbi = VoteContractABI.abi as Abi;

// // Contract addresses - set from environment variables or config
// const VOTE_CONTRACT_ADDRESS = process.env.REACT_APP_VOTE_CONTRACT_ADDRESS || '0x3EE545015530c36F42A676190d98c86Fd3D6c659';
// const LABEL_CONTRACT_ADDRESS = process.env.REACT_APP_LABEL_CONTRACT_ADDRESS || '0xEFd89ffe442DfeCC12bDcBfef74a2764c1408177';

export const stakeWithPermit = async (amount: number, deadline: Date) => {
  const tx = {
    address: "0xYourContractAddress",
    abi: labelAbi,
    functionName: "stakeWithPermit",
    args: [
      amount, 
      deadline, 
      "PERMIT2_SIGNATURE_PLACEHOLDER_0"  // placeholder to auto-generate the Permit2 signature
    ]
  };

  const { finalPayload } = await MiniKit.commandsAsync.sendTransaction({
    transaction: [tx]
  });

  if (finalPayload.status === "success") {
    return finalPayload.transaction_id;
    // console.log("Stake with Permit transaction sent, tx id:", finalPayload.transaction_id);
  } else {
    console.error("Stake with Permit transaction failed:", finalPayload);
  }
};

export const createProposal = async (target: string, malicious: boolean, description: string) => {
  // Create a deadline 3 days from now
  const proposalId = crypto.randomUUID(); // Generate a random UUID for this vote
  const deadline = Math.floor(Date.now() / 1000) + (3 * 24 * 60 * 60); // Current time in seconds + 3 days in seconds
  const tx = {
    address: import.meta.env.VITE_VOTE_CON_ADDR,
    abi: voteAbi,
    functionName: "createProposal",
    args: [proposalId, target, malicious, description, deadline]
  };

  const { finalPayload } = await MiniKit.commandsAsync.sendTransaction({
    transaction: [tx]
  });

  if (finalPayload.status === "success") {
    return { transaction_id: finalPayload.transaction_id, proposalId };
  } else {
    console.error("Proposal creation failed:", finalPayload);
    return null;
  }
};

export const commitVote = async (proposalId: string, vote: boolean, yes_prediction: number) => {
  // Generate a random salt for vote commitment
  const salt = '0x' + Array.from(window.crypto.getRandomValues(new Uint8Array(32)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  // Hash the vote, salt and yes_prediction to create the commitment
  const voteHash = Web3.utils.soliditySha3(
    { type: 'bool', value: vote },
    { type: 'uint256', value: yes_prediction.toString() },
    { type: 'bytes32', value: salt }
  );

  // Note: The function is missing the proposalId parameter
  const tx = {
    address: (process.env.VITE_VOTE_CON_ADDR) as string,
    abi: voteAbi,
    functionName: "commitVote",
    args: [proposalId, voteHash]
  };

  const { finalPayload } = await MiniKit.commandsAsync.sendTransaction({
    transaction: [tx]
  });

  if (finalPayload.status === "success") {
    return finalPayload.transaction_id;
  } else {
    console.error("Commit vote failed:", finalPayload);
    return null;
  }
};

export const claimReward = async (proposalId: string) => {
  const tx = {
    address: "0xYourContractAddress",
    abi: voteAbi,
    functionName: "claimReward",
    args: [proposalId]
  };

  const { finalPayload } = await MiniKit.commandsAsync.sendTransaction({
    transaction: [tx]
  });

  if (finalPayload.status === "success") {
    return finalPayload.transaction_id;
  } else {
    console.error("Claim reward failed:", finalPayload);
    return null;
  }
};
