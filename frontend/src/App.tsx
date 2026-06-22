import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Workspace from './pages/Workspace';
import Auth from './pages/Auth';


function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/workspace" element={<Workspace />} />
      <Route path="/auth" element={<Auth />} />

    </Routes>
  );
}

export default App;