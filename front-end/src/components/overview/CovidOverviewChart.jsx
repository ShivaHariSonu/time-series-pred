const CovidOverviewChart = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  const iframeUrl = `${baseUrl}/covid-admissions/`;
  return (
    <main className='max-w-10xl py-6 px-4 lg:px-8 xl:px-20 bg-white'>

      <div className="h-[800px] w-full">
        <iframe
          src={iframeUrl}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: '8px'
          }}
          title="COVID Admissions Dashboard"
        />
      </div>
    </main>
  );
};

export default CovidOverviewChart;