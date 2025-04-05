// components/PageWrapper.tsx
import { motion } from 'framer-motion'

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
      {children}
    </motion.div>
  )
}
