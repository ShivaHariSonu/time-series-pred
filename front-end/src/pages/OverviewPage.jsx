import React, { useState } from 'react'
import Header from '../components/common/Header'
import {motion} from "framer-motion"
import StatCard from '../components/common/StatCard'
import { Baby, BarChart, BarChart2, Hospital, MapPin, Users, Zap } from 'lucide-react'
import CovidOverviewChart from '../components/overview/CovidOverviewChart'
import InfluenzaOverviewChart from '../components/overview/InfluenzaOverviewChart'
import RsvOverviewChart from '../components/overview/RsvOverviewChart'

const diseaseOptions = [
  { label: 'COVID-19', value: 'covid' },
  { label: 'Influenza', value: 'influenza' },
  { label: 'RSV', value: 'rsv' },
]


const OverviewPage = () => {
  const [selected, setSelected] = useState('covid');
  const renderChart = () => {
    switch (selected) {
      case 'influenza':
        return <InfluenzaOverviewChart />
      case 'rsv':
        return <RsvOverviewChart />
      default:
        return <CovidOverviewChart />
    }
  };

  return (
    <div className='flex-1 overflow-auto relative z-10'>
        <Header title="Overview"/>
        <main className='max-w-10xl mx-auto py-6 px-4 lg:px-8 xl:px-20'>
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
            <motion.div
              className='w-full mb-8'
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1}}
            >
            <select
              value={selected}
              onChange={e => setSelected(e.target.value)}
              className='w-full bg-gray-800 border border-gray-700 rounded-xl mt-1 text-1xl font-semibold text-gray-100 px-4 py-3 focus:outline-none'
            >
              {diseaseOptions.map(opt => (
                <option key={opt.value} value={opt.value} className='bg-gray-900 text-gray-100'>
                  {opt.label}
                </option>
              ))}
            </select>
            </motion.div>
            {/* <div className='w-full flex flex-col gap-5'>
              <CovidOverviewChart/>
              <InfluenzaOverviewChart/>
              <RsvOverviewChart/> */}

            <div className='w-full'>
              {renderChart()}
            </div>
        </main>

    </div>
  )
}

export default OverviewPage