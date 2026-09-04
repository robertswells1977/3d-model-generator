import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import './App.css'

function App() {
  const [token, setToken] = useState<string | null>(null);

  const handleLoginSuccess = async (credentialResponse: any) => {
    try {
      const res = await fetch(import.meta.env.VITE_API_URL + '/auth/google-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken: credentialResponse.credential })
      });
      
      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        alert(`Login successful! Welcome ${data.user.name}`);
      } else {
        alert("Login failed on server.");
      }
    } catch (e) {
      console.error(e);
      alert("Error reaching backend.");
    }
  };

  return (
    <div className="App">
      <h1>3D Model Generator</h1>
      {!token ? (
        <div style={{ marginTop: '2rem' }}>
          <p>Please log in to continue:</p>
          <GoogleLogin
            onSuccess={handleLoginSuccess}
            onError={() => {
              console.log('Login Failed');
            }}
          />
        </div>
      ) : (
        <div style={{ marginTop: '2rem' }}>
          <h2>You are logged in!</h2>
          <p>JWT Token received. Ready for Phase 3!</p>
        </div>
      )}
    </div>
  )
}

export default App
