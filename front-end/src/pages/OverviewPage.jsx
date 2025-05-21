import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const chartOptions = [
  { label: 'COVID Admissions & Forecast', value: 'covid' },
  { label: 'COVID Map', value: 'covidmap' },
  { label: 'Influenza Admissions & Forecast', value: 'influenza' },
  { label: 'RSV Admissions & Forecast', value: 'rsv' },
];

const OverviewPage = () => {
  const [selected, setSelected] = useState('covid');
  const navigate = useNavigate();

  const handleViewForecast = () => {
    if (selected === 'covidmap') {
      navigate('/map');
    } else {
      navigate(`/${selected}`);
    }
  };

  return (
    <main className='max-w-10xl py-6 px-4 lg:px-8 xl:px-20 bg-white'>

      <div className='max-w-4xl mx-auto'>

        <h2 className='text-3xl font-semibold text-red-800 mb-4'>UHealth Forecast Hub</h2>
        <p className='text-gray-800 mb-6'>
          This application provides forecasts for COVID-19, Influenza, and RSV admissions, as well as a COVID Map. Select an option below and click "View Forecast" to see the chart.
        </p>
        <div className='flex justify-center items-center gap-4 mb-16'>
          <select
            value={selected}
            onChange={e => setSelected(e.target.value)}
            className='bg-white border border-red-700 rounded-md px-4 py-2 text-red-800 focus:outline-none focus:ring-2 focus:ring-red-700'
          >
            {chartOptions.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleViewForecast}
            className='bg-red-800 text-white px-4 py-2 rounded-md hover:bg-red-700'
          >
            View Forecast
          </button>
        </div>
        <hr className='border-t border-gray-300 mb-6' />
        <section className='mt-8'>
        <h3 className='text-3xl font-semibold text-red-800 mb-4'>Models Included</h3>
        <ul className='list-disc list-inside text-gray-700 space-y-2'>
          <li><strong>chronos-pred</strong>: <a href='https://github.com/amazon-science/chronos-forecasting' target="_blank" className="text-red-800 hover:text-red-700 font-medium">Chronos</a> is a family of pretrained time series forecasting models based on language model architectures. A time series is transformed into a sequence of tokens via scaling and quantization, and a language model is trained on these tokens using the cross-entropy loss.</li>
          <li><strong>arima-pred</strong>: <a href='https://unit8co.github.io/darts/generated_api/darts.models.forecasting.arima.html' target="_blank"  className="text-red-800 hover:text-red-700 font-medium">ARIMA </a> (AutoRegressive Integrated Moving Average) is a statistical time series model that combines autoregression, differencing (to make data stationary), and moving averages to forecast future values.</li>
          <li><strong>transformer-pred</strong>: <a href='https://unit8co.github.io/darts/generated_api/darts.models.forecasting.tft_model.html#darts.models.forecasting.tft_model.TFTModel' target="_blank" className="text-red-800 hover:text-red-700 font-medium">Temporal Fusion Transformer</a> is a deep learning model designed for interpretable multi-horizon time series forecasting, combining attention mechanisms with recurrent layers to capture both long- and short-term temporal patterns. It also handles static and time-varying inputs, enabling dynamic feature selection and quantile predictions.</li>
          <li><strong>xgb-pred</strong>: <a href='https://unit8co.github.io/darts/generated_api/darts.models.forecasting.xgboost.html' target="_blank" className="text-red-800 hover:text-red-700 font-medium">XGBoost</a> is a gradient boosting framework that builds additive decision tree models in a forward stage-wise manner using second-order Taylor approximation for optimized loss minimization and regularization.</li>
          <li><strong>conformal-naive-pred</strong>: <a href="https://unit8co.github.io/darts/generated_api/darts.models.forecasting.baselines.html" target="_blank" className="text-red-800 hover:text-red-700 font-medium">Naive Seasonal</a> model in Darts forecasts future values by repeating the last observed seasonal cycle, assuming the seasonality pattern remains unchanged.</li>
        </ul>
      </section>
      </div>
    </main>
  );
};

export default OverviewPage;