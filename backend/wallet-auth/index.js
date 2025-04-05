import express from 'express';
import cookieParser from 'cookie-parser';
import crypto from 'crypto';
import cors from 'cors';
import { verifySiweMessage } from '@worldcoin/minikit-js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(cors({
  origin: process.env.FRONTEND_URL || '*',
  credentials: true
}));

// Define handlers
const getNonce = (req, res) => {
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

const completeSiwe = async (req, res) => {
  try {
    const { payload, nonce } = req.body;
    
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
    } catch (error) {
      console.error('SIWE verification error:', error);
      res.status(400).json({
        status: 'error',
        isValid: false,
        message: error.message
      });
    }
  } catch (error) {
    console.error('Error in complete-siwe endpoint:', error);
    res.status(400).json({
      status: 'error',
      isValid: false,
      message: error.message
    });
  }
};

// Register routes
app.get('/api/nonce', getNonce);
app.post('/api/complete-siwe', completeSiwe);

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});