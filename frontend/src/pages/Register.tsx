import React, { useState } from 'react';
import { apiClient } from '../utils/api-simple';
import { getApiBaseUrl } from '../utils/getApiBaseUrl';

interface RegisterProps {
  onRegister: (user: any) => void;
  onLogin: () => void;
  onHome: () => void;
}

const Register: React.FC<RegisterProps> = ({ onRegister, onLogin, onHome }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Register user
      const registerResponse = await apiClient.post('/api/v1/auth/register', {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name
      });

      // Auto-login after registration
      const loginFormData = new FormData();
      loginFormData.append('username', formData.email);
      loginFormData.append('password', formData.password);

      const loginResponse = await fetch(`${getApiBaseUrl()}/api/v1/auth/login`, {
        method: 'POST',
        body: loginFormData,
      });

      const loginData = await loginResponse.json();
      
      // Store tokens
      apiClient.setTokens({
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
        token_type: loginData.token_type || 'bearer',
        expires_in: loginData.expires_in || 3600
      });

      onRegister(loginData.user);
      
    } catch (err: any) {
      let errorMessage = 'Registration failed';
      
      // Handle different error response formats
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message;
          if (detail.requirements && Array.isArray(detail.requirements)) {
            errorMessage += ': ' + detail.requirements.join(', ');
          }
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      } else if (err.detail) {
        if (typeof err.detail === 'object' && err.detail.message) {
          errorMessage = err.detail.message;
          if (err.detail.requirements && Array.isArray(err.detail.requirements)) {
            errorMessage += ': ' + err.detail.requirements.join(', ');
          }
        } else if (typeof err.detail === 'string') {
          errorMessage = err.detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      // If it's password validation, add helpful requirements
      if (errorMessage.includes('password') && errorMessage.includes('security')) {
        errorMessage = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character (!@#$%^&*)';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-md p-8 border border-gray-700">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-600 mb-2">🏦 WealthPath AI</h1>
          <h2 className="text-xl font-semibold text-gray-800">Create Account</h2>
          <p className="text-gray-600">Start your financial journey</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">First Name</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">Last Name</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Must be 8+ characters with uppercase, lowercase, number, and special character
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-medium mb-2">Confirm Password</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button onClick={onLogin} className="text-blue-600 hover:text-blue-800 font-semibold">
              Sign in
            </button>
          </p>
          {/* Force navigation to landing page */}
          <button 
            onClick={onHome}
            className="mt-4 text-gray-500 hover:text-gray-700 inline-block bg-transparent border-none cursor-pointer"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  );
};

export default Register;