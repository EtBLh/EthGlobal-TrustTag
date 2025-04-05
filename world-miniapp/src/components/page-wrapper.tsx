import { motion } from 'framer-motion'
import Propose from '@/icons/propose.svg?react'
import Search from '@/icons/search.svg?react'
import Home from '@/icons/home.svg?react'
import Reward from '@/icons/rewards.svg?react'
import { Link } from 'react-router'

const variants = {
    ltr: {
        initial: { x: '100%', opacity: 0 },
        animate: { x: 0, opacity: 1, transition: { duration: 0.1, ease: 'easeInOut' } },
        exit: { x: '-100%', opacity: 0, transition: { duration: 0.1, ease: 'easeInOut' } },
    },
    rtl: {
        initial: { x: '-100%', opacity: 0 },
        animate: { x: 0, opacity: 1, transition: { duration: 0.4, ease: 'easeInOut' } },
        exit: { x: '100%', opacity: 0, transition: { duration: 0.4, ease: 'easeInOut' } },
    }
}

interface props extends React.PropsWithChildren {
    variant: keyof typeof variants
}

export default function PageWrapper({ variant, children }: props) {
  return (
    <motion.div
      variants={variants[variant]}
      initial="initial"
      animate="animate"
      exit="exit"
      style={{ position: 'absolute', width: '100%' }}
    >
      <div className='flex flex-col justify-between h-screen'>
      {children}
      <nav className='border-t-2 p-2 flex flex-row h-[54px] justify-between px-[64px] items-center'>
        <Link to='/search'>
            <Search className='text-indigo-200'/>
        </Link>
        <Link to='/home'>
            <Home className='text-indigo-200'/>
        </Link>
        <Link to='/propose'>
            <Propose className='text-indigo-200'/>
        </Link>
        <Link to='/claim'>
            <Reward className='text-indigo-200'/>
        </Link>
      </nav>
      </div>
    </motion.div>
  )
}
