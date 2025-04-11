import React from 'react'
import Header from '../components/common/Header'
import {motion} from "framer-motion"
import StatCard from '../components/common/StatCard'
import { Baby, BarChart, BarChart2, Hospital, MapPin, Users, Zap } from 'lucide-react'
import CovidOverviewChart from '../components/overview/CovidOverviewChart'
import InfluenzaOverviewChart from '../components/overview/InfluenzaOverviewChart'
import RsvOverviewChart from '../components/overview/RsvOverviewChart'

const OverviewPage = () => {
  return (
    <div className='flex-1 overflow-auto relative z-10'>
        <Header title="Overview"/>
        <main className='max-w-7xl mx-auto py-6 px-4 lg:px-8 xl:px-20'>
            <motion.div
            className='grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8'
            initial={{opacity:0,y:20}}
            animate={{opacity:1,y:0}}
            transition={{duration:1}}>
            <StatCard name="Hospital Count" icon={Hospital} value='15' color='#6366F1'/>
            <StatCard name="Childrens Hospital" icon={Baby} value='2' color='#8B5CF6'/>
            <StatCard name="No. of Diseases" icon={BarChart} value='3' color='#EC4899'/>
            <StatCard name="State" icon={MapPin} value='Utah' color='#10B981'/>
            </motion.div>
            <div className='w-full flex flex-col gap-5'>
              <CovidOverviewChart/>
              <InfluenzaOverviewChart/>
              <RsvOverviewChart/>
            </div>

        </main>

    </div>
  )
}

export default OverviewPage