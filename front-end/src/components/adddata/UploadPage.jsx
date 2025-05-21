import { useState } from 'react';
import axios from 'axios';

const diseaseOptions = [
  { label: 'COVID-19', value: 'covid' },
  { label: 'Influenza', value: 'influenza' },
  { label: 'RSV', value: 'rsv' },
];

const UploadPage = () => {
  const [selectedDisease, setSelectedDisease] = useState('');
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleDiseaseChange = (e) => {
    setSelectedDisease(e.target.value);
    setUploadSuccess(false);
    setError('');
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadSuccess(false);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedDisease || !file) {
      setError('Please select both a disease and a file');
      return;
    }

    const formData = new FormData();
    formData.append('disease_type', selectedDisease);
    formData.append('file', file);

    try {
      setIsUploading(true);
      setError('');
      setUploadSuccess(false);
      setUploadProgress(0);
      const apiUrl = 'http://localhost:8000/upload-data/';
      
      await axios.post(apiUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          let stepsCompleted = 0;
          const totalProcessingSteps = 16;
          const percentCompleted = setInterval(() => {
            stepsCompleted++;
            const newProgress = 20 + Math.min(stepsCompleted, 60);
            setUploadProgress(newProgress);
          },5000);
        },
      });
    setUploadProgress(100);
    setUploadSuccess(true);
    setFile(null);

    } catch (err) {
      if (err.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorMessage = err.response.data?.error || 
                         err.response.data?.message || 
                         err.response.statusText;
      setError(errorMessage);

      } else if (err.request) {
        // The request was made but no response was received
        setError('No response from server. Please check your connection.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setError(err.message || 'Error uploading file. Please try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className='max-w-10xl py-6 px-4 lg:px-8 xl:px-20 bg-white'>
      <div className='max-w-4xl mx-auto'>
        <h2 className='text-3xl font-semibold text-red-800 mb-4'>Data Upload</h2>
        <p className='text-gray-800 mb-6'>
          Upload your CSV data file for COVID-19, Influenza, or RSV. Select the disease type and choose your file below.
        </p>

        <div className='flex flex-col gap-4 mb-6'>
          <select
            value={selectedDisease}
            onChange={handleDiseaseChange}
            className='bg-white border border-red-700 rounded-md px-4 py-2 text-red-800 focus:outline-none focus:ring-2 focus:ring-red-700'
          >
            <option value=''>Select Disease</option>
            {diseaseOptions.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <div className='flex items-center gap-4'>
            <label className='cursor-pointer bg-red-800 text-white px-4 py-2 rounded-md hover:bg-red-700'>
              Choose File
              <input
                type='file'
                accept='.csv'
                onChange={handleFileChange}
                className='hidden'
              />
            </label>
            <span className='text-gray-600'>
              {file ? file.name : 'No file chosen'}
            </span>
          </div>

          {error && <p className='text-red-600'>{error}</p>}

          {isUploading && (
            <div className="w-full mt-4">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-red-800">
                  {uploadProgress < 20 ? 'Uploading...' : 'Training models...'} {uploadProgress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 relative">
                <div 
                  className="bg-red-600 h-2.5 rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
                {uploadProgress >= 20 && uploadProgress < 100 && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="animate-pulse text-xs text-white">
                      Training models...
                    </div>
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {uploadProgress < 20 
                  ? `Uploading your file (${Math.round(file.size * uploadProgress / 20 / 1024)}/${Math.round(file.size / 1024)} KB)`
                  : 'Training models and running predictions'}
              </div>
            </div>
          )}

          {uploadSuccess && (
            <p className='text-green-600'>File uploaded successfully!</p>
          )}

          <button
            onClick={handleUpload}
            disabled={isUploading || !selectedDisease || !file}
            className={`bg-red-800 text-white px-4 py-2 rounded-md hover:bg-red-700 ${
              (isUploading || !selectedDisease || !file) ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isUploading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>

        <hr className='border-t border-gray-300 mb-6' />

        <section className='mt-8'>
          <h3 className='text-3xl font-semibold text-red-800 mb-4'>CSV Format Requirements</h3>
          <ul className='list-disc list-inside text-gray-700 space-y-2'>
            <li>File must be in CSV format with UTF-8 encoding</li>
            <li>Required columns: EMPI, ADMIT_DTS, ORGANIZATION_NM, CHILDRENS_HOSPITAL</li>
            <li>Date format: YYYY-MM-DD or YYYY-MM-DD hh:mm:ss</li>
            <li>Maximum file size: 10MB</li>
            <li>First row should be header row</li>
          </ul>
        </section>
      </div>
    </main>
  );
};

export default UploadPage;