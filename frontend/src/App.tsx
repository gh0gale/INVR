import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Workspace from './pages/Working';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/workspace" element={<Workspace />} />
    </Routes>
  );
}

export default App;