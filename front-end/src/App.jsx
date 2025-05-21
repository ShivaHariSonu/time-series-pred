import { Route, Routes } from "react-router-dom";
import OverviewPage from "./pages/OverviewPage";
import MapPage from "./pages/MapPage";
import CovidPage from "./pages/CovidPage";
import InfluenzaPage from "./pages/InfluenzaPage";
import RsvPage from "./pages/RsvPage";
import AddDataPage from "./pages/AddDataPage";
import TitleBar from "./components/common/TitleBar";

function App() {
  return (
    <div className='flex flex-col h-screen bg-white'>
      <TitleBar />
      <div className='flex-1 overflow-auto'>
        <Routes>
          <Route path='/' element={<OverviewPage />} />
          <Route path='/map' element={<MapPage />} />
          <Route path='/covid' element={<CovidPage />} />
          <Route path='/influenza' element={<InfluenzaPage />} />
          <Route path='/rsv' element={<RsvPage />} />
          <Route path='/add-data' element={<AddDataPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;