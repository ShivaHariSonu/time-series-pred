import React from 'react'
import Header from '../components/common/Header'
import Data from '../components/adddata/Data'

function AddDataPage() {
  return (
    <div className='flex-1 overflow-auto relative z-10 bg-gray-900'>
        <Header title="Add Data"/>
        <main className='max-w-4xl mx-auto py-6 px-4 lg:px-8'>
            <Data/>
        </main>
    </div>
  )
}

export default AddDataPage