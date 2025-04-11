import React from 'react'

const TextField = ({ label, value, onChange, placeholder = "", type = "text" }) => {
  return (
    <div className="flex items-center justify-between py-3">
      <label className="text-gray-300">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        step="1"
        className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition duration-200 w-72 flex-shrink-0"
      />
    </div>
  )
}

export default TextField;