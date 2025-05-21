import {Database, HomeIcon} from 'lucide-react';
import { motion} from 'framer-motion'
import { NavLink } from 'react-router-dom';

const TITLEBAR_ITEMS = [
    {name:"Overview", icon:HomeIcon, color:"#F0F0F0", path:"/"},
    {name:"Add data",icon:Database,color:"#F0F0F0", path:"/add-data"}
]

const TitleBar = () => {
  return (
    <header className='bg-red-800 shadow-lg'>
      <div className='max-w-7xl py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center'>
        <h1 className='text-2xl font-light text-white mr-8'>UHealth Forecast Hub</h1>
        <nav className='flex items-center gap-4 flex-1'>
          {TITLEBAR_ITEMS.map((item) => (
            <NavLink 
              key={item.path} 
              to={item.path}
              className={({ isActive }) => 
                `flex items-center text-white hover:opacity-80 transition-opacity ${
                  isActive ? 'font-medium' : 'font-normal'
                }`
              }
            >
              <item.icon size={20} style={{ color: item.color, minWidth: "20px" }} />
              <motion.span
                className='ml-2 whitespace-nowrap'
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2, delay: 0.3 }}
              >
                {item.name}
              </motion.span>
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default TitleBar;