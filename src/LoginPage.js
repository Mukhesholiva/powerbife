import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import './LoginPage.css';

function LoginPage({ setLoggedIn, setUsername, setRole }) {
  const [inputUsername, setInputUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    setIsLoading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await axios.post("https://dev-oneoliva.olivaclinic.com/backend/login", {
        username: inputUsername,
        password,
      });

      if (response.data && response.data.user?.username && response.data.user?.role) {
        setUsername(response.data.user.username);
        setRole(response.data.user.role);
        setLoggedIn(true);
        setSuccessMessage("Login successful! Redirecting...");

        setTimeout(() => {
          navigate("/powerbi");
        }, 1500);
      } else {
        setErrorMessage("Login failed. Missing username or role.");
      }
    } catch (error) {
      setErrorMessage("Invalid credentials.");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="logo-container">
          <img 
            src="/image.jpeg" 
            alt="Oliva Skin and Hair Clinic" 
            className="logo-image"
          />
        </div>
        <div className="form-container">
          <label htmlFor="username" className="input-label">Username</label>
          <input
            id="username"
            type="text"
            value={inputUsername}
            onChange={(e) => setInputUsername(e.target.value)}
            required
            className="login-input"
            placeholder="Enter your username"
          />

          <label htmlFor="password" className="input-label">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
            placeholder="Enter your password"
          />

          {errorMessage && <p className="error-text">{errorMessage}</p>}
          {successMessage && <p className="success-text">{successMessage}</p>}

          <button
            onClick={handleLogin}
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
