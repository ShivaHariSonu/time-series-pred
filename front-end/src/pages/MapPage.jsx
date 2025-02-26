import React from 'react'
import CovidMapChart from '../components/overview/CovidMapChart'
import Header from '../components/common/Header'

const MapPage = () => {
  return (
    <div className='flex-1 overflow-auto relative z-10'>
        <Header title="Maps"/>
        <main className='max-w-7xl mx-auto py-6 px-4 lg:px-8 xl:px-20'>
            <div className='w-full'>
              <CovidMapChart/>
            </div>

        </main>

    </div>
  )
}

export default MapPage