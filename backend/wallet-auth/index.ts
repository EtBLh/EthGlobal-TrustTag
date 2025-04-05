import express from 'express';
// import cookieParser from 'cookie-parser';
import { NextRequest, NextResponse } from 'next/server';
import { MiniAppWalletAuthSuccessPayload } from '@worldcoin/minikit-js';
import crypto from 'crypto';
// import cors from 'cors';

// Import handler functions (mock imports as we'll adapt them)
// Note: We need to adapt them because they use Next.js specific APIs

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
// app.use(cookieParser());
// app.use(cors({
//   origin: process.env.FRONTEND_URL || '*',
//   credentials: true
// }));

// Adapter function to convert Express request to NextRequest (simplified)
function createNextRequest(req: express.Request): NextRequest {
  const url = new URL(req.url, `http://${req.headers.host}`);
  
  // Create a minimal NextRequest-like object
  return {
    url: url.toString(),
    json: async () => req.body,
    cookies: {
      get: (name: string) => ({ name, value: req.cookies[name] }),
    },
  } as unknown as NextRequest;
}

// Adapter function to apply NextResponse to Express response
function applyNextResponse(res: express.Response, nextRes: NextResponse): void {
  // Set status
  res.status(nextRes.status);
  
  // Apply headers
  for (const [key, value] of Object.entries(nextRes.headers.entries())) {
    if (key === 'set-cookie') {
      res.setHeader('Set-Cookie', value);
    } else {
      res.setHeader(key, value);
    }
  }
  
  // Send body
  res.send(nextRes.json());
}

// Adapted nonce handler
app.get('/nonce', (req, res) => {
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
});

// Adapted complete-siwe handler
app.post('/complete-siwe', async (req, res) => {
  try {
    const { payload, nonce } = req.body as {
      payload: MiniAppWalletAuthSuccessPayload;
      nonce: string;
    };
    
    // Check nonce in cookie
    if (nonce !== req.cookies.siwe) {
      return res.status(400).json({
        status: 'error',
        isValid: false,
        message: 'Invalid nonce'
      });
    }
    
    // Import verifySiweMessage dynamically (since it's used server-side)
    const { verifySiweMessage } = await import('@worldcoin/minikit-js');
    
    // Verify SIWE message
    const validMessage = await verifySiweMessage(payload, nonce);
    
    // Clear the cookie
    res.clearCookie('siwe');
    
    // Return success response
    return res.json({
      status: 'success',
      isValid: validMessage.isValid,
      address: validMessage.siweMessageData.address
    });
  } catch (error: any) {
    console.error('Error in complete-siwe endpoint:', error);
    return res.status(400).json({
      status: 'error',
      isValid: false,
      message: error.message
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});