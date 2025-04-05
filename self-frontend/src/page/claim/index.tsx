import { useEffect, useState } from "react";
import { Link } from "react-router";
import BackArrowIcon from '@/icons/backarrow.svg?react'
import Tag from '@/icons/tag.svg?react'
import { Button } from "@/components/ui/button";
import { shortenAddr } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const ClaimItem = (props: {
    address: string
    amount: number
}) => {
      
    return (
        <div className="flex flex-row gap-2 items-center">
            <Tag style={{color: 'white'}}/>
            <span className="flex-1">{shortenAddr(props.address)}</span>
            <Badge className="text-lg space-mono-regular">{props.amount}</Badge>
        </div>
    )
}

const ClaimPage = () => {
    const [list, setList] = useState<any[]>([]);

    useEffect(() => {
        fetch(`${import.meta.env.VITE_API_URL}api/rewards`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            address: MiniKit.walletAddress ?? '0x216e555e9a928Cc9f7bD19d9b948C907087Ed700'
          })
        })
          .then(res => res.json())
          .then(json => {
            setList(json.list.filter((item:any) => item.claimed_at === null));
          })
      }, [])
      
    return (
        <main className="flex flex-col relative flex-1">
            <header className='text-lg font-bold flex flex-row gap-1/2 items-center gap-2 px-4 py-2 border-b border-gray-600 fixed top-0 left-0 w-full h-[48px]'>
                <Link to='/home'>
                    <BackArrowIcon width={24} height={24} style={{ color: 'white' }} />
                </Link>
                <span className='text-xl montserrat font-normal absolute left-1/2 transform-[translateX(-50%)]'>Claim Rewards</span>
            </header>
            <div className='h-[48px]'/>
            <section className='p-2 flex-1 flex flex-col gap-2'>

            {
                list === undefined || list.length === 0? 'no rewards to claim':null
            }
            {
                list.map(item => <ClaimItem {...item}/>)
            }
            </section>
            <Button className="mb-2 mx-2 rounded-full bg-indigo-500" disabled={!(list !== undefined && list.length > 0)}>Claim All</Button>
        </main>
    )
}

export default ClaimPage;