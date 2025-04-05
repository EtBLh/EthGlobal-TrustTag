import { ProposalIcon } from '@/components/proposal-icon';
import ProposalListItem from '@/components/proposal-listitem';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import BackArrowIcon from '@/icons/backarrow.svg?react'
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

const SearchPage = () => {

  const [search, setSearch] = useState('');

  
  const [list, setList] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}api/propose/list`)
      .then(res => res.json())
      .then(json => setList(json.list))
  }, [])

  return (
    <main className="flex flex-col relative max-w-screen">
      <header className='text-lg font-bold flex flex-row gap-1/2 items-center gap-2 px-4 py-2 border-b border-gray-600'>
        <Link to='/home'>
          <BackArrowIcon width={24} height={24} style={{ color: 'white' }} />
        </Link>
        <span className='text-xl montserrat font-normal absolute left-1/2 transform-[translateX(-50%)]'>Search Tag</span>
      </header>
      <section className='px-2 flex flex-col flex-1 pb-3 pt-2'>
        <Input value={search} placeholder='Search Tag or Address' className='border-2 h-[40px]' onChange={e => setSearch(e.target.value)}/>
        <div className='mt-4 flex flex-col'>
        {
          search !== '' && list ?
            list
              .filter(item => item.address.includes(search) || item.tag.includes(search))
              .map(props => <ProposalListItem {...props}/>)
            : null
        }
        </div>
      </section>
    </main>
  )
}

export default SearchPage;