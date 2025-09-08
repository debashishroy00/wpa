import React, { useState, useEffect } from 'react'
import './App.css'

// Simple component interfaces for type safety
interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
}

function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'login' | 'register' | 'dashboard'>('landing')
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check for existing auth on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
        setCurrentView('dashboard')
      } catch (e) {
        localStorage.removeItem('user')
      }
    }
  }, [])

  const handleLogin = async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    
    try {
      // Simulate API call - replace with actual API
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const userData = {
        id: '1',
        email,
        firstName: email.split('@')[0]
      }
      
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
      setCurrentView('dashboard')
    } catch (err) {
      setError('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('user')
    setCurrentView('landing')
  }

  // Landing Page Component
  if (currentView === 'landing') {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="container mx-auto px-4 py-16">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              🏦 WealthPath AI
            </h1>
            <p className="text-xl text-gray-300">Intelligent Financial Planning Platform</p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-2">✅ AI-Powered Analysis</h3>
              <p className="text-gray-300">Smart financial insights powered by advanced AI</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-2">✅ Complete Planning</h3>
              <p className="text-gray-300">Full financial planning from goals to execution</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-2">✅ Real-time Updates</h3>
              <p className="text-gray-300">Live market data and portfolio tracking</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="text-center space-x-4">
            <button
              onClick={() => setCurrentView('login')}
              className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all transform hover:-translate-y-1 shadow-lg"
            >
              🔐 Login to WealthPath AI
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className="px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white text-lg rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:-translate-y-1 shadow-lg"
            >
              ✨ Create Account
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Login Component
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold mb-2">🏦 WealthPath AI</h1>
            <h2 className="text-xl font-semibold">Welcome Back</h2>
            <p className="text-gray-300">Sign in to your account</p>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault()
            const formData = new FormData(e.currentTarget)
            const email = formData.get('email') as string
            const password = formData.get('password') as string
            handleLogin(email, password)
          }}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  name="email"
                  type="email"
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Password</label>
                <input
                  name="password"
                  type="password"
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-900 border border-red-700 rounded-lg">
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-6 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-gray-300">
              Don't have an account?{' '}
              <button
                onClick={() => setCurrentView('register')}
                className="text-purple-400 hover:text-purple-300 font-medium"
              >
                Create one
              </button>
            </p>
            <button
              onClick={() => setCurrentView('landing')}
              className="text-purple-400 hover:text-purple-300 text-sm"
            >
              ← Back to Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Register Component
  if (currentView === 'register') {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold mb-2">🏦 WealthPath AI</h1>
            <h2 className="text-xl font-semibold">Create Account</h2>
            <p className="text-gray-300">Start your financial journey</p>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault()
            const formData = new FormData(e.currentTarget)
            const email = formData.get('email') as string
            const password = formData.get('password') as string
            handleLogin(email, password) // For now, same as login
          }}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">First Name</label>
                  <input
                    name="firstName"
                    type="text"
                    required
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Last Name</label>
                  <input
                    name="lastName"
                    type="text"
                    required
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  name="email"
                  type="email"
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Password</label>
                <input
                  name="password"
                  type="password"
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <p className="text-xs text-gray-400 mt-1">Must be 8+ characters with uppercase, lowercase, number, and special character</p>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-900 border border-red-700 rounded-lg">
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-6 px-4 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-gray-300">
              Already have an account?{' '}
              <button
                onClick={() => setCurrentView('login')}
                className="text-purple-400 hover:text-purple-300 font-medium"
              >
                Sign in
              </button>
            </p>
            <button
              onClick={() => setCurrentView('landing')}
              className="text-purple-400 hover:text-purple-300 text-sm"
            >
              ← Back to Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Dashboard Component
  if (currentView === 'dashboard') {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="container mx-auto px-4 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold">🏦 WealthPath AI</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-300">Welcome, {user?.firstName || user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Dashboard Coming Soon</h2>
            <p className="text-gray-300 text-lg">Your personalized financial planning dashboard is being built.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-xl font-semibold mb-2">📊 Portfolio Overview</h3>
              <p className="text-gray-300">Track your investments and performance</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-xl font-semibold mb-2">🎯 Financial Goals</h3>
              <p className="text-gray-300">Set and monitor your financial objectives</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-xl font-semibold mb-2">🤖 AI Insights</h3>
              <p className="text-gray-300">Personalized recommendations from AI</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return null
}

export default App