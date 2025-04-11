import React, { useState } from 'react'
import AddDataSection from './AddDataSection'
import { FileText } from 'lucide-react'
import ToggleSwitch from './ToggleSwitch'
import SelectSwitch from './SelectSwitch'
import TextField from './TextField'

const Data = () => {
    const [toggleData, setToggleData] = useState({
            children: false,
            icuflag: false
    })
    const hospitals = ['Primary Childrens Hospital', 'McKay-Dee Hospital',
        'McKay-Dee Behavioral Health',
        'Primary Childrens Behavioral Health', 'Utah Valley Hospital',
        'American Fork Hospital', 'Intermountain Medical Center',
        'St George Regional Hospital', 'Cedar City Hospital',
        'Logan Regional Hospital', 'Garfield Memorial Hospital',
        'Riverton Hospital', 'LDS Hospital', 'Cassia Regional Hospital',
        'Park City Hospital', 'Sanpete Valley Hospital',
        'Alta View Hospital', 'Bear River Valley Hospital',
        'Layton Hospital', 'Delta Community Hospital',
        'Spanish Fork Hospital', 'Sevier Valley Hospital',
        'Fillmore Community Hospital',
        'Primary Childrens Hospital Lehi - Miller Campus',
        'Heber Valley Hospital',
        'Primary Childrens Lehi Behavioral Health - Miller Campus']

    const [hospital, setHospital] = useState(hospitals[0]);

    const regions = ['North Region', 'Primary Childrens Hospital', 'Central Region',
        'South Region', 'Rural', 'Southwest Region', 'Riverton']
    const [region,setRegion] = useState(regions[0]);

    const measurements = ['covid','influenza','rsv']
    const [measurement,setMeasurement] = useState(measurements[0]);

    const [reasonforvisit, setReasonForVisit] = useState("");
    const [nurseunitdsp, setNurseUnitDSP] = useState("");
    const [empi,setEMPI] = useState("");
    const [ageyearsno,setAgeYearsNo] = useState("");
    const [agedays,setAgeDays] = useState("");
    const [timestamp,setTimestamp] = useState("");

    const handleSubmit = async () => {
        const payload = {
          toggleData,
          hospital,
          region,
          measurement,
          reasonforvisit,
          nurseunitdsp,
          empi,
          ageyearsno: Number(ageyearsno),
          agedays: Number(agedays),
          timestamp,
        };
    
        try {
          const response = await fetch("http://localhost:8000/ingest-one-record/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          });
    
          if (!response.ok) throw new Error("Failed to submit");
    
          const result = await response.json();
          console.log("Submitted successfully:", result);
          alert("Success!");
        } catch (error) {
          console.error("Error submitting:", error);
          alert("Something went wrong.");
        }
      };


  return (
    <AddDataSection icon={FileText} title={"Data"}>
        <ToggleSwitch
				label={"Children's Hospital"}
				isOn={toggleData.children}
				onToggle={() => setToggleData({ ...toggleData, children: !toggleData.children})}
		/>
        <ToggleSwitch
            label={"ICU Flag"}
            isOn={toggleData.icuflag}
            onToggle={() => setToggleData({ ...toggleData, icuflag: !toggleData.icuflag})}
        />
        <SelectSwitch
          label="ORGANIZATION_NM"
          options={hospitals}
          value={hospital}
          onChange={(e) => setHospital(e.target.value)}
        />
        <SelectSwitch
          label="REGION"
          options={regions}
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        />
        <SelectSwitch
          label="MEASUREMENT"
          options={measurements}
          value={measurement}
          onChange={(e) => setMeasurement(e.target.value)}
        />
        <TextField
            label="REASON_FOR_VISIT"
            value={reasonforvisit}
            onChange={(e) => setReasonForVisit(e.target.value)}
            placeholder=""
        />
        <TextField
            label="NURSE_UNIT_DSP"
            value={nurseunitdsp}
            onChange={(e) => setNurseUnitDSP(e.target.value)}
            placeholder=""
        />
        <TextField
            label="EMPI"
            value={empi}
            onChange={(e) => setEMPI(e.target.value)}
            placeholder=""
        />
        <TextField
            label="AGE_YEARS_NO"
            value={ageyearsno}
            onChange={(e) => setAgeYearsNo(e.target.value)}
            placeholder=""
            type="number"
        />
        <TextField
            label="AGE_DAYS"
            value={agedays}
            onChange={(e) => setAgeDays(e.target.value)}
            placeholder=""
            type="number"
        />
        <TextField
            label="Timestamp"
            value={timestamp}
            onChange={(e) => setTimestamp(e.target.value)}
            type="datetime-local"
        />
        <div className='mt-4'>
            <button
                onClick={handleSubmit}
                className='bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded transition duration-200'
            >
                Submit
            </button>
		</div>

    </AddDataSection>
  )
}

export default Data