import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import NewProject from './pages/NewProject'
import ProjectDetail from './pages/ProjectDetail'

import Navbar from './components/Navbar'

const queryClient = new QueryClient();

function App() {
  // Simple auth state for demo purposes. 
  // Normally this would be in a Context/Store.
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  const handleLoginSuccess = async (credentialResponse: any) => {
    try {
      const res = await fetch(import.meta.env.VITE_API_URL + '/auth/google-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken: credentialResponse.credential })
      });
      
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
      } else {
        alert("Login failed on server.");
      }
    } catch (e) {
      console.error(e);
      alert("Error reaching backend.");
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full">
            <div className="flex justify-center mb-4">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-xl shadow-blue-500/30">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
              </div>
            </div>
            <h1 className="text-3xl font-bold mb-3 text-gray-800">Antigravity 3D</h1>
            <p className="text-gray-500 mb-8 font-medium">Sign in to orchestrate your autonomous CAD agent.</p>
            <div className="flex justify-center">
                <GoogleLogin
                onSuccess={handleLoginSuccess}
                onError={() => console.log('Login Failed')}
                />
            </div>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50/50">
          <Navbar onLogout={logout} />
          <main className="py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewProject />} />
              <Route path="/project/:id" element={<ProjectDetail />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
