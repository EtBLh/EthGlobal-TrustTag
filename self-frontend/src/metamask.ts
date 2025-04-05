/* eslint-disable @typescript-eslint/no-explicit-any */
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