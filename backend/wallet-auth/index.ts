import express from 'express';
import { Request, Response } from 'express';
import cookieParser from 'cookie-parser';
import crypto from 'crypto';
import cors from 'cors';
import { MiniAppWalletAuthSuccessPayload } from '@worldcoin/minikit-js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(cors({
  origin: process.env.FRONTEND_URL || '*',
  credentials: true
}));

// Define handlers separately with explicit return types
const getNonce = (req: Request, res: Response): void => {
  try {
    // Generate nonce
    const nonce = crypto.randomUUID().replace(/-/g, "");
    
    // Set cookie directly using Express
    res.cookie('siwe', nonce, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });
    
    // Return nonce
    res.json({ nonce });
  } catch (error) {
    console.error('Error in nonce endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

const completeSiwe = async (req: Request, res: Response): Promise<void> => {
  try {
    const { payload, nonce } = req.body as {
      payload: MiniAppWalletAuthSuccessPayload;
      nonce: string;
    };
    
    // Check nonce in cookie
    if (nonce !== req.cookies.siwe) {
      res.status(400).json({
        status: 'error',
        isValid: false,
        message: 'Invalid nonce'
      });
      return;
    }
    
    try {
      // Import the verification function directly
      // Don't use dynamic import here since we're already importing the type
      const { verifySiweMessage } = require('@worldcoin/minikit-js');
      
      // Verify SIWE message
      const validMessage = await verifySiweMessage(payload, nonce);
      
      // Clear the cookie
      res.clearCookie('siwe');
      
      // Return success response
      res.json({
        status: 'success',
        isValid: validMessage.isValid,
        address: validMessage.siweMessageData.address
      });
    } catch (error: any) {
      console.error('SIWE verification error:', error);
      res.status(400).json({
        status: 'error',
        isValid: false,
        message: error.message
      });
    }
  } catch (error: any) {
    console.error('Error in complete-siwe endpoint:', error);
    res.status(400).json({
      status: 'error',
      isValid: false,
      message: error.message
    });
  }
};

// Register routes with the defined handlers
app.get('/nonce', getNonce);
app.post('/complete-siwe', completeSiwe);

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});