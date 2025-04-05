import { ProposalIcon } from '@/components/proposal-icon';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import BackArrowIcon from '@/icons/backarrow.svg?react'
import { Link } from 'react-router';

const VotePage = () => {
  return (
    <main className="flex flex-col relative max-w-screen">
      <header className='text-lg font-bold flex flex-row gap-1/2 items-center gap-2 px-4 py-2 border-b border-gray-600'>
        <Link to='/home'>
          <BackArrowIcon width={24} height={24} style={{ color: 'white' }} />
        </Link>
        <span className='text-xl montserrat font-normal absolute left-1/2 transform-[translateX(-50%)]'>Vote</span>
      </header>
      <section className='px-2 flex flex-col flex-1 pb-3'>
        <div className='flex flex-col rounded-lg border-2 mt-2 p-2 gb-gray-200 '>
          <div className='flex flex-row items-center gap-2'>
            <ProposalIcon type='scam' />
            <span className='flex-1'>Is this address a scam?</span>
            <Badge variant='outline'>malicious</Badge>
          </div>
          <span className='text-sm text-gray-200'>Address</span>
          <div className='h-[48px] border-2 overflow-scroll rounded-lg leading-[36px] px-3'>
            0x216e555e9a928Cc9f7bD19d9b948C907087Ed700
          </div>

          <span className='mt-4 text-sm text-gray-200'>Proof</span>
          <div className='h-[48px] border-2 overflow-scroll rounded-lg leading-[36px] px-3'>
            https://etherscan.io/tx/0x8e76ea95879166b6d084a7ded9a27e877a372232303c686fc18496c9d1b1d04b
          </div>
        </div>
        <div className='flex-1'></div>

        <span className='mt-4 text-sm text-gray-200'>How many percentage you think others will vote yes?</span>
        <Slider max={100} value={[50]} onValueChange={() => {}} step={1} className='h-[32px]'/>
        <span className='mb-2 text-sm text-gray-200'>your choice</span>
        <div className='flex flex-row gap-2'>
          <Button className='flex-1'>No</Button>
          <Button className='flex-1'>Yes</Button>
        </div>
      </section>

    </main>
  )
}

export default VotePage;