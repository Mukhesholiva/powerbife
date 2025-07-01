import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './LoginPage';
import PowerBIEmbed from './PowerBIEmbed';

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [role, setRole] = useState("");
  const [username, setUsername] = useState(""); // add username

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <LoginPage
              setLoggedIn={setLoggedIn}
              setRole={setRole}
              setUsername={setUsername}
            />
          }
        />
        <Route
          path="/powerbi"
          element={
            loggedIn ? (
              <PowerBIEmbed role={role} username={username} />
            ) : (
              <LoginPage
                setLoggedIn={setLoggedIn}
                setRole={setRole}
                setUsername={setUsername}
              />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
