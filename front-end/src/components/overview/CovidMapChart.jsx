import { motion } from "framer-motion";
import React from 'react';

const CovidMapChart = () => {
  return (
    <motion.div 
      className="bg-gray-800 bg-opacity-50 backdrop-blur-md shadow-lg rounded-xl p-6 border border-gray-700"
      initial={{opacity:0,y:20}}
      animate={{opacity:1,y:0}}
      transition={{delay:0.2}}>
      
      <h2 className="text-lg font-medium mb-4 text-gray-100">
        COVID Map
      </h2>

      <div className="h-[850px] w-full">
        <iframe
          src="http://localhost:8000/covid-map-view/"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: '8px'
          }}
          title="COVID Map"
        />
      </div>
    </motion.div>
  )
}

export default CovidMapChart;