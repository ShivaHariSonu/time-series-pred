import CovidOverviewChart from '../components/overview/CovidOverviewChart';

const CovidPage = () => {
  return (
    <main className='max-w-10xl mx-auto py-6 px-4 lg:px-8 xl:px-20 bg-white'>
      <div className='w-full'>
        <CovidOverviewChart />
      </div>
    </main>
  );
};

export default CovidPage;