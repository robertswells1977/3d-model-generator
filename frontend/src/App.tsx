import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import NewProject from './pages/NewProject'
import ProjectDetail from './pages/ProjectDetail'

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
            <h1 className="text-3xl font-bold mb-6 text-gray-800">3D Model Generator</h1>
            <p className="text-gray-600 mb-8">Sign in with Google to manage your autonomous CAD agent.</p>
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
        <nav className="bg-white shadow-sm border-b px-6 py-4 flex justify-between items-center">
            <div className="font-bold text-xl text-blue-600">3D CAD Agent</div>
            <button onClick={logout} className="text-gray-500 hover:text-gray-800 text-sm font-medium">Logout</button>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewProject />} />
          <Route path="/project/:id" element={<ProjectDetail />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
