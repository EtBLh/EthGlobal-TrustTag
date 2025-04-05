import React, { useState, useEffect } from 'react';
import SelfQRcodeWrapper, { SelfAppBuilder } from '@selfxyz/qrcode';
import { v4 as uuidv4 } from 'uuid';

function VerifyPage() {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    setUserId(uuidv4());
  }, []);

  if (!userId) return null;

  const selfApp = new SelfAppBuilder({
    appName: "Self Playground",
    scope: "self-playground",
    endpoint: "https://df78-42-72-239-22.ngrok-free.app/api/verify",
    // endpoint: "https://c622-118-169-75-84.ngrok-free.app/api/verify",
    endpointType: "https",
    logoBase64: "https://i.imgur.com/Rz8B3s7.png",
    userId,
    disclosures: {
        minimumAge: 18,
        date_of_birth: true,
    },
    devMode: false,
  }).build();

  return (
    <div className='flex flex-col h-full items-center justify-center text-center'>
      <p className='text-sm'>please use Self app to verify your human identify</p>
    
        <SelfQRcodeWrapper
            darkMode
            selfApp={selfApp}
            type='websocket'
            onSuccess={() => {
                console.log("✅ 驗證成功！");
            }}
            size={300}
        />

      <p style={{ fontSize: "0.8rem", color: "gray" }}>
        User ID: {userId.substring(0, 8)}...
      </p>
    </div>
  );
}

export default VerifyPage;