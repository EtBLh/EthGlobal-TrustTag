// import { PayBlock } from "./components/Pay";
// import { VerifyBlock } from "./components/Verify";
import Tag from '@/icons/tag.svg?react'
import RightArrow from '@/icons/rightarrow.svg?react'
// import ProposeCard from '@/components/propose-card'
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { proposal } from '@/lib/type';
import { Link, useNavigate } from 'react-router';
import ProposalListItem from '@/components/proposal-listitem'
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

export default function IndexPage() {

  const navigate = useNavigate();

  const [list, setList] = useState<any[]>([]);
  const [canClaim, setCanCliam] = useState(false);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}api/propose/list`)
      .then(res => res.json())
      .then(json => setList(json.list))
  }, [])

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}api/rewards`, {
      headers: {
        'Content-Type': 'application/json'
      },
      method: 'POST',
      body: JSON.stringify({
        address: '0x216e555e9a928Cc9f7bD19d9b948C907087Ed700'
      })
    })
      .then(res => res.json())
      .then(json => {
        if (json.list && json.list.filter((item:any) => item.claimed_at === null).length > 0) {
          setCanCliam(true);
        }
      })
  }, [])

  return (
    <main className="flex flex-col relative">
      <header className='text-lg font-bold flex flex-row gap-1/2 items-center gap-2 px-4 py-2 border-b border-gray-600'>
        <Tag width={24} height={24} style={{color: 'white'}}/>
        <span className='text-xl montserrat font-normal'>TrustTag</span>
      </header>
      <div className='flex flex-row items-baseline mt-6 px-2'>
        <span className='text-lg space-mono-semibold'>TAG</span>
        <span className='space-mono-bold text-5xl outfit flex-1'>12.32</span>
        <Button className='self-center bg-indigo-500' disabled={!canClaim} onClick={() => navigate('/claim')}>Claim</Button>
      </div>
      <Link to={'/propose'} viewTransition>
        <Alert className='my-4 mx-2 relative'>
            <Tag className="h-4 w-4" />
            <AlertTitle>Propose a Tag!</AlertTitle>
            <AlertDescription>
                Propse a tag to earn TAG token!
            </AlertDescription>
            <RightArrow style={{width:'24px', height: '24px'}} className="text-gray-1000 absolute right-1 top-1/2 transform-[translateY(-50%)]"/>
        </Alert>
      </Link>
      <Tabs defaultValue="proposals" className="flex-1 mx-2 mt-2">
        <TabsList className='w-full'>
          <TabsTrigger value="proposals">Current Proposals</TabsTrigger>
          <TabsTrigger value="user_vote">Past Proposals</TabsTrigger>
        </TabsList>
        <TabsContent value="proposals" className='w-full h-full'>
          <div className='flex flex-col w-full h-full gap-3 mt-2'>          
          {
            list.filter((item:any) => item.phase === 'Commit').map(props => <ProposalListItem {...props}/>)
          }
          </div>
        </TabsContent>
        <TabsContent value="user_vote">
          <div className='flex flex-col w-full h-full gap-3 mt-2'>          
            {
              list.filter((item:any) => item.phase !== 'Commit').map(props => <ProposalListItem {...props}/>)
            }
          </div>
        </TabsContent>
      </Tabs>
    </main>
  );
}
