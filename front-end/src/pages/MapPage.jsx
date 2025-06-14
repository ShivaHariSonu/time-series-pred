import CovidMapChart from '../components/overview/CovidMapChart';

const MapPage = () => {
  return (
    <main className='max-w-10xl mx-auto py-6 px-4 lg:px-8 xl:px-20 bg-white'>
      <div className='w-full'>
        <CovidMapChart />
      </div>
    </main>
  );
};

export default MapPage;