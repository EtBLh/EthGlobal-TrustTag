import { Button } from '@/components/ui/button'
import Tag from '@/icons/tag.svg?react'
import { useNavigate } from 'react-router'

const SplashScreen = () => {

    const navigate = useNavigate();

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
        <Button className='bg-indigo-300 rounded-full h-[48px] text-lg hover:bg-indigo-400' onClick={() => navigate('/verify')}>Enter</Button>
    </main>
    )
}

export default SplashScreen;