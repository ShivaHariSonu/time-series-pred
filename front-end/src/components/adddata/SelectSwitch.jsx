import React from 'react'

const SelectSwitch = ({label,options, value, onChange}) => {
  return (
    <div className="flex items-center justify-between py-3">
      <label className="text-gray-300">{label}</label>
      <select
        value={value}
        onChange={onChange}
        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded transition duration-200 w-72 flex-shrink-0"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  )
}

export default SelectSwitch