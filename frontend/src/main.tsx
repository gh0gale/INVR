import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { apiUrl } from './api'
import './index.css'

// Wake the backend while the visitor is still reading or picking a ticker.
// The free host sleeps after 15 idle minutes and takes ~50s to start; by the
// time an analysis is submitted it is usually awake (deployment_plan.md §2.4).
// Nothing waits on this, so a slow or failed ping costs nothing.
void fetch(apiUrl('/health')).catch(() => undefined)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)