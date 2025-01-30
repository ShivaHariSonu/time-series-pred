import React from 'react'
import Header from '../components/common/Header'
import {motion} from "framer-motion"

const OverviewPage = () => {
  return (
    <div className='flex-1 overflow-auto relative z-10'>
        <Header title="Overview"/>
        <main className='max-w-7xl mx-auto py-6 px-4 lg:px-8 xl:px-20'>
            <motion.div>
            
            </motion.div>

        </main>

    </div>
  )
}

export default OverviewPage