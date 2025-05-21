const CovidMapChart = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  const iframeUrl = `${baseUrl}/covid-map-view/`;
  return (
    <main className='max-w-10xl py-6 px-4 lg:px-8 xl:px-20 bg-white'>
      {/* <h2 className="text-lg font-medium mb-4 text-red-800">
        COVID Map
      </h2> */}
      <div className="h-[850px] w-full">
        <iframe
          src={iframeUrl}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: '8px'
          }}
          title="COVID Map"
        />
      </div>
    </main>
  );
};

export default CovidMapChart;