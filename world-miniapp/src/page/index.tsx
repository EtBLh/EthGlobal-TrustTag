import { Button } from '@/components/ui/button'
import Tag from '@/icons/tag.svg?react'
import { MiniKit } from '@worldcoin/minikit-js'
import { useNavigate } from 'react-router'

const SplashScreen = () => {

    const navigate = useNavigate();

    const signInWithWallet = async () => {
        // if (!MiniKit.isInstalled()) {
        //     alert('minikit not found');
        //     console.log('minikit not found')
        //     return;
        // }
    
        const res = await fetch(`${import.meta.env.VITE_AUTH_API_URL}api/nonce`,{
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'whatever'
            }
        })
        const { nonce } = await res.json()
    
        const { finalPayload } = await MiniKit.commandsAsync.walletAuth({
            nonce: nonce,
            expirationTime: new Date(new Date().getTime() + 7 * 24 * 60 * 60 * 1000),
            notBefore: new Date(new Date().getTime() - 24 * 60 * 60 * 1000),
            statement: '[walletAuth] TrustTag',
        })
    
        if (finalPayload.status === 'error') {
            console.log('wallet auth error', finalPayload)
            return
        } else {
            console.log(finalPayload)
            await fetch(`${import.meta.env.VITE_AUTH_API_URL}api/complete-siwe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    payload: finalPayload,
                    nonce,
                }),
            })
            navigate('/home');
        }
    }

    return (
    <main className="flex min-h-screen flex-col relative p-4">
        <div className='flex flex-row items-center gap-2'>
            <Tag style={{color: 'white', width: 32, height: 32}} />
            <span className='text-4xl outfit'>TrustTag</span>
            <span>EthGlobal</span>
        </div>
        <div className='flex-1 space-mono-regular mt-2'>
            A Decentralized address tagging system
        </div>
        <Button className='bg-indigo-300 rounded-full h-[48px] text-lg hover:bg-indigo-400' onClick={() => signInWithWallet()}>Enter</Button>
    </main>
    )
}

export default SplashScreen;