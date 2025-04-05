/* eslint-disable @typescript-eslint/no-explicit-any */
import Web3 from 'web3';
import { v4 as uuidv4 } from 'uuid';

// Import ABIs
import VoteContractABI from '../../blockchain/TrustTag-contract/out/TrustTagVoting.sol/TrustTagVoting.json';
// import LabelContractABI from '../../blockchain/TrustTag-contract/out/TrustTagStorage.sol/TrustTagStorage.json';

// Contract addresses from environment variables or hardcoded for dev
const VOTE_CONTRACT_ADDRESS = import.meta.env.VITE_VOTE_CONTRACT_ADDRESS || '0x3EE545015530c36F42A676190d98c86Fd3D6c659';

// Extend the Window interface to include the Ethereum provider
declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      request: (request: { method: string; params?: unknown[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
    };
  }
}

// Track the current account state
let currentAccount: string | null = null;

export async function connectWallet(): Promise<{ success: boolean; account?: string; error?: string }> {
  if (window.ethereum) {
    try {
      // Request account access
      const accounts: string[] = await window.ethereum.request({ method: 'eth_requestAccounts' });
      currentAccount = accounts[0];
      console.log('Connected account:', accounts[0]);
      return { success: true, account: accounts[0] };
    } catch (error: any) {
      // Handle errors (e.g., if the user rejects the request)
      console.error('User rejected the connection request:', error);
      return { success: false, error: error.message || 'Failed to connect' };
    }
  } else {
    // Inform the user that MetaMask is not installed
    const errorMessage = 'MetaMask is not installed. Please install MetaMask to use this feature.';
    console.error(errorMessage);
    return { success: false, error: errorMessage };
  }
}

export function getCurrentAccount(): string | null {
  return currentAccount;
}

// Set up account change listener
export function setupAccountChangeListener(): void {
  if (window.ethereum) {
    window.ethereum.on('accountsChanged', (accounts: string[]) => {
      currentAccount = accounts.length > 0 ? accounts[0] : null;
      console.log('Account changed:', currentAccount);
      
      // You can dispatch a custom event that React components can listen for
      window.dispatchEvent(new CustomEvent('accountChanged', { detail: currentAccount }));
    });
  }
}

/**
 * Create a proposal using MetaMask
 * @param target Target address for the proposal
 * @param malicious Whether the target is flagged as malicious
 * @param description Description of the proposal
 * @returns Object with transaction hash and proposal ID
 */
export async function createProposal(target: string, malicious: boolean, description: string): Promise<{
  success: boolean;
  transaction_hash?: string;
  proposal_id?: string;
  error?: string;
}> {
  if (!window.ethereum || !currentAccount) {
    return {
      success: false,
      error: 'MetaMask not connected. Please connect your wallet first.'
    };
  }

  try {
    // Generate a UUID for the proposal ID
    const proposalId = uuidv4();
    
    // Create a deadline 3 days from now (in seconds)
    const deadline = Math.floor(Date.now() / 1000) + (3 * 24 * 60 * 60);
    
    // Create a Web3 instance
    const web3 = new Web3(window.ethereum);
    
    // Create contract instance
    const contract = new web3.eth.Contract(
      VoteContractABI.abi,
      VOTE_CONTRACT_ADDRESS
    );
    
    // Encode function data
    const data = contract.methods.createProposal(
      proposalId,
      target,
      malicious,
      description,
      deadline
    ).encodeABI();
    
    // Send transaction via MetaMask
    const transactionParameters = {
      to: VOTE_CONTRACT_ADDRESS,
      from: currentAccount,
      data: data,
      chainId: '0x12c1', // Chain ID 4801
    };
    
    // Send the transaction
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [transactionParameters],
    });
    
    console.log('Proposal created, tx hash:', txHash);
    return {
      success: true,
      transaction_hash: txHash,
      proposal_id: proposalId
    };
  } catch (error: any) {
    console.error('Error creating proposal:', error);
    return {
      success: false,
      error: error.message || 'Unknown error creating proposal'
    };
  }
}

/**
 * Commit a vote for a proposal
 * @param proposalId ID of the proposal to vote on
 * @param vote Boolean value of the vote (true = yes, false = no)
 * @param yes_prediction Prediction percentage for yes votes (0-100)
 * @returns Object with transaction hash
 */
export async function commitVote(proposalId: string, vote: boolean, yes_prediction: number): Promise<{
  success: boolean;
  transaction_hash?: string;
  salt?: string;
  error?: string;
}> {
  if (!window.ethereum || !currentAccount) {
    return {
      success: false,
      error: 'MetaMask not connected. Please connect your wallet first.'
    };
  }

  try {
    // Generate a random salt for vote commitment
    const salt = '0x' + Array.from(window.crypto.getRandomValues(new Uint8Array(32)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    // Create a Web3 instance
    const web3 = new Web3(window.ethereum);
    
    // Hash the vote, yes_prediction and salt to create the commitment
    const voteHash = web3.utils.soliditySha3(
      { type: 'bool', value: vote },
      { type: 'uint256', value: yes_prediction.toString() },
      { type: 'bytes32', value: salt }
    );
    
    // Create contract instance
    const contract = new web3.eth.Contract(
      VoteContractABI.abi,
      VOTE_CONTRACT_ADDRESS
    );
    
    // Encode function data for commitVote
    const data = contract.methods.commitVote(
      proposalId,
      voteHash
    ).encodeABI();
    
    // Send transaction via MetaMask
    const transactionParameters = {
      to: VOTE_CONTRACT_ADDRESS,
      from: currentAccount,
      data: data,
      chainId: '0x12c1', // Chain ID 4801
    };
    
    // Send the transaction
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [transactionParameters],
    });
    
    console.log('Vote committed, tx hash:', txHash);
    
    // Save the salt in local storage for later reveal
    localStorage.setItem(`vote-salt-${proposalId}`, salt);
    localStorage.setItem(`vote-value-${proposalId}`, vote.toString());
    localStorage.setItem(`vote-prediction-${proposalId}`, yes_prediction.toString());
    
    return {
      success: true,
      transaction_hash: txHash,
      salt: salt
    };
  } catch (error: any) {
    console.error('Error committing vote:', error);
    return {
      success: false,
      error: error.message || 'Unknown error committing vote'
    };
  }
}

/**
 * Reveal a previously committed vote
 * @param proposalId ID of the proposal 
 * @returns Object with transaction hash
 */
export async function revealVote(proposalId: string): Promise<{
  success: boolean;
  transaction_hash?: string;
  error?: string;
}> {
  if (!window.ethereum || !currentAccount) {
    return {
      success: false,
      error: 'MetaMask not connected. Please connect your wallet first.'
    };
  }

  try {
    // Get the saved vote information
    const salt = localStorage.getItem(`vote-salt-${proposalId}`);
    const voteString = localStorage.getItem(`vote-value-${proposalId}`);
    const predictionString = localStorage.getItem(`vote-prediction-${proposalId}`);
    
    if (!salt || !voteString || !predictionString) {
      return {
        success: false,
        error: 'No vote information found for this proposal. Did you commit a vote?'
      };
    }
    
    const vote = voteString === 'true';
    const yes_prediction = parseInt(predictionString);
    
    // Create a Web3 instance
    const web3 = new Web3(window.ethereum);
    
    // Create contract instance
    const contract = new web3.eth.Contract(
      VoteContractABI.abi,
      VOTE_CONTRACT_ADDRESS
    );
    
    // Encode function data for revealVote
    const data = contract.methods.revealVote(
      proposalId,
      vote,
      yes_prediction,
      salt
    ).encodeABI();
    
    // Send transaction via MetaMask
    const transactionParameters = {
      to: VOTE_CONTRACT_ADDRESS,
      from: currentAccount,
      data: data,
      chainId: '0x12c1', // Chain ID 4801
    };
    
    // Send the transaction
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [transactionParameters],
    });
    
    console.log('Vote revealed, tx hash:', txHash);
    return {
      success: true,
      transaction_hash: txHash
    };
  } catch (error: any) {
    console.error('Error revealing vote:', error);
    return {
      success: false,
      error: error.message || 'Unknown error revealing vote'
    };
  }
}