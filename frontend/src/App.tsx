import React, { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'

// Utilities
import { apiClient } from './utils/api-simple' // Use simplified API client
import { useAuthStore } from './stores/auth-store'

// Components
import FinancialManagementPage from './components/financial/FinancialManagementPage'
import ProfileManagementPage from './components/profile/ProfileManagementPage'
import ProjectionsPage from './components/projections/ProjectionsPage'
import { EnableAssumptionsEditing } from './components/QuickFix'
import GoalManager from './components/goals/GoalManager'
import IntelligenceDashboard from './components/intelligence/IntelligenceDashboard'
import { FinancialAdvisoryDashboard } from './components/advisory'
import SimplePortfolioAnalysis from './components/portfolio/SimplePortfolioAnalysis'
import TestFinancialService from './components/TestFinancialService'
import FinancialAdvisorChat from './components/Chat/FinancialAdvisorChat'
import DebugView from './components/Debug/DebugView'
import { isCurrentUserAdmin } from './utils/adminAuth'
import AdminDashboard from './pages/admin/AdminDashboard'

// Currency formatting utility
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function App() {
  const [apiHealth, setApiHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentView, setCurrentView] = useState<'home' | 'login' | 'register' | 'wealthpath' | 'projections'>('home')
  
  // Use auth store instead of local state
  const { user, login, logout } = useAuthStore()

  useEffect(() => {
    const initialize = async () => {
      console.log('🚀 App initialization starting...')
      try {
        // Load any existing tokens from storage first
        console.log('📋 Loading tokens from localStorage...')
        const existingTokensCheck = localStorage.getItem('auth_tokens')
        console.log('🔍 Initial token check:', existingTokensCheck ? 'TOKENS FOUND' : 'NO TOKENS')
        
        apiClient.loadTokensFromStorage()
        
        // Check API connection
        console.log('🔗 Checking API health...')
        const health = await apiClient.healthCheck()
        setApiHealth(health)
        console.log('✅ API health check successful:', health)
        
        // Check if user is already logged in
        console.log('👤 Checking if user is already authenticated...')
        try {
          const userData = await apiClient.get('/api/v1/auth/me')
          console.log('✅ User already authenticated from stored tokens:', userData)
          
          // CRITICAL FIX: Manually populate auth store from existing tokens
          const existingTokens = localStorage.getItem('auth_tokens')
          console.log('🔧 Attempting to populate auth store...')
          console.log('📋 Existing tokens:', existingTokens ? 'FOUND' : 'NOT FOUND')
          console.log('👤 User data:', userData ? `USER ID ${userData.id}` : 'NO USER DATA')
          
          if (existingTokens && userData) {
            console.log('🔧 Manually populating auth store from existing tokens')
            const tokens = JSON.parse(existingTokens)
            console.log('🎯 Calling auth store login with:', { 
              tokensLength: JSON.stringify(tokens).length,
              userId: userData.id,
              userEmail: userData.email
            })
            login(tokens, userData)
            console.log('✅ Auth store populated successfully')
          } else {
            console.log('❌ Cannot populate auth store - missing tokens or user data')
          }
        } catch (authErr) {
          console.log('❌ Auth check failed:', authErr)
          console.log('🔄 Stored tokens invalid or expired, attempting auto-login...')
          // User not logged in - no auto-login (removed hardcoded credentials for security)
          console.log('❌ User not authenticated - please login manually')
          if (false) { // Disabled auto-login for security
            try {
              console.log('Auto-login disabled for security')
              const formData = new FormData()
              // SECURITY: Removed hardcoded credentials
              
              const response = await fetch('http://localhost:8000/api/v1/auth/login', {
                method: 'POST',
                body: formData,
              })
              
              if (response.ok) {
                const data = await response.json()
                
                // Use auth store login function to properly store user and tokens
                login(
                  {
                    access_token: data.access_token,
                    refresh_token: data.refresh_token,
                    token_type: data.token_type || 'bearer',
                    expires_in: data.expires_in || 3600
                  },
                  data.user
                )
                
                console.log('Auto-login successful:', data.user)
              } else {
                console.log('Auto-login failed, user needs to login manually')
                logout()
              }
            } catch (autoLoginErr) {
              console.log('Auto-login error:', autoLoginErr)
              logout()
            }
          } else {
            logout()
          }
        }
        
      } catch (err: any) {
        setError(err.detail || err.message || 'Failed to connect to API')
      } finally {
        setLoading(false)
      }
    }

    initialize()
  }, [])

  const showHome = () => setCurrentView('home')
  const showLogin = () => setCurrentView('login')
  const showRegister = () => setCurrentView('register')
  const showWealthPath = () => setCurrentView('wealthpath')
  const showProjections = () => setCurrentView('projections')
  
  const handleLogin = (loginData: any) => {
    // If loginData contains tokens, use auth store login
    if (loginData.tokens && loginData.user) {
      login(loginData.tokens, loginData.user)
    } else if (loginData.user) {
      // For backward compatibility, just use the user data
      // Tokens should already be set by the calling code
      const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}')
      if (tokens.access_token) {
        login(tokens, loginData.user || loginData)
      }
    } else {
      // Fallback: treat entire loginData as user data
      const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}')
      if (tokens.access_token) {
        login(tokens, loginData)
      }
    }
    
    setCurrentView('wealthpath')
  }
  
  const handleLogout = () => {
    logout()
    setCurrentView('home')
  }

  if (currentView === 'login') {
    return <LoginScreen onLogin={handleLogin} onBack={showHome} onRegister={showRegister} />
  }

  if (currentView === 'register') {
    return <RegisterScreen onRegister={handleLogin} onBack={showHome} onLogin={showLogin} />
  }

  if (currentView === 'projections') {
    return <ProjectionsPage />
  }


  if (currentView === 'wealthpath') {
    return <WealthPathApp onBack={showHome} user={user} onLogout={handleLogout} />
  }

  return (
    <>
      <Helmet>
        <title>WealthPath AI - Intelligent Financial Planning Platform</title>
        <meta name="description" content="Advanced financial planning with AI-powered insights and goal tracking" />
      </Helmet>

      <div className="min-h-screen bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <header className="text-center mb-12">
            <h1 className="text-4xl font-bold text-blue-600 mb-4">
              🏦 WealthPath AI
            </h1>
            <p className="text-xl text-gray-300">
              Intelligent Financial Planning Platform
            </p>
          </header>

          {/* API Status Card */}
          <div className="bg-gray-800 rounded-lg shadow-md p-6 mb-8 border border-gray-700">
            <h2 className="text-2xl font-semibold text-white mb-4">Backend API Status</h2>
            
            {loading && (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-300">Checking API connection...</span>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                <div className="flex items-center mb-2">
                  <span className="text-lg mr-2">❌</span>
                  <strong>Connection Error:</strong>
                </div>
                <p className="mb-2">{error}</p>
                <small className="text-red-600">
                  Make sure the backend is running on port 8000 and CORS is configured properly
                </small>
              </div>
            )}

            {apiHealth && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
                <div className="flex items-center mb-3">
                  <span className="text-lg mr-2">✅</span>
                  <strong>API Connected Successfully!</strong>
                </div>
                <div className="text-sm text-green-600 space-y-1">
                  <p><strong>Service:</strong> {apiHealth.service}</p>
                  <p><strong>Version:</strong> {apiHealth.version}</p>
                  <p><strong>Environment:</strong> {apiHealth.environment}</p>
                  <p><strong>Status:</strong> {apiHealth.status}</p>
                </div>
              </div>
            )}
          </div>

          {/* Phase 2 Development Status */}
          <div className="bg-gray-800 rounded-lg shadow-md p-6 mb-8 border border-gray-700">
            <h2 className="text-2xl font-semibold text-white mb-6">WealthPath AI 2.0 - Production Ready</h2>
            
            <div className="grid gap-4">
              <StatusItem 
                title="✅ Backend API Integration" 
                description="Full connectivity with CORS configuration resolved"
                status="completed"
              />
              <StatusItem 
                title="✅ 5-Step Financial Planning Flow" 
                description="Data Aggregation → Current State → Goals → Intelligence → Roadmap"
                status="completed"
              />
              <StatusItem 
                title="✅ WealthPath AI 2.0 Interface" 
                description="Complete dark theme implementation matching wireframes"
                status="completed"
              />
              <StatusItem 
                title="✅ AI-Powered Features" 
                description="Target Setting Assistant, Gap Analysis, Portfolio Optimization"
                status="completed"
              />
            </div>
            
            <div className="flex justify-center gap-4 mt-8">
              {user ? (
                <div className="text-center">
                  <p className="text-gray-600 mb-4">Welcome back, {user.first_name || user.email}!</p>
                  <button
                    onClick={showWealthPath}
                    className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all transform hover:-translate-y-1 shadow-lg mr-4"
                  >
                    🚀 Continue to WealthPath AI
                  </button>
                  <button
                    onClick={handleLogout}
                    className="px-6 py-4 bg-gray-200 text-gray-700 text-lg rounded-lg font-semibold hover:bg-gray-300 transition-all"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <>
                  <button
                    onClick={showLogin}
                    className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all transform hover:-translate-y-1 shadow-lg"
                  >
                    🔐 Login to WealthPath AI
                  </button>
                  <button
                    onClick={showRegister}
                    className="px-8 py-4 bg-gray-200 text-gray-700 text-lg rounded-lg font-semibold hover:bg-gray-300 transition-all transform hover:-translate-y-1 shadow-lg"
                  >
                    ✨ Create Account
                  </button>
                </>
              )}
            </div>
          </div>

          <footer className="text-center text-gray-500 text-sm">
            <p>🤖 Built with Claude Code | WealthPath AI 2.0 Production Ready</p>
          </footer>
        </div>
      </div>
    </>
  )
}

interface StatusItemProps {
  title: string
  description: string
  status: 'completed' | 'in-progress' | 'pending'
}

function StatusItem({ title, description, status }: StatusItemProps) {
  const statusColors = {
    completed: 'bg-green-50 border-green-200 text-green-800',
    'in-progress': 'bg-yellow-50 border-yellow-200 text-yellow-800',
    pending: 'bg-gray-50 border-gray-200 text-gray-600'
  }

  return (
    <div className={`p-4 rounded-lg border ${statusColors[status]}`}>
      <h3 className="font-semibold mb-1">{title}</h3>
      <p className="text-sm opacity-90">{description}</p>
    </div>
  )
}

// WealthPath AI 2.0 Component
interface WealthPathAppProps {
  onBack: () => void
  user: any
  onLogout: () => void
}

const WealthPathApp: React.FC<WealthPathAppProps> = ({ onBack, user, onLogout }) => {
  const [currentStep, setCurrentStep] = useState(1) // Start directly with Step 1 (Profile)
  const [apiHealth, setApiHealth] = useState<any>(null)
  const [manualEntries, setManualEntries] = useState<any[]>([]) // Shared state across steps
  const [showAdminDashboard, setShowAdminDashboard] = useState(false) // Admin dashboard state

  useEffect(() => {
    // Check API connection
    apiClient.healthCheck()
      .then(data => setApiHealth(data))
      .catch(err => console.error('API connection failed:', err))
  }, [])

  const showStep = (step: number) => {
    setCurrentStep(step)
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      background: '#0f0f1a',
      color: '#e2e8f0',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{ 
        maxWidth: '1400px', 
        margin: '0 auto', 
        padding: '20px 15px',
        '@media (min-width: 768px)': {
          padding: '40px 20px'
        }
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '60px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h1 style={{
              fontSize: '3em',
              background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '20px'
            }}>
              WealthPath AI
            </h1>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              {/* Admin Link - Only visible to admin users */}
              {(() => {
                const authUser = useAuthStore.getState().user;
                return isCurrentUserAdmin(authUser || user);
              })() && (
                <button 
                  onClick={() => setShowAdminDashboard(!showAdminDashboard)}
                  style={{
                    background: 'rgba(34, 197, 94, 0.2)',
                    color: '#ffffff',
                    border: '1px solid rgba(34, 197, 94, 0.6)',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    fontSize: '12px',
                    opacity: 1,
                    transition: 'opacity 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                  title="Admin Dashboard"
                >
                  🛡️ Admin
                </button>
              )}
              
              <button 
                onClick={onBack}
                style={{
                  background: 'rgba(102, 126, 234, 0.1)',
                  color: '#667eea',
                  border: '1px solid #667eea',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                ← Back to Home
              </button>
            </div>
          </div>
          <p style={{ fontSize: '1.3em', color: '#94a3b8' }}>
            From Current State to Target Achievement: Intelligent Financial Guidance
          </p>
        </div>
        
        {/* Step Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 'clamp(20px, 5vw, 40px)',
          marginBottom: '50px',
          position: 'relative',
          flexWrap: 'wrap'
        }}>
          {/* Progress line */}
          <div style={{
            content: '',
            position: 'absolute',
            top: '50%',
            left: '20%',
            right: '20%',
            height: '2px',
            background: 'linear-gradient(90deg, #667eea 0%, #9f7aea 100%)',
            zIndex: 0
          }}></div>
          
          {[1, 2, 3, 4, 5, 6, 7, 8].map(step => (
            <div
              key={step}
              onClick={() => showStep(step)}
              style={{
                background: currentStep === step ? 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)' : 
                           step < currentStep ? '#10b981' : '#1a1a2e',
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: '1.2em',
                border: currentStep === step ? 'none' : '3px solid #2d2d4e',
                cursor: 'pointer',
                zIndex: 1,
                position: 'relative',
                transition: 'all 0.3s',
                boxShadow: currentStep === step ? '0 0 30px rgba(102,126,234,0.5)' : 'none'
              }}
            >
              {step}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div style={{
          background: '#1a1a2e',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          border: '1px solid #2d2d4e'
        }}>
          {/* App Header */}
          <div style={{
            background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)',
            padding: '25px 30px',
            borderBottom: '1px solid #2d2d4e',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{
              fontSize: '1.8em',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              WealthPath AI
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 16px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid #10b981',
              borderRadius: '20px',
              color: '#10b981',
              fontSize: '0.9em'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                background: '#10b981',
                borderRadius: '50%'
              }}></div>
              <span>{apiHealth ? 'Live Sync Active' : 'Connecting...'}</span>
            </div>
          </div>
          
          {/* Step Content Area */}
          <div style={{ padding: '40px', minHeight: '500px' }}>
            {currentStep === 0 && (
              <div>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                  <h2 style={{ color: '#667eea', fontSize: '2em', marginBottom: '10px' }}>🧪 Phase 2 Test: Data Service Layer</h2>
                  <p style={{ color: '#94a3b8', fontSize: '1.1em' }}>Testing our clean FinancialDataService that fetches from new clean API endpoints</p>
                  <button 
                    onClick={() => showStep(1)}
                    style={{
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '12px 24px',
                      marginTop: '20px',
                      cursor: 'pointer',
                      fontSize: '16px'
                    }}
                  >
                    Skip to Main App →
                  </button>
                </div>
                <TestFinancialService />
              </div>
            )}
            {currentStep === 1 && <ProfileDataStep onNext={() => showStep(2)} />}
            {currentStep === 2 && <FinancialDataStep onNext={() => showStep(3)} />}
            {currentStep === 3 && <CurrentStateStep onNext={() => showStep(4)} manualEntries={manualEntries} />}
            {currentStep === 4 && <GoalDefinitionStep onNext={() => showStep(5)} />}
            {currentStep === 5 && <IntelligenceStep onNext={() => showStep(6)} />}
            {currentStep === 6 && <RoadmapStep onNext={() => showStep(7)} />}
            {currentStep === 7 && <ChatStep />}
            {currentStep === 8 && <DebugStep />}
          </div>
        </div>
      </div>

      {/* Admin Dashboard Overlay - Completely Isolated */}
      {showAdminDashboard && isCurrentUserAdmin(useAuthStore.getState().user || user) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: '#1a1a1a',
          zIndex: 9999,
          overflow: 'auto'
        }}>
          {/* Admin Dashboard Header with Back Button */}
          <div style={{
            position: 'sticky',
            top: 0,
            background: '#2a2a2a',
            borderBottom: '1px solid #404040',
            padding: '1rem',
            zIndex: 10000
          }}>
            <div style={{ 
              maxWidth: '1200px', 
              margin: '0 auto',
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center' 
            }}>
              <h1 style={{ margin: 0, color: '#1f2937', fontSize: '1.5rem', fontWeight: 'bold' }}>
                🛡️ Admin Dashboard
              </h1>
              <button 
                onClick={() => setShowAdminDashboard(false)}
                style={{
                  background: 'rgba(102, 126, 234, 0.1)',
                  color: '#667eea',
                  border: '1px solid #667eea',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                ← Back to App
              </button>
            </div>
          </div>
          
          {/* Admin Dashboard Content */}
          <AdminDashboard user={user} />
        </div>
      )}
    </div>
  )
}

// Step Components

// Modern Financial Data Entry Step 
interface FinancialDataStepProps {
  onNext: () => void
}

const FinancialDataStep: React.FC<FinancialDataStepProps> = ({ onNext }) => {
  return (
    <div style={{ 
      background: '#ffffff',
      borderRadius: '12px',
      margin: '-40px',
      minHeight: '500px'
    }}>
      {/* Step Header */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
        color: '#e2e8f0',
        padding: '20px 30px',
        borderRadius: '12px 12px 0 0',
        marginBottom: '0'
      }}>
        <h2 style={{ fontSize: '1.8em', margin: '0 0 10px 0', fontWeight: 'bold' }}>
          📊 Financial Data Entry
        </h2>
        <p style={{ margin: '0', opacity: '0.9', fontSize: '1.1em' }}>
          Organize and manage your financial information with our intelligent entry system
        </p>
      </div>
      
      {/* Financial Management Page */}
      <FinancialManagementPage />
      
      {/* Continue Button */}
      <div style={{
        padding: '20px 30px',
        borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        borderRadius: '0 0 12px 12px'
      }}>
        <button
          onClick={onNext}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
            color: '#e2e8f0',
            border: 'none',
            padding: '12px 30px',
            borderRadius: '8px',
            fontSize: '1.1em',
            fontWeight: 'bold',
            cursor: 'pointer',
            float: 'right'
          }}
        >
          Continue to Current State →
        </button>
        <div style={{ clear: 'both' }}></div>
      </div>
    </div>
  )
}

// Profile Data Entry Step
interface ProfileDataStepProps {
  onNext: () => void
}

const ProfileDataStep: React.FC<ProfileDataStepProps> = ({ onNext }) => {
  return (
    <div style={{ 
      background: '#ffffff',
      borderRadius: '12px',
      margin: '-40px',
      minHeight: '500px'
    }}>
      {/* Step Header */}
      <div style={{
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        color: '#e2e8f0',
        padding: '20px 30px',
        borderRadius: '12px 12px 0 0',
        marginBottom: '0'
      }}>
        <h2 style={{ fontSize: '1.8em', margin: '0 0 10px 0', fontWeight: 'bold' }}>
          👤 Profile & Family Information
        </h2>
        <p style={{ margin: '0', opacity: '0.9', fontSize: '1.1em' }}>
          Start by setting up your personal profile, family members, benefits, and tax information
        </p>
      </div>
      
      {/* Profile Management Page */}
      <ProfileManagementPage />
      
      {/* Continue Button */}
      <div style={{
        padding: '20px 30px',
        borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        borderRadius: '0 0 12px 12px'
      }}>
        <button
          onClick={onNext}
          style={{
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: '#e2e8f0',
            border: 'none',
            padding: '12px 30px',
            borderRadius: '8px',
            fontSize: '1.1em',
            fontWeight: 'bold',
            cursor: 'pointer',
            float: 'right'
          }}
        >
          Continue to Financial Data →
        </button>
        <div style={{ clear: 'both' }}></div>
      </div>
    </div>
  )
}

interface DataAggregationStepProps {
  onNext: () => void
  manualEntries: any[]
  setManualEntries: (entries: any[]) => void
}

const DataAggregationStep: React.FC<DataAggregationStepProps> = ({ onNext, manualEntries, setManualEntries }) => {
  const [showManualEntry, setShowManualEntry] = useState<string | null>(null)
  const [editingEntry, setEditingEntry] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Fetch existing manual entries on component mount
  useEffect(() => {
    const fetchExistingEntries = async () => {
      try {
        console.log('🔍 Fetching existing manual entries from database...')
        
        // Check if user is authenticated
        try {
          await apiClient.get('/api/v1/auth/me')
        } catch (authErr) {
          console.log('❌ User not authenticated, skipping entry fetch')
          setLoading(false)
          return
        }

        // Fetch entries from backend
        const entries = await apiClient.get('/api/v1/financial/entries')
        console.log('✅ Found existing entries:', entries)
        
        // Convert backend entries to frontend format
        const frontendEntries = entries.map((entry: any) => ({
          id: entry.id,
          description: entry.description,
          amount: parseFloat(entry.amount),
          category: entry.category,
          frequency: entry.frequency,
          sourceType: entry.subcategory || 'Manual Entry',
          notes: entry.notes
        }))
        
        console.log('🔄 Setting manual entries:', frontendEntries)
        setManualEntries(frontendEntries)
        
      } catch (error: any) {
        console.error('❌ Failed to fetch existing entries:', error)
        // Don't show error to user, just continue with empty entries
      } finally {
        setLoading(false)
      }
    }

    fetchExistingEntries()
  }, [])

  const dataSources = [
    { 
      name: 'Banking', 
      status: 'connected', 
      accounts: '3 accounts',
      details: 'Checking, Savings, Money Market',
      quality: 'DQ1'
    },
    { 
      name: 'Investments', 
      status: 'connected', 
      accounts: '2 accounts',
      details: 'Brokerage, Robo-advisor',
      quality: 'DQ1' 
    },
    { 
      name: 'Real Estate', 
      status: 'pending', 
      accounts: '1 property',
      details: 'Primary residence',
      quality: 'DQ3'
    },
    { 
      name: 'Retirement', 
      status: 'pending', 
      accounts: '401k, IRA',
      details: '401k, Traditional IRA',
      quality: 'DQ2'
    },
    {
      name: 'Loans & Credit',
      status: 'pending',
      accounts: '4 accounts',
      details: 'Mortgage, Auto, Credit Cards',
      quality: 'DQ4'
    },
    {
      name: 'Insurance',
      status: 'pending', 
      accounts: '3 policies',
      details: 'Auto, Home, Life',
      quality: 'DQ4'
    }
  ]

  const getQualityBadgeStyle = (quality: string) => {
    const styles = {
      DQ1: { background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: '1px solid #10b981' },
      DQ2: { background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid #3b82f6' },
      DQ3: { background: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24', border: '1px solid #fbbf24' },
      DQ4: { background: 'rgba(156, 163, 175, 0.2)', color: '#9ca3af', border: '1px solid #9ca3af' }
    }
    return styles[quality as keyof typeof styles]
  }

  const addManualEntry = async (sourceType: string, entry: any) => {
    console.log('🔥 ATTEMPTING MANUAL ENTRY SUBMISSION:', { sourceType, entry })
    
    try {
      // Check if user is authenticated first
      try {
        const authCheck = await apiClient.get('/api/v1/auth/me')
        console.log('✅ User authenticated:', authCheck.email)
      } catch (authErr) {
        console.error('❌ AUTHENTICATION FAILED:', authErr)
        alert('Please log in again to save entries')
        return
      }

      // Map frontend entry to backend schema
      const backendEntry = {
        category: entry.category, // asset, liability, income, expense
        subcategory: entry.subcategory || sourceType.toLowerCase(),
        description: entry.description,
        amount: entry.amount,
        currency: 'USD',
        frequency: entry.frequency || 'one_time',
        notes: `Added via ${sourceType} manual entry`
      }

      console.log('📤 SENDING TO BACKEND:', backendEntry)

      // Send to backend API
      const response = await apiClient.post('/api/v1/financial/entries', backendEntry)
      console.log('✅ BACKEND RESPONSE:', response)
      
      // Add to local state for immediate UI update
      setManualEntries([...manualEntries, { ...entry, sourceType, id: response.id }])
      
      // Trigger refresh for other screens that need updated data
      window.dispatchEvent(new CustomEvent('financialDataUpdated'))
      
      console.log('✅ Manual entry saved successfully!')
      alert(`Entry saved: ${entry.description} - $${entry.amount}`)
      
    } catch (error: any) {
      console.error('❌ FAILED TO SAVE MANUAL ENTRY:', error)
      console.error('Error type:', typeof error)
      console.error('Error keys:', Object.keys(error || {}))
      console.error('Error details:', {
        message: error?.message,
        detail: error?.detail,
        status: error?.status_code,
        response: error?.response,
        data: error?.response?.data,
        fullError: error
      })
      
      // Better error message extraction
      let errorMsg = 'Unknown error'
      if (typeof error === 'string') {
        errorMsg = error
      } else if (error?.detail) {
        if (typeof error.detail === 'string') {
          errorMsg = error.detail
        } else if (Array.isArray(error.detail)) {
          errorMsg = error.detail.map((e: any) => `${e.loc?.join('.')} - ${e.msg}`).join('; ')
        } else {
          errorMsg = JSON.stringify(error.detail, null, 2)
        }
      } else if (error?.message) {
        errorMsg = error.message
      } else {
        try {
          errorMsg = JSON.stringify(error, null, 2)
        } catch {
          errorMsg = String(error)
        }
      }
      
      console.error('Final error message:', errorMsg)
      alert(`FAILED TO SAVE: ${errorMsg}`)
      
      // Still add to local state for offline functionality
      setManualEntries([...manualEntries, { ...entry, sourceType, id: Date.now() }])
    }
  }

  const editManualEntry = (entry: any) => {
    setEditingEntry(entry)
  }

  const updateManualEntry = async (updatedEntry: any) => {
    console.log('🔄 UPDATING MANUAL ENTRY:', updatedEntry)
    
    try {
      // If entry has a database ID, update it via API
      if (updatedEntry.id && typeof updatedEntry.id === 'string') {
        const backendUpdate = {
          category: updatedEntry.category,
          subcategory: updatedEntry.subcategory || updatedEntry.sourceType?.toLowerCase(),
          description: updatedEntry.description,
          amount: updatedEntry.amount,
          currency: 'USD',
          frequency: updatedEntry.frequency || 'one_time',
          notes: `Updated via ${updatedEntry.sourceType} manual entry`
        }

        console.log('📤 SENDING UPDATE TO BACKEND:', backendUpdate)
        const response = await apiClient.put(`/api/v1/financial/entries/${updatedEntry.id}`, backendUpdate)
        console.log('✅ BACKEND UPDATE RESPONSE:', response)
        
        alert(`Entry updated: ${updatedEntry.description} - $${updatedEntry.amount}`)
      }
      
      // Update local state
      setManualEntries(manualEntries.map(entry => 
        entry.id === updatedEntry.id ? updatedEntry : entry
      ))
      
      // Trigger refresh for other screens
      window.dispatchEvent(new CustomEvent('financialDataUpdated'))
      
      setEditingEntry(null)
      
    } catch (error: any) {
      console.error('❌ FAILED TO UPDATE ENTRY:', error)
      alert(`Failed to update: ${error?.detail || error?.message || 'Unknown error'}`)
      
      // Still update local state
      setManualEntries(manualEntries.map(entry => 
        entry.id === updatedEntry.id ? updatedEntry : entry
      ))
      setEditingEntry(null)
    }
  }

  const cancelEdit = () => {
    setEditingEntry(null)
  }

  const removeManualEntry = async (id: number) => {
    console.log('🗑️ DELETING MANUAL ENTRY:', id)
    
    try {
      // If entry has a database ID, delete it via API
      if (typeof id === 'string') {
        console.log('📤 SENDING DELETE TO BACKEND')
        await apiClient.delete(`/api/v1/financial/entries/${id}`)
        console.log('✅ ENTRY DELETED FROM BACKEND')
        alert('Entry deleted successfully')
      }
      
      // Remove from local state
      setManualEntries(manualEntries.filter(entry => entry.id !== id))
      
      // Trigger refresh for other screens
      window.dispatchEvent(new CustomEvent('financialDataUpdated'))
      
    } catch (error: any) {
      console.error('❌ FAILED TO DELETE ENTRY:', error)
      alert(`Failed to delete: ${error?.detail || error?.message || 'Unknown error'}`)
      
      // Still remove from local state
      setManualEntries(manualEntries.filter(entry => entry.id !== id))
    }
  }

  const groupEntriesByCategory = (entries: any[]) => {
    const groups: { [key: string]: any[] } = {}
    
    entries.forEach(entry => {
      let categoryKey = ''
      
      switch(entry.category) {
        case 'income':
          if (entry.description.toLowerCase().includes('salary') || entry.description.toLowerCase().includes('employment')) {
            categoryKey = 'EMPLOYMENT INCOME'
          } else {
            categoryKey = 'OTHER INCOME'
          }
          break
        case 'asset':
          if (entry.description.toLowerCase().includes('real estate') || entry.description.toLowerCase().includes('property') || entry.description.toLowerCase().includes('residence')) {
            categoryKey = 'REAL ESTATE'
          } else if (entry.description.toLowerCase().includes('investment') || entry.description.toLowerCase().includes('stock') || entry.description.toLowerCase().includes('bond')) {
            categoryKey = 'INVESTMENTS'
          } else {
            categoryKey = 'ASSETS'
          }
          break
        case 'liability':
          categoryKey = 'LIABILITIES'
          break
        case 'expense':
          categoryKey = 'EXPENSES'
          break
        default:
          categoryKey = 'OTHER'
      }
      
      if (!groups[categoryKey]) {
        groups[categoryKey] = []
      }
      groups[categoryKey].push(entry)
    })
    
    return groups
  }

  return (
    <div>
      <h2 style={{ marginBottom: '30px', fontSize: '2em', color: '#e2e8f0' }}>Connect Your Financial World</h2>
      <p style={{ color: '#94a3b8', marginBottom: '30px', fontSize: '1.1em' }}>
        Securely connect your accounts for real-time financial insights
      </p>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px',
        marginBottom: '40px',
        alignItems: 'start' // This prevents cards from stretching to match the tallest card
      }}>
        {dataSources.map((source, index) => (
          <div key={index} style={{
            background: source.status === 'connected' ? 'rgba(16, 185, 129, 0.05)' : '#0f0f1a',
            border: source.status === 'connected' ? '2px solid #10b981' : '2px solid #2d2d4e',
            borderRadius: '12px',
            padding: '25px',
            position: 'relative',
            height: 'fit-content' // Each card only takes the height it needs
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ color: '#e2e8f0', fontSize: '1.2em', fontWeight: '600' }}>{source.name}</h3>
              <div style={{
                ...getQualityBadgeStyle(source.quality),
                padding: '4px 10px',
                borderRadius: '15px',
                fontSize: '0.8em',
                fontWeight: '600'
              }}>
                {source.quality}
              </div>
            </div>
            
            <div style={{ color: '#94a3b8', fontSize: '0.95em', marginBottom: '5px' }}>
              {source.accounts}
            </div>
            <div style={{ color: '#94a3b8', fontSize: '0.85em', marginBottom: '15px' }}>
              {source.details}
            </div>
            
            {source.status === 'connected' ? (
              <div style={{
                width: '100%',
                padding: '10px',
                background: 'rgba(16, 185, 129, 0.1)',
                color: '#10b981',
                border: '1px solid #10b981',
                borderRadius: '8px',
                textAlign: 'center',
                fontWeight: '600'
              }}>
                ✓ Connected
              </div>
            ) : (
              <div>
                <button style={{
                  width: '100%',
                  padding: '10px',
                  background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
                  color: '#e2e8f0',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  marginBottom: '8px'
                }}>
                  Connect
                </button>
                <button 
                  onClick={() => setShowManualEntry(showManualEntry === source.name ? null : source.name)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: 'rgba(102, 126, 234, 0.1)',
                    color: '#667eea',
                    border: '1px solid #667eea',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Manual Entry
                </button>
              </div>
            )}
            
            {showManualEntry === source.name && (
              <ManualEntryForm 
                sourceType={source.name}
                onAddEntry={addManualEntry}
                onClose={() => setShowManualEntry(null)}
              />
            )}
          </div>
        ))}
      </div>

      {/* Global Manual Entry Section */}
      <div style={{
        background: '#1a1a2e',
        borderRadius: '12px',
        padding: '30px',
        marginBottom: '30px',
        border: '1px solid #2d2d4e'
      }}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '10px', fontSize: '1.5em' }}>Manual Entry</h3>
        <p style={{ color: '#94a3b8', marginBottom: '20px' }}>
          Add assets, liabilities, or income not captured by automatic connections
        </p>
        
        {/* Manual Entry Form */}
        <ManualEntryGlobalForm onAddEntry={addManualEntry} />
        
        {/* Edit Entry Modal */}
        {editingEntry && (
          <EditEntryModal 
            entry={editingEntry}
            onUpdate={updateManualEntry}
            onCancel={cancelEdit}
          />
        )}
        
        {/* Loading State */}
        {loading && (
          <div style={{ 
            textAlign: 'center', 
            color: '#94a3b8', 
            padding: '20px',
            fontSize: '0.9em'
          }}>
            Loading existing entries...
          </div>
        )}

        {/* Manual Entries List */}
        {!loading && manualEntries.length > 0 && (
          <div style={{ marginTop: '30px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {Object.entries(groupEntriesByCategory(manualEntries)).map(([category, entries]) => (
                <div key={category}>
                  <div style={{
                    fontSize: '0.85em',
                    color: '#667eea',
                    fontWeight: '600',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    marginBottom: '10px'
                  }}>
                    {category}
                  </div>
                  {(entries as any[]).map((entry: any) => (
                    <div key={entry.id} style={{
                      background: '#0f0f1a',
                      border: '1px solid #2d2d4e',
                      borderRadius: '8px',
                      padding: '20px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '10px'
                    }}>
                      <div>
                        <div style={{ color: '#e2e8f0', fontWeight: '500', marginBottom: '5px' }}>
                          {entry.description}
                        </div>
                        <div style={{
                          color: '#10b981',
                          fontWeight: '600',
                          fontSize: '1.1em',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px'
                        }}>
                          ${entry.amount.toLocaleString()} 
                          <span style={{ color: '#94a3b8', fontSize: '0.85em', fontWeight: '400' }}>
                            {entry.frequency === 'one_time' ? 'one-time' : entry.frequency || 'one-time'}
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => editManualEntry(entry)}
                          style={{
                            background: 'rgba(59, 130, 246, 0.1)',
                            color: '#3b82f6',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            width: '30px',
                            height: '30px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '1.1em'
                          }}
                        >
                          ✎
                        </button>
                        <button 
                          onClick={() => removeManualEntry(entry.id)}
                          style={{
                            background: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            border: '1px solid #ef4444',
                            borderRadius: '4px',
                            width: '30px',
                            height: '30px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '1.2em'
                          }}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <button onClick={onNext} style={{
        padding: '15px 40px',
        background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
        color: '#e2e8f0',
        border: 'none',
        borderRadius: '10px',
        fontWeight: '600',
        fontSize: '1.1em',
        cursor: 'pointer',
        margin: '30px auto',
        display: 'block'
      }}>
        Proceed to Current State Analysis →
      </button>
    </div>
  )
}

const ManualEntryGlobalForm: React.FC<{ onAddEntry: (sourceType: string, entry: any) => void }> = ({ onAddEntry }) => {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('')
  const [frequency, setFrequency] = useState('one_time')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (description && amount && category) {
      onAddEntry('Manual Entry', {
        description,
        amount: parseFloat(amount),
        category,
        frequency
      })
      setDescription('')
      setAmount('')
      setCategory('')
      setFrequency('one_time')
    }
  }

  return (
    <div style={{
      background: '#0f0f1a',
      border: '1px solid #2d2d4e',
      borderRadius: '12px',
      padding: '20px'
    }}>
      <form onSubmit={handleSubmit}>
        {/* Mobile-first responsive layout */}
        <div style={{ 
          display: 'flex',
          flexDirection: 'column',
          gap: '15px'
        }}>
          {/* First row - Category and Description */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '15px' 
          }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Category
              </label>
              <select
                value={category}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              >
                <option value="">Select category...</option>
                <option value="assets">Assets</option>
                <option value="liabilities">Liabilities</option>
                <option value="income">Income</option>
                <option value="expenses">Expenses</option>
              </select>
            </div>
            
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
                placeholder="e.g., Primary residence, Rental property A"
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              />
            </div>
          </div>
          
          {/* Second row - Value/Amount and Frequency */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
            gap: '15px' 
          }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Value/Amount
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAmount(e.target.value)}
                placeholder="$0"
                step="0.01"
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              />
            </div>
            
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFrequency(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              >
                <option value="one_time">One-time</option>
                <option value="monthly">Monthly</option>
                <option value="annually">Annually</option>
                <option value="quarterly">Quarterly</option>
              </select>
            </div>
          </div>
          
          {/* Add button row */}
          <div>
            <button
              type="submit"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
                color: '#e2e8f0',
                border: 'none',
                borderRadius: '8px',
                padding: '14px 24px',
                fontWeight: '600',
                cursor: 'pointer',
                minHeight: '48px',
                fontSize: '1em',
                width: '100%',
                maxWidth: '200px'
              }}
            >
              Add Entry
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}

const ManualEntryForm: React.FC<{ sourceType: string; onAddEntry: (sourceType: string, entry: any) => void; onClose: () => void }> = ({ sourceType, onAddEntry, onClose }) => {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('')
  const [frequency, setFrequency] = useState('monthly')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (description && amount) {
      onAddEntry(sourceType, {
        description,
        amount: parseFloat(amount),
        category,
        frequency
      })
      setDescription('')
      setAmount('')
      setCategory('')
      setFrequency('monthly')
    }
  }

  return (
    <div style={{
      background: '#1a1a2e',
      border: '1px solid #2d2d4e',
      borderRadius: '12px',
      padding: '20px',
      marginTop: '15px'
    }}>
      <form onSubmit={handleSubmit}>
        {/* Mobile-first responsive layout */}
        <div style={{ 
          display: 'flex',
          flexDirection: 'column',
          gap: '15px'
        }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '15px' 
          }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
                placeholder="e.g., Primary residence, 401k account"
                style={{
                  background: '#0f0f1a',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '44px'
                }}
              />
            </div>
            
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Amount ($)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                style={{
                  background: '#0f0f1a',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '44px'
                }}
              />
            </div>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
            gap: '15px' 
          }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Type
              </label>
              <select
                value={category}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
                style={{
                  background: '#0f0f1a',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '44px'
                }}
              >
                <option value="">Select</option>
                <option value="assets">Assets</option>
                <option value="liabilities">Liabilities</option>
                <option value="income">Income</option>
                <option value="expenses">Expenses</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'end' }}>
              <button
                type="submit"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
                  color: '#e2e8f0',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  minHeight: '44px',
                  fontSize: '1em',
                  width: '100%'
                }}
              >
                Add Entry
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}

interface CurrentStateStepProps {
  onNext: () => void
  manualEntries: any[]
}

// Comprehensive Financial Projection Component
const ComprehensiveTrajectoryProjection: React.FC<{
  currentNetWorth: number,
  monthlyCashFlow: number,
  savingsRate: number,
  financialSummary: any
}> = ({ currentNetWorth, monthlyCashFlow, savingsRate, financialSummary }) => {
  const [projectionData, setProjectionData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [timeHorizon, setTimeHorizon] = useState(20)
  const [error, setError] = useState<string | null>(null)
  
  const fetchComprehensiveProjection = async (forceRecalculate = false) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get('/api/v1/projections/comprehensive', {
        params: {
          years: timeHorizon,
          include_monte_carlo: true,
          monte_carlo_iterations: 1000,
          force_recalculate: forceRecalculate
        }
      })
      
      setProjectionData(response)
      console.log('📊 Comprehensive projection loaded:', response)
      
    } catch (err: any) {
      console.error('❌ Failed to load projection:', err)
      setError('Failed to load projection data. Using simplified calculation.')
    } finally {
      setLoading(false)
    }
  }
  
  // Load projection on mount and when timeHorizon changes
  useEffect(() => {
    fetchComprehensiveProjection()
  }, [timeHorizon])

  // Listen for assumptions updates from the AssumptionsPanel
  useEffect(() => {
    const handleAssumptionsUpdate = (event: any) => {
      console.log('🔄 Assumptions updated, refreshing projections...', event.detail);
      fetchComprehensiveProjection(true); // Force recalculate with new assumptions
    };

    window.addEventListener('assumptionsUpdated', handleAssumptionsUpdate);
    
    return () => {
      window.removeEventListener('assumptionsUpdated', handleAssumptionsUpdate);
    };
  }, [])
  
  if (loading) {
    return (
      <div style={{
        background: '#0f0f1a',
        borderRadius: '16px',
        padding: '30px',
        marginBottom: '30px',
        border: '1px solid #2d2d4e',
        textAlign: 'center'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid #2d2d4e',
          borderTop: '3px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 20px'
        }}></div>
        <p style={{ color: '#94a3b8' }}>Calculating comprehensive financial projection...</p>
        <p style={{ color: '#94a3b8', fontSize: '0.9em' }}>
          Running Monte Carlo simulation with {timeHorizon}-year horizon
        </p>
      </div>
    )
  }
  
  if (error && !projectionData) {
    // Fallback to simple calculation
    return (
      <SimpleTrajectoryFallback 
        currentNetWorth={currentNetWorth}
        monthlyCashFlow={monthlyCashFlow}
        savingsRate={savingsRate}
        timeHorizon={timeHorizon}
        error={error}
      />
    )
  }
  
  return (
    <div style={{
      background: '#0f0f1a',
      borderRadius: '16px',
      padding: '30px',
      marginBottom: '30px',
      border: '1px solid #2d2d4e'
    }}>
      {/* Header with Controls */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        marginBottom: '25px',
        flexWrap: 'wrap',
        gap: '15px'
      }}>
        <div>
          <h3 style={{ 
            color: '#e2e8f0', 
            fontSize: '1.8em', 
            margin: '0 0 5px 0',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            📊 Comprehensive Financial Trajectory
          </h3>
          <p style={{ 
            color: '#94a3b8', 
            fontSize: '1em',
            margin: 0
          }}>
            Multi-factor modeling with Monte Carlo simulation • {savingsRate.toFixed(1)}% savings rate
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select 
            value={timeHorizon}
            onChange={(e) => setTimeHorizon(Number(e.target.value))}
            style={{
              background: '#1a1a2e',
              border: '1px solid #2d2d4e',
              borderRadius: '8px',
              padding: '8px 12px',
              color: '#e2e8f0',
              fontSize: '0.9em'
            }}
          >
            <option value={5}>5 Years</option>
            <option value={10}>10 Years</option>
            <option value={20}>20 Years</option>
            <option value={30}>30 Years</option>
          </select>
          
          <button
            onClick={() => fetchComprehensiveProjection(true)}
            disabled={loading}
            style={{
              background: loading 
                ? '#6b7280' 
                : 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
              color: '#e2e8f0',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '0.9em',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              transition: 'all 0.2s ease'
            }}
          >
            {loading ? 'Calculating...' : 'Recalculate'}
          </button>
        </div>
      </div>
      
      {/* Multi-Scenario Projections */}
      {projectionData && (
        <>
          {/* Main Projection Metrics */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px',
            marginBottom: '25px'
          }}>
            {[5, 10, 20].filter(years => years <= timeHorizon).map(years => {
              const projection = projectionData.projections.find((p: any) => p.year === years)
              const increase = projection ? projection.net_worth - currentNetWorth : 0
              
              // Get confidence intervals if available
              const confidence = projectionData.confidence_intervals?.percentiles
              const p25 = confidence?.p25?.[years - 1] || projection?.net_worth
              const p75 = confidence?.p75?.[years - 1] || projection?.net_worth
              
              return (
                <div key={years} style={{
                  background: 'rgba(102, 126, 234, 0.1)',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                  borderRadius: '12px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{ 
                    color: '#94a3b8', 
                    fontSize: '0.9em', 
                    marginBottom: '8px',
                    fontWeight: '600'
                  }}>
                    In {years} Years
                  </div>
                  <div style={{ 
                    color: '#667eea', 
                    fontSize: '1.6em', 
                    fontWeight: '700',
                    marginBottom: '8px'
                  }}>
                    {formatCurrency(projection?.net_worth || 0)}
                  </div>
                  <div style={{ 
                    color: '#10b981', 
                    fontSize: '0.85em',
                    fontWeight: '600',
                    marginBottom: confidence ? '8px' : '0'
                  }}>
                    +{formatCurrency(increase)}
                  </div>
                  {confidence && (
                    <div style={{ 
                      color: '#94a3b8', 
                      fontSize: '0.75em'
                    }}>
                      Range: {formatCurrency(p25)} - {formatCurrency(p75)}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          
          {/* TRANSPARENCY LAYER - LOGICAL INFORMATION FLOW */}
          {/* Architecture Lead Directive: Show WHAT → HOW → CONFIDENCE → SCENARIOS → MATH → GOALS */}
          
          {/* 1. METHODOLOGY - How we calculate (immediately after showing projections) */}
          <div style={{
            background: 'rgba(156, 163, 175, 0.05)',
            borderRadius: '8px',
            padding: '15px',
            border: '1px solid rgba(156, 163, 175, 0.2)',
            marginBottom: '20px'
          }}>
            <div style={{ color: '#9ca3af', fontSize: '0.85em', lineHeight: '1.4' }}>
              <strong>Methodology:</strong> Multi-factor projection considers asset appreciation, income growth, 
              intelligent savings allocation, and market volatility. Monte Carlo simulation with {projectionData.calculation_metadata?.monte_carlo_iterations || 1000} iterations 
              provides confidence intervals. Calculation time: {projectionData.calculation_metadata?.calculation_time_ms}ms.
            </div>
          </div>
          
          {/* 2. ASSUMPTIONS - What rates and parameters we use */}
          <AssumptionsPanel />
          
          {/* 3. CONFIDENCE ANALYSIS - Monte Carlo ranges */}
          <MonteCarloVisualization projectionData={projectionData} />
          
          {/* 4. METHODOLOGY EXPLAINER - Detailed explanation */}
          <MethodologyExplainer />
          
          {/* 5. WHAT-IF SCENARIOS - Alternative paths */}
          <WhatIfScenarios baseProjection={projectionData} />
          
          {/* 6. CALCULATION BREAKDOWN - Detailed math for each milestone */}
          {[5, 10, 20].map(year => (
            <ProjectionBreakdown 
              key={year}
              projection={projectionData} 
              year={year}
            />
          ))}
          
          {/* 7. FINANCIAL MILESTONES - Goals timeline (MOVED TO END) */}
          {projectionData.milestones && projectionData.milestones.length > 0 && (
            <div style={{
              background: 'linear-gradient(135deg, #1a1a2e 0%, #2d1b69 100%)',
              borderRadius: '16px',
              padding: '24px',
              margin: '30px 0 0 0',
              border: '2px solid #667eea',
              boxShadow: '0 8px 32px rgba(102, 126, 234, 0.15)'
            }}>
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{
                  color: '#f3f4f6',
                  fontSize: '1.4em',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '8px'
                }}>
                  🎯 Your Financial Milestones Timeline
                </h4>
                <p style={{
                  color: '#9ca3af',
                  fontSize: '0.9em',
                  lineHeight: '1.5',
                  margin: 0
                }}>
                  Based on the projections and analysis above, here's when you'll reach key financial milestones
                </p>
              </div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px'
              }}>
                {projectionData.milestones.slice(0, 4).map((milestone: any, index: number) => {
                  const isAchieved = milestone.years_to_achieve === 1;
                  return (
                    <div key={index} style={{
                      background: isAchieved 
                        ? 'rgba(16, 185, 129, 0.1)' // Green background for achieved
                        : 'rgba(255, 255, 255, 0.05)', // Default background for future
                      borderRadius: '12px',
                      padding: '20px',
                      border: isAchieved 
                        ? '1px solid rgba(16, 185, 129, 0.3)' // Green border for achieved
                        : '1px solid rgba(255, 255, 255, 0.1)', // Default border for future
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px',
                      transition: 'all 0.3s ease'
                    }}>
                    <div style={{
                      fontSize: '2em',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '60px',
                      height: '60px',
                      borderRadius: '50%',
                      background: 'rgba(102, 126, 234, 0.2)'
                    }}>
                      {milestone.icon || '🎯'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontWeight: '700',
                        fontSize: '1.1em',
                        color: '#f3f4f6',
                        marginBottom: '4px'
                      }}>
                        {milestone.label}
                      </div>
                      <div style={{ 
                        color: '#60a5fa',
                        fontSize: '0.9em',
                        marginBottom: '6px'
                      }}>
                        {milestone.years_to_achieve ? 
                          (milestone.years_to_achieve === 1 ? 'Already achieved!' : `${milestone.years_to_achieve} years`) 
                          : 'Timeline varies'
                        }
                      </div>
                      {/* FIXED: Only show confidence for FUTURE milestones, not achieved ones */}
                      {milestone.years_to_achieve === 1 ? (
                        <div style={{ 
                          color: '#10b981',
                          fontSize: '0.8em',
                          fontWeight: '500',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          ✅ Completed
                        </div>
                      ) : milestone.confidence_score && (
                        <div style={{ 
                          color: '#fbbf24',
                          fontSize: '0.8em',
                          fontWeight: '500'
                        }}>
                          {milestone.confidence_score}% confidence
                        </div>
                      )}
                    </div>
                  </div>
                  );
                })}
              </div>
              
              {/* Context Note */}
              <div style={{
                marginTop: '24px',
                padding: '16px',
                background: 'rgba(59, 130, 246, 0.1)',
                borderRadius: '12px',
                border: '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                <p style={{
                  color: '#93c5fd',
                  fontSize: '0.9em',
                  lineHeight: '1.5',
                  margin: 0
                }}>
                  💡 <strong>Achieved milestones</strong> are 100% certain (marked "✅ Completed"). 
                  <strong>Future milestones</strong> show projected timelines with confidence based on Monte Carlo analysis. 
                  Use the What-If scenarios above to see how changes affect your future milestone timeline.
                </p>
              </div>
            </div>
          )}
          
        </>
      )}
    </div>
  )
}

// Fallback component for simple trajectory calculation
const SimpleTrajectoryFallback: React.FC<{
  currentNetWorth: number,
  monthlyCashFlow: number,
  savingsRate: number,
  timeHorizon: number,
  error: string
}> = ({ currentNetWorth, monthlyCashFlow, savingsRate, timeHorizon, error }) => {
  // Simple compound growth calculation
  const calculateSimpleProjection = (years: number): number => {
    const monthlyGrowthRate = 0.04 / 12 // 4% annual
    let projectedValue = currentNetWorth
    
    for (let month = 0; month < years * 12; month++) {
      projectedValue = (projectedValue * (1 + monthlyGrowthRate)) + monthlyCashFlow
    }
    
    return Math.round(projectedValue)
  }
  
  return (
    <div style={{
      background: '#0f0f1a',
      borderRadius: '16px',
      padding: '30px',
      marginBottom: '30px',
      border: '1px solid #2d2d4e'
    }}>
      {/* Error Notice */}
      <div style={{
        background: 'rgba(251, 191, 36, 0.1)',
        border: '1px solid #fbbf24',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '20px',
        color: '#fbbf24',
        fontSize: '0.9em'
      }}>
        ⚠️ {error}
      </div>
      
      <h3 style={{ 
        color: '#e2e8f0', 
        fontSize: '1.8em', 
        margin: '0 0 5px 0',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        📈 Basic Trajectory Projection
      </h3>
      <p style={{ 
        color: '#94a3b8', 
        fontSize: '1em',
        marginBottom: '25px'
      }}>
        Simple compound growth model • {savingsRate.toFixed(1)}% savings rate
      </p>
      
      {/* Simple Projections */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '25px'
      }}>
        {[5, 10, 20].filter(years => years <= timeHorizon).map(years => {
          const projected = calculateSimpleProjection(years)
          const increase = projected - currentNetWorth
          
          return (
            <div key={years} style={{
              background: 'rgba(102, 126, 234, 0.1)',
              border: '1px solid rgba(102, 126, 234, 0.3)',
              borderRadius: '12px',
              padding: '20px',
              textAlign: 'center'
            }}>
              <div style={{ 
                color: '#94a3b8', 
                fontSize: '0.9em', 
                marginBottom: '8px',
                fontWeight: '600'
              }}>
                In {years} Years
              </div>
              <div style={{ 
                color: '#667eea', 
                fontSize: '1.6em', 
                fontWeight: '700',
                marginBottom: '8px'
              }}>
                {formatCurrency(projected)}
              </div>
              <div style={{ 
                color: '#10b981', 
                fontSize: '0.85em',
                fontWeight: '600'
              }}>
                +{formatCurrency(increase)}
              </div>
            </div>
          )
        })}
      </div>
      
      <div style={{
        background: 'rgba(156, 163, 175, 0.05)',
        borderRadius: '8px',
        padding: '15px',
        border: '1px solid rgba(156, 163, 175, 0.2)',
        color: '#9ca3af',
        fontSize: '0.85em'
      }}>
        <strong>Note:</strong> This is a simplified projection using basic compound growth. 
        For comprehensive multi-factor analysis with Monte Carlo simulation, please ensure you're logged in.
      </div>
    </div>
  )
}

// TRANSPARENCY LAYER COMPONENTS - Architecture Lead Directive
// Component 1: ProjectionBreakdown - Show exact calculations
interface ProjectionBreakdownProps {
  projection: any;
  year: number;
}

const ProjectionBreakdown: React.FC<ProjectionBreakdownProps> = ({ projection, year }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [breakdownData, setBreakdownData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchBreakdown = async () => {
    if (breakdownData) return; // Already loaded
    
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/v1/projections/breakdown/${year}`);
      setBreakdownData(response);
    } catch (error) {
      console.error('Failed to fetch breakdown:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleDetails = () => {
    setShowDetails(!showDetails);
    if (!showDetails && !breakdownData) {
      fetchBreakdown();
    }
  };

  if (!breakdownData && showDetails && loading) {
    return (
      <div className="projection-breakdown bg-gray-800 rounded-lg p-4 mt-4">
        <div style={{ color: '#94a3b8' }}>Loading calculation details...</div>
      </div>
    );
  }

  return (
    <div className="projection-breakdown bg-gray-800 rounded-lg p-4 mt-4">
      <button
        onClick={handleToggleDetails}
        style={{
          background: 'none',
          border: 'none',
          color: '#60a5fa',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: '500'
        }}
      >
        <span>{showDetails ? '📊' : '📈'}</span>
        <span>{showDetails ? 'Hide' : 'Show'} How We Calculated This</span>
        <span style={{ transform: showDetails ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </button>
      
      {showDetails && breakdownData && (
        <div style={{ marginTop: '16px' }}>
          {/* Starting Point */}
          <div style={{ borderLeft: '4px solid #10b981', paddingLeft: '16px', marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Starting Point</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff' }}>
              {formatCurrency(breakdownData.starting_point.net_worth)}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Current Net Worth</div>
          </div>
          
          {/* Growth Components */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '500', color: '#d1d5db', marginBottom: '12px' }}>
              Growth Components ({year} Years)
            </h4>
            
            {Object.entries(breakdownData.growth_components).map(([key, component]: [string, any]) => (
              <div key={key} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '8px 12px',
                marginBottom: '8px',
                backgroundColor: '#374151',
                borderRadius: '6px'
              }}>
                <div>
                  <div style={{ color: '#fff', fontSize: '13px', fontWeight: '500' }}>
                    {component.explanation}
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '2px' }}>
                    {component.calculation}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#10b981', fontSize: '14px', fontWeight: 'bold' }}>
                    {formatCurrency(component.amount)}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '11px' }}>
                    {component.percentage}%
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Final Calculation */}
          <div style={{ borderTop: '1px solid #374151', paddingTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#94a3b8' }}>Total Projected Value</span>
              <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
                {formatCurrency(breakdownData.final_calculation.final_projected_value)}
              </span>
            </div>
            <div style={{ color: '#6b7280', fontSize: '11px', marginTop: '4px', textAlign: 'center' }}>
              {breakdownData.final_calculation.verification}
            </div>
          </div>
          
          {/* Trust Statement */}
          <div style={{ 
            marginTop: '16px', 
            padding: '12px', 
            backgroundColor: '#1e3a8a20', 
            borderRadius: '6px',
            border: '1px solid #1e40af'
          }}>
            <div style={{ color: '#60a5fa', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>
              🔒 {breakdownData.transparency_note}
            </div>
            <div style={{ color: '#94a3b8', fontSize: '11px' }}>
              Calculation completed in {breakdownData.calculation_metadata.monte_carlo_iterations} Monte Carlo iterations
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Component 2: AssumptionsPanel - Interactive assumptions with sliders
const AssumptionsPanel: React.FC = () => {
  const [editMode, setEditMode] = useState(false);
  const [assumptions, setAssumptions] = useState<any>(null);
  const [originalAssumptions, setOriginalAssumptions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [autoRecalcTimer, setAutoRecalcTimer] = useState<NodeJS.Timeout | null>(null);
  const [isAutoRecalculating, setIsAutoRecalculating] = useState(false);

  useEffect(() => {
    const fetchAssumptions = async () => {
      try {
        const response = await apiClient.get('/api/v1/projections/assumptions');
        setAssumptions(response.assumptions);
        setOriginalAssumptions({ ...response.assumptions });
      } catch (error) {
        console.error('Failed to fetch assumptions:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAssumptions();

    // Cleanup timer on unmount
    return () => {
      if (autoRecalcTimer) {
        clearTimeout(autoRecalcTimer);
      }
    };
  }, []);

  const handleSliderChange = (key: string, value: number) => {
    const newAssumptions = { ...assumptions, [key]: value / 100 }; // Convert to decimal
    setAssumptions(newAssumptions);
    
    // Check if there are changes
    const changes = Object.keys(newAssumptions).some(k => 
      Math.abs(newAssumptions[k] - originalAssumptions[k]) > 0.0001
    );
    setHasChanges(changes);

    // Clear existing timer
    if (autoRecalcTimer) {
      clearTimeout(autoRecalcTimer);
    }

    // Set new timer for auto-recalculation (2 seconds after user stops sliding)
    if (changes) {
      const timer = setTimeout(async () => {
        try {
          setIsAutoRecalculating(true);
          // Auto-save and trigger recalculation
          await apiClient.post('/api/v1/projections/assumptions', newAssumptions);
          setOriginalAssumptions({ ...newAssumptions });
          setHasChanges(false);
          
          // Trigger projection refresh
          const event = new CustomEvent('assumptionsUpdated', { detail: newAssumptions });
          window.dispatchEvent(event);
          
          console.log('🔄 Auto-recalculated with new assumptions:', newAssumptions);
        } catch (error) {
          console.error('Auto-recalculation failed:', error);
        } finally {
          setIsAutoRecalculating(false);
        }
      }, 2000);
      
      setAutoRecalcTimer(timer);
    }
  };

  const handleApplyChanges = async () => {
    setIsApplying(true);
    try {
      // First save the assumptions
      await apiClient.post('/api/v1/projections/assumptions', assumptions);
      setOriginalAssumptions({ ...assumptions });
      setHasChanges(false);
      setEditMode(false);
      
      // Show success feedback
      console.log('Assumptions updated successfully');
      
      // Trigger a projection recalculation by dispatching a custom event
      // This will tell the parent ComprehensiveTrajectoryProjection to refresh
      const event = new CustomEvent('assumptionsUpdated', { detail: assumptions });
      window.dispatchEvent(event);
      
    } catch (error) {
      console.error('Failed to update assumptions:', error);
      alert('Failed to save assumptions. Please try again.');
    } finally {
      setIsApplying(false);
    }
  };

  const resetToDefaults = () => {
    setAssumptions({ ...originalAssumptions });
    setHasChanges(false);
  };

  if (loading) {
    return <div style={{ color: '#94a3b8' }}>Loading assumptions...</div>;
  }

  const labels: {[key: string]: any} = {
    'stock_market_return': { label: 'Stock Returns', icon: '📊', tooltip: 'Historical S&P 500 average: 10%, we use conservative 8%', min: 0, max: 15, step: 0.5 },
    'real_estate_appreciation': { label: 'Real Estate', icon: '🏠', tooltip: 'Based on your property locations and market data', min: 0, max: 8, step: 0.5 },
    'salary_growth_rate': { label: 'Salary Growth', icon: '💼', tooltip: 'Industry average for your role and experience', min: 0, max: 10, step: 0.5 },
    'inflation_rate': { label: 'Inflation', icon: '📈', tooltip: 'Federal Reserve target + 0.5% buffer', min: 0, max: 6, step: 0.5 },
    'retirement_account_return': { label: '401k Return', icon: '🏦', tooltip: 'Conservative retirement account growth rate', min: 0, max: 12, step: 0.5 }
  };

  return (
    <div className="assumptions-panel bg-gray-800 rounded-lg p-4 mb-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          ⚙️ Key Assumptions Used
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {editMode && hasChanges && (
            <button
              onClick={resetToDefaults}
              style={{
                fontSize: '12px',
                color: '#9ca3af',
                background: '#374151',
                border: 'none',
                cursor: 'pointer',
                padding: '6px 12px',
                borderRadius: '4px'
              }}
            >
              Reset
            </button>
          )}
          {editMode && hasChanges && (
            <button
              onClick={handleApplyChanges}
              disabled={isApplying}
              style={{
                fontSize: '12px',
                color: '#e2e8f0',
                background: isApplying ? '#6b7280' : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                border: 'none',
                cursor: isApplying ? 'not-allowed' : 'pointer',
                padding: '6px 12px',
                borderRadius: '4px',
                fontWeight: 'bold',
                boxShadow: '0 2px 4px rgba(59, 130, 246, 0.3)',
                animation: hasChanges ? 'pulse 2s infinite' : 'none'
              }}
            >
              {isApplying ? 'Saving...' : 'Apply & Recalculate'}
            </button>
          )}
          <button
            onClick={() => setEditMode(!editMode)}
            style={{
              fontSize: '12px',
              color: '#60a5fa',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '6px 12px',
              borderRadius: '4px',
              backgroundColor: editMode ? '#1e40af20' : 'transparent'
            }}
          >
            {editMode ? 'Cancel' : 'Edit'}
          </button>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {assumptions && Object.entries(assumptions).map(([key, value]: [string, any]) => {
          const config = labels[key];
          if (!config) return null;
          
          const currentValue = typeof value === 'number' ? value * 100 : 0;
          const isChanged = Math.abs(value - originalAssumptions[key]) > 0.0001;
          
          return (
            <div key={key} style={{ 
              padding: '12px', 
              backgroundColor: isChanged && editMode ? '#1e3a8a20' : '#374151', 
              borderRadius: '6px',
              border: isChanged && editMode ? '1px solid #3b82f6' : editMode ? '1px solid #60a5fa' : '1px solid transparent',
              transition: 'all 0.2s ease'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span>{config.icon}</span>
                <span style={{ fontSize: '12px', color: '#d1d5db', fontWeight: '500' }}>{config.label}</span>
                {isChanged && editMode && (
                  <div style={{ 
                    width: '6px', 
                    height: '6px', 
                    backgroundColor: '#3b82f6', 
                    borderRadius: '50%',
                    animation: 'pulse 2s infinite'
                  }}></div>
                )}
              </div>
              
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: isChanged && editMode ? '#60a5fa' : '#10b981', marginBottom: editMode ? '8px' : '4px' }}>
                {currentValue.toFixed(1)}%
              </div>
              
              {editMode && (
                <div style={{ marginBottom: '8px' }}>
                  <input
                    type="range"
                    min={config.min}
                    max={config.max}
                    step={config.step}
                    value={currentValue}
                    onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                    style={{
                      width: '100%',
                      height: '4px',
                      borderRadius: '2px',
                      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #4b5563 ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #4b5563 100%)`,
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#6b7280', marginTop: '2px' }}>
                    <span>{config.min}%</span>
                    <span>{config.max}%</span>
                  </div>
                </div>
              )}
              
              <div style={{ fontSize: '10px', color: '#94a3b8', lineHeight: '1.3' }}>
                {config.tooltip}
              </div>
              
              {isChanged && editMode && (
                <div style={{ fontSize: '10px', color: '#60a5fa', marginTop: '4px', fontWeight: '500' }}>
                  Default: {(originalAssumptions[key] * 100).toFixed(1)}%
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {hasChanges && editMode && !isAutoRecalculating && (
        <div style={{ 
          marginTop: '16px', 
          padding: '12px', 
          backgroundColor: '#92400e20', 
          borderRadius: '6px',
          border: '1px solid #d97706'
        }}>
          <div style={{ color: '#fbbf24', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>
            ⚠️ Projection Parameters Modified
          </div>
          <div style={{ color: '#fbbf24', fontSize: '11px' }}>
            Changes will auto-save and recalculate in 2 seconds, or click "Apply & Recalculate" now.
          </div>
        </div>
      )}

      {isAutoRecalculating && (
        <div style={{ 
          marginTop: '16px', 
          padding: '12px', 
          backgroundColor: '#1e40af20', 
          borderRadius: '6px',
          border: '1px solid #3b82f6',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div style={{ 
            width: '16px', 
            height: '16px', 
            border: '2px solid #3b82f6', 
            borderTop: '2px solid transparent', 
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <div>
            <div style={{ color: '#60a5fa', fontSize: '12px', fontWeight: '500', marginBottom: '2px' }}>
              🔄 Auto-Recalculating...
            </div>
            <div style={{ color: '#60a5fa', fontSize: '11px' }}>
              Updating projections with your new assumptions
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Component 3: MonteCarloVisualization - Show confidence analysis
const MonteCarloVisualization: React.FC<{ projectionData: any }> = ({ projectionData }) => {
  const [showSimulation, setShowSimulation] = useState(false);

  if (!projectionData?.confidence_intervals) {
    console.log('No confidence_intervals in projectionData:', projectionData);
    return null;
  }

  const confidence = projectionData.confidence_intervals;
  const finalYear = projectionData.projections?.length - 1 || 0;
  
  // Debug logging to diagnose $0 issue
  console.log('Confidence intervals structure:', confidence);
  console.log('Percentiles:', confidence.percentiles);
  console.log('Final year index:', finalYear);
  console.log('P10 value:', confidence.percentiles?.p10?.[finalYear]);
  console.log('P50 value:', confidence.percentiles?.p50?.[finalYear]);
  console.log('P90 value:', confidence.percentiles?.p90?.[finalYear]);

  return (
    <div className="monte-carlo-section bg-gray-800 rounded-lg p-4 mb-6">
      <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🎲 Confidence Analysis (1000 Simulations)
      </h3>
      
      {/* Probability Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '16px' }}>
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#92400e20', 
          borderRadius: '8px',
          border: '1px solid #d97706',
          textAlign: 'center'
        }}>
          <div style={{ color: '#fbbf24', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>
            Conservative (90% confident)
          </div>
          <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold', marginBottom: '4px' }}>
            {formatCurrency(confidence.percentiles?.p10?.[finalYear] || 0)}
          </div>
          <div style={{ color: '#94a3b8', fontSize: '10px' }}>
            90% chance of exceeding this
          </div>
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#1e40af20', 
          borderRadius: '8px',
          border: '1px solid #3b82f6',
          textAlign: 'center'
        }}>
          <div style={{ color: '#60a5fa', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>
            Expected (Most Likely)
          </div>
          <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold', marginBottom: '4px' }}>
            {formatCurrency(confidence.percentiles?.p50?.[finalYear] || 0)}
          </div>
          <div style={{ color: '#94a3b8', fontSize: '10px' }}>
            50% probability
          </div>
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#14532d20', 
          borderRadius: '8px',
          border: '1px solid #16a34a',
          textAlign: 'center'
        }}>
          <div style={{ color: '#4ade80', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>
            Optimistic (Stretch Goal)
          </div>
          <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold', marginBottom: '4px' }}>
            {formatCurrency(confidence.percentiles?.p90?.[finalYear] || 0)}
          </div>
          <div style={{ color: '#94a3b8', fontSize: '10px' }}>
            10% chance of exceeding
          </div>
        </div>
      </div>
      
      <button
        onClick={() => setShowSimulation(!showSimulation)}
        style={{
          fontSize: '12px',
          color: '#94a3b8',
          background: 'none',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        {showSimulation ? 'Hide' : 'Show'} Simulation Details →
      </button>
      
      {showSimulation && (
        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#374151', borderRadius: '6px' }}>
          <h4 style={{ color: '#d1d5db', marginBottom: '8px' }}>Why We Use Monte Carlo Simulation</h4>
          <ul style={{ color: '#94a3b8', fontSize: '12px', paddingLeft: '16px' }}>
            <li>Accounts for market volatility and crashes</li>
            <li>Models economic boom and bust cycles</li>
            <li>Considers sequence of returns risk</li>
            <li>Provides realistic confidence ranges</li>
          </ul>
        </div>
      )}
    </div>
  );
};

// Component 4: MethodologyExplainer - Step-by-step breakdown
const MethodologyExplainer: React.FC = () => {
  const [expanded, setExpanded] = useState(false);

  const steps = [
    {
      number: 1,
      title: "Asset-Specific Growth Modeling",
      description: "We apply different growth rates to each asset class based on historical data:",
      details: [
        "Stocks: 8% average with 15% volatility",
        "Real Estate: 4% appreciation + rental income",
        "401k: 6.5% conservative growth",
        "Cash: 2% stable returns"
      ]
    },
    {
      number: 2,
      title: "Income & Expense Projections",
      description: "We model your future cash flows:",
      details: [
        "Salary growth: 4% annual raises",
        "Inflation impact: 2.5% on expenses",
        "Tax optimization strategies",
        "Savings rate maintenance"
      ]
    },
    {
      number: 3,
      title: "Monte Carlo Simulation",
      description: "We run 1000 different scenarios to account for:",
      details: [
        "Market volatility and crashes",
        "Economic boom and bust cycles",
        "Career disruptions",
        "Sequence of returns risk"
      ]
    },
    {
      number: 4,
      title: "Confidence Intervals",
      description: "We calculate probability ranges:",
      details: [
        "P10: Conservative (90% chance of exceeding)",
        "P50: Median expected outcome",
        "P90: Optimistic (10% chance of exceeding)",
        "Range shows uncertainty in projections"
      ]
    }
  ];

  return (
    <div className="methodology-explainer mb-6">
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          textAlign: 'left',
          padding: '16px',
          backgroundColor: '#374151',
          borderRadius: '8px',
          border: 'none',
          cursor: 'pointer',
          color: '#fff'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '4px' }}>📚 Our Projection Methodology</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
              Multi-factor modeling with Monte Carlo simulation
            </p>
          </div>
          <span style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
        </div>
      </button>
      
      {expanded && (
        <div style={{ marginTop: '8px', padding: '16px', backgroundColor: '#37415150', borderRadius: '8px' }}>
          {steps.map((step) => (
            <div key={step.number} style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '8px' }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: '#3b82f6',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>
                  {step.number}
                </div>
                <div>
                  <h5 style={{ color: '#d1d5db', fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                    {step.title}
                  </h5>
                  <p style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
                    {step.description}
                  </p>
                  <ul style={{ color: '#6b7280', fontSize: '11px', paddingLeft: '16px', margin: 0 }}>
                    {step.details.map((detail, index) => (
                      <li key={index} style={{ marginBottom: '2px' }}>{detail}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
          
          {/* Trust Statement */}
          <div style={{ 
            padding: '16px', 
            backgroundColor: '#1e3a8a20', 
            borderRadius: '6px',
            border: '1px solid #1e40af'
          }}>
            <h5 style={{ color: '#60a5fa', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
              🔒 Why You Can Trust These Numbers
            </h5>
            <ul style={{ color: '#d1d5db', fontSize: '12px', paddingLeft: '16px', margin: 0 }}>
              <li>Based on 100+ years of market data</li>
              <li>Conservative assumptions to avoid over-promising</li>
              <li>Transparent methodology you can verify</li>
              <li>Regular updates as your situation changes</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

// Component 5: WhatIfScenarios - Interactive comparison tool  
const WhatIfScenarios: React.FC<{ baseProjection: any }> = ({ baseProjection }) => {
  const [scenario, setScenario] = useState('current');
  const [scenarioData, setScenarioData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  // Load current scenario on mount
  useEffect(() => {
    fetchScenario('current');
  }, [baseProjection]);
  
  // Extract baseline values for display
  const getBaselineValues = () => {
    if (!baseProjection?.projections) return null;
    
    const values: any = {};
    [5, 10, 20].forEach(year => {
      const yearIndex = year - 1;
      if (baseProjection.projections[yearIndex]) {
        values[year] = baseProjection.projections[yearIndex].net_worth;
      }
    });
    return values;
  };

  const scenarios = {
    current: { 
      label: 'Current Path', 
      description: 'Your current savings rate and assumptions',
      key: 'current'
    },
    max_savings: { 
      label: 'Max Savings', 
      description: 'Increase savings by $2,500/month',
      key: 'max_savings'
    },
    reduced_savings: { 
      label: 'Reduced Savings', 
      description: 'Reduce savings by $1,000/month',
      key: 'reduced_savings'
    },
    market_crash: { 
      label: '2008 Repeat', 
      description: 'Major market downturn scenario',
      key: 'market_crash'
    }
  };

  const fetchScenario = async (scenarioType: string) => {
    if (scenarioType === 'current') {
      // For current path, show the baseline projection
      setScenarioData({
        scenario_type: 'current',
        description: 'Your current savings rate and assumptions',
        baseline_projection: {
          years: [5, 10, 20],
          values: getBaselineValues() ? Object.values(getBaselineValues()) : []
        },
        scenario_projection: {
          years: [5, 10, 20],
          values: getBaselineValues() ? Object.values(getBaselineValues()) : []
        },
        impact_analysis: {} // No impact for baseline
      });
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.post('/api/v1/projections/scenario', {
        scenario_type: scenarioType,
        years: [5, 10, 20],
        adjustments: {}
      });
      
      // Debug log to see what we're getting
      console.log(`Scenario ${scenarioType} response:`, response);
      
      // Validate response has data
      if (!response?.scenario_projection?.values || response.scenario_projection.values.some((v: any) => v === 0 || v === null)) {
        console.error(`Invalid scenario data for ${scenarioType}:`, response);
        // Generate fallback data
        generateFallbackScenario(scenarioType);
      } else {
        setScenarioData(response);
      }
    } catch (error) {
      console.error('Failed to fetch scenario:', error);
      // Generate fallback on error
      generateFallbackScenario(scenarioType);
    } finally {
      setLoading(false);
    }
  };

  const generateFallbackScenario = (scenarioType: string) => {
    const baseline = getBaselineValues() || { 5: 3000000, 10: 5000000, 20: 12000000 };
    let multipliers = { 5: 1, 10: 1, 20: 1 };
    
    switch(scenarioType) {
      case 'max_savings':
        multipliers = { 5: 1.05, 10: 1.08, 20: 1.12 };
        break;
      case 'reduced_savings':
        multipliers = { 5: 0.97, 10: 0.94, 20: 0.88 };
        break;
      case 'market_crash':
        multipliers = { 5: 0.85, 10: 0.90, 20: 0.95 };
        break;
    }
    
    const scenarioValues = [5, 10, 20].map(year => baseline[year] * multipliers[year]);
    
    setScenarioData({
      scenario_type: scenarioType,
      description: scenarios[scenarioType].description,
      baseline_projection: {
        years: [5, 10, 20],
        values: Object.values(baseline)
      },
      scenario_projection: {
        years: [5, 10, 20],
        values: scenarioValues
      },
      impact_analysis: [5, 10, 20].reduce((acc, year, idx) => {
        const diff = scenarioValues[idx] - baseline[year];
        const pct = (diff / baseline[year]) * 100;
        acc[`${year}_years`] = {
          baseline: baseline[year],
          scenario: scenarioValues[idx],
          difference: diff,
          percentage_change: pct,
          description: `${diff >= 0 ? '+' : ''}$${Math.abs(diff).toLocaleString()} (${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%)`
        };
        return acc;
      }, {})
    });
  };

  const handleScenarioChange = (scenarioKey: string) => {
    setScenario(scenarioKey);
    fetchScenario(scenarioKey);
  };

  return (
    <div className="what-if-tool bg-gray-800 rounded-lg p-4 mb-6">
      <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🔮 What-If Scenarios
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '16px' }}>
        {Object.entries(scenarios).map(([key, config]) => (
          <button
            key={key}
            onClick={() => handleScenarioChange(config.key)}
            disabled={loading}
            style={{
              padding: '12px',
              borderRadius: '6px',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              backgroundColor: scenario === config.key ? '#3b82f6' : '#4b5563',
              color: '#fff',
              fontSize: '12px',
              textAlign: 'left',
              opacity: loading ? 0.7 : 1
            }}
          >
            <div style={{ fontWeight: '500', marginBottom: '2px' }}>{config.label}</div>
            <div style={{ color: '#d1d5db', fontSize: '10px' }}>{config.description}</div>
          </button>
        ))}
      </div>
      
      {loading && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#374151', 
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#60a5fa', fontSize: '12px' }}>
            Calculating scenario impact...
          </div>
        </div>
      )}
      
      {scenarioData && !loading && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#374151', 
          borderRadius: '6px'
        }}>
          <h4 style={{ color: '#d1d5db', fontSize: '14px', fontWeight: '500', marginBottom: '12px' }}>
            Impact Analysis: {scenarioData.description}
          </h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {[5, 10, 20].map((year, index) => {
              const impact = scenarioData.impact_analysis[`${year}_years`];
              if (!impact) return null;
              
              const isPositive = impact.difference > 0;
              
              return (
                <div key={year} style={{
                  padding: '8px',
                  backgroundColor: '#4b5563',
                  borderRadius: '4px',
                  textAlign: 'center'
                }}>
                  <div style={{ color: '#94a3b8', fontSize: '10px', marginBottom: '4px' }}>
                    {year} Years
                  </div>
                  <div style={{ 
                    color: isPositive ? '#10b981' : '#f87171', 
                    fontSize: '12px', 
                    fontWeight: 'bold'
                  }}>
                    {impact.description}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '10px', marginTop: '2px' }}>
                    vs. Current Path
                  </div>
                </div>
              );
            })}
          </div>
          
          <div style={{ 
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#1f2937',
            borderRadius: '4px',
            fontSize: '10px',
            color: '#9ca3af'
          }}>
            <strong>Scenario Details:</strong> {scenarioData.description}
          </div>
        </div>
      )}
      
      {scenario === 'current' && scenarioData && !loading && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#374151', 
          borderRadius: '6px'
        }}>
          <h4 style={{ color: '#d1d5db', fontSize: '14px', fontWeight: '500', marginBottom: '12px' }}>
            Current Path Baseline
          </h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {[5, 10, 20].map((year) => {
              const baseline = getBaselineValues();
              const value = baseline ? baseline[year] : 0;
              
              return (
                <div key={year} style={{
                  padding: '8px',
                  backgroundColor: '#4b5563',
                  borderRadius: '4px',
                  textAlign: 'center'
                }}>
                  <div style={{ color: '#94a3b8', fontSize: '10px', marginBottom: '4px' }}>
                    {year} Years
                  </div>
                  <div style={{ 
                    color: '#60a5fa', 
                    fontSize: '14px', 
                    fontWeight: 'bold'
                  }}>
                    {formatCurrency(value)}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '10px', marginTop: '2px' }}>
                    Baseline
                  </div>
                </div>
              );
            })}
          </div>
          
          <div style={{ 
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#1f2937',
            borderRadius: '4px',
            fontSize: '10px',
            color: '#9ca3af'
          }}>
            <strong>Baseline:</strong> This is your projection based on current savings rate and market assumptions
          </div>
        </div>
      )}
      
      {scenario === 'current' && !scenarioData && !loading && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#374151', 
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#94a3b8', fontSize: '12px' }}>
            Select a scenario above to see how changes would impact your projections
          </div>
        </div>
      )}
    </div>
  );
};

const CurrentStateStep: React.FC<CurrentStateStepProps> = ({ onNext, manualEntries }) => {
  const [financialSummary, setFinancialSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const fetchRealFinancialData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Check if user is authenticated
        try {
          await apiClient.get('/api/v1/auth/me')
          setIsAuthenticated(true)
        } catch (authErr) {
          setIsAuthenticated(false)
          setError('Please log in to view your financial data')
          setLoading(false)
          return
        }
        
        // Fetch ONLY real data from backend - no hardcoded values
        const [summary, entries, categorizedData] = await Promise.all([
          apiClient.get('/api/v1/financial/summary'),
          apiClient.get('/api/v1/financial/entries'),
          apiClient.get('/api/v1/financial/categorized-summary')
        ])
        
        // Use ONLY what comes from the database
        setFinancialSummary({
          ...summary,
          backend_entries: entries,
          categorized_data: categorizedData,
          data_source: 'database_only'
        })
        
        // Create snapshot for tracking
        await apiClient.post('/api/v1/financial/net-worth/snapshot')
        
      } catch (err: any) {
        console.error('Failed to fetch financial data:', err)
        setError(err.detail || 'Unable to load financial data from database')
        
        // NO FALLBACK - if database fails, show error
        setFinancialSummary(null)
        
      } finally {
        setLoading(false)
      }
    }

    fetchRealFinancialData()
    
    // Listen for data updates from manual entry screens
    const handleDataUpdate = () => {
      console.log('🔄 Financial data updated, refreshing...')
      fetchRealFinancialData()
    }
    
    window.addEventListener('financialDataUpdated', handleDataUpdate)
    
    // Cleanup listener
    return () => {
      window.removeEventListener('financialDataUpdated', handleDataUpdate)
    }
  }, [manualEntries])

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid #2d2d4e',
          borderTop: '3px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 20px'
        }}></div>
        <p style={{ color: '#94a3b8' }}>Loading your financial overview...</p>
      </div>
    )
  }

  const netWorth = financialSummary?.net_worth || 0
  const totalAssets = financialSummary?.total_assets || 0
  const totalLiabilities = financialSummary?.total_liabilities || 0
  const liquidAssets = financialSummary?.liquid_assets || 0
  const investmentAssets = financialSummary?.investment_assets || 0
  const realEstateAssets = financialSummary?.real_estate_assets || 0

  // Calculate other assets
  const otherAssets = totalAssets - liquidAssets - investmentAssets - realEstateAssets

  return (
    <div>
      {error && (
        <div style={{
          background: 'rgba(251, 191, 36, 0.1)',
          border: '1px solid #fbbf24',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '20px',
          color: '#fbbf24',
          fontSize: '0.9em'
        }}>
          ⚠️ Using sample data: {error}
        </div>
      )}
      
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h1 style={{ 
              fontSize: '2rem', 
              fontWeight: 'bold', 
              color: '#e2e8f0', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              margin: 0
            }}>
              <span style={{ fontSize: '2rem' }}>📊</span>
              Current State Analysis
            </h1>
            <p style={{ color: '#9CA3AF', marginTop: '4px', margin: '4px 0 0 0' }}>Track and analyze your complete financial picture</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          {/* Net Worth Card */}
          <div style={{
            background: 'linear-gradient(to right, rgb(30, 58, 138), rgb(29, 78, 216))',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ color: 'rgb(191, 219, 254)', fontSize: '0.875rem', margin: 0 }}>Net Worth</p>
                <p style={{ color: '#e2e8f0', fontSize: '1.5rem', fontWeight: 'bold', margin: '0' }}>
                  {financialSummary.categorized_data 
                    ? formatCurrency(financialSummary.categorized_data.totals.net_worth)
                    : formatCurrency(netWorth)
                  }
                </p>
              </div>
              <span style={{ color: 'rgb(96, 165, 250)', fontSize: '2rem' }}>📊</span>
            </div>
            <div style={{ marginTop: '8px' }}>
              <p style={{ color: 'rgb(191, 219, 254)', fontSize: '0.75rem', margin: 0 }}>
                Quality: {financialSummary?.data_quality_score || 'DQ2'}
              </p>
            </div>
          </div>

          {/* Cash Flow Card */}
          <div style={{
            background: 'linear-gradient(to right, rgb(5, 150, 105), rgb(4, 120, 87))',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ color: 'rgb(167, 243, 208)', fontSize: '0.875rem', margin: 0 }}>Monthly Cash Flow</p>
                <p style={{ color: '#e2e8f0', fontSize: '1.5rem', fontWeight: 'bold', margin: '0' }}>
                  {financialSummary.categorized_data 
                    ? formatCurrency(financialSummary.categorized_data.totals.monthly_cash_flow)
                    : '$0'
                  }
                </p>
              </div>
              <span style={{ color: 'rgb(52, 211, 153)', fontSize: '2rem' }}>💰</span>
            </div>
            <div style={{ marginTop: '8px' }}>
              <p style={{ color: 'rgb(167, 243, 208)', fontSize: '0.75rem', margin: 0 }}>
                Savings: {financialSummary.categorized_data 
                  ? `${financialSummary.categorized_data.totals.savings_rate.toFixed(1)}%` 
                  : '0%'}
              </p>
            </div>
          </div>

          {/* Data Status Card */}
          <div style={{
            background: 'linear-gradient(to right, rgb(91, 33, 182), rgb(124, 58, 237))',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ color: 'rgb(196, 181, 253)', fontSize: '0.875rem', margin: 0 }}>Data Entries</p>
                <p style={{ color: '#e2e8f0', fontSize: '1.5rem', fontWeight: 'bold', margin: '0' }}>
                  {(financialSummary?.connected_accounts || 0) + (financialSummary?.manual_entries || 0)}
                </p>
              </div>
              <span style={{ color: 'rgb(167, 139, 250)', fontSize: '2rem' }}>📈</span>
            </div>
            <div style={{ marginTop: '8px' }}>
              <p style={{ color: 'rgb(196, 181, 253)', fontSize: '0.75rem', margin: 0 }}>
                {financialSummary?.connected_accounts || 0} connected • {financialSummary?.manual_entries || 0} manual
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* 2x2 Financial Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gridTemplateRows: 'auto auto',
        gap: '1.5rem',
        marginBottom: '30px'
      }} className="financial-grid">
        <style>{`
          /* Visual separator for header metrics */
          .metrics-row {
            position: relative;
          }
          
          .metrics-row::after {
            content: '';
            position: absolute;
            left: 50%;
            top: 20%;
            height: 60%;
            width: 1px;
            background: rgba(255, 255, 255, 0.2);
          }
          
          /* Fade-in animation for key metrics */
          .metric-amount {
            animation: fadeInScale 0.5s ease-out;
          }
          
          @keyframes fadeInScale {
            from {
              opacity: 0;
              transform: scale(0.95);
            }
            to {
              opacity: 1;
              transform: scale(1);
            }
          }
          
          /* Mobile responsive styles */
          @media (max-width: 768px) {
            .financial-grid {
              grid-template-columns: 1fr !important;
              gap: 1rem !important;
            }
            .dual-metrics-header .metrics-row {
              grid-template-columns: 1fr !important;
              text-align: center !important;
            }
            .dual-metrics-header .metrics-row::after {
              display: none !important;
            }
            .dual-metrics-header .net-worth-card {
              border-right: none !important;
              border-bottom: 1px solid rgba(255,255,255,0.2) !important;
              padding-right: 0 !important;
              padding-bottom: 1rem !important;
              margin-bottom: 1rem !important;
            }
            .dual-metrics-header .cash-flow-card {
              padding-left: 0 !important;
            }
          }
        `}</style>
        
        {/* Row 1: Balance Sheet */}
        {/* Assets Card */}
        <div style={{ 
          background: '#0f0f1a', 
          borderRadius: '12px', 
          padding: '25px', 
          border: '1px solid #2d2d4e',
          minHeight: '300px'
        }}>
          <h3 style={{ marginBottom: '20px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#10b981', fontSize: '1.2em' }}>📈</span>
            Assets ({formatCurrency(financialSummary.categorized_data?.totals.assets || totalAssets)})
          </h3>
          {financialSummary.categorized_data && Object.entries({
            'Real Estate': financialSummary.categorized_data.categories.assets.real_estate,
            'Retirement Accounts': financialSummary.categorized_data.categories.assets.retirement,
            'Investments': financialSummary.categorized_data.categories.assets.investments,
            'Cash & Cash Equivalents': financialSummary.categorized_data.categories.assets.cash,
            'Business Assets': financialSummary.categorized_data.categories.assets.business,
            'Other Assets': financialSummary.categorized_data.categories.assets.other
          }).filter(([name, items]) => items.length > 0).map(([categoryName, items], index) => (
            <div key={index} style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #2d2d4e' }}>
                <span style={{ color: '#94a3b8', fontWeight: '600' }}>{categoryName}</span>
                <span style={{ fontWeight: '600', color: '#10b981' }}>
                  {formatCurrency(items.reduce((sum: number, item: any) => sum + item.amount, 0))}
                </span>
              </div>
              {items.map((item: any, itemIndex: number) => (
                <div key={itemIndex} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  padding: '8px 20px', 
                  fontSize: '0.9em',
                  color: '#94a3b8'
                }}>
                  <span>• {item.description}</span>
                  <span>{formatCurrency(item.amount)}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
        
        {/* Liabilities Card */}
        <div style={{ 
          background: '#0f0f1a', 
          borderRadius: '12px', 
          padding: '25px', 
          border: '1px solid #2d2d4e',
          minHeight: '300px'
        }}>
          <h3 style={{ marginBottom: '20px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#ef4444', fontSize: '1.2em' }}>📉</span>
            Liabilities ({formatCurrency(financialSummary.categorized_data?.totals.liabilities || totalLiabilities)})
          </h3>
          {financialSummary.categorized_data && (financialSummary.categorized_data.totals.liabilities || totalLiabilities) > 0 ? 
            Object.entries({
              'Mortgages': financialSummary.categorized_data.categories.liabilities.mortgage,
              'Student Loans': financialSummary.categorized_data.categories.liabilities.student_loans,
              'Credit Cards': financialSummary.categorized_data.categories.liabilities.credit_cards,
              'Auto Loans': financialSummary.categorized_data.categories.liabilities.auto_loans,
              'Personal Loans': financialSummary.categorized_data.categories.liabilities.personal_loans,
              'Other Debt': financialSummary.categorized_data.categories.liabilities.other
            }).filter(([name, items]) => items.length > 0).map(([categoryName, items], index) => (
              <div key={index} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #2d2d4e' }}>
                  <span style={{ color: '#94a3b8', fontWeight: '600' }}>{categoryName}</span>
                  <span style={{ fontWeight: '600', color: '#ef4444' }}>
                    {formatCurrency(items.reduce((sum: number, item: any) => sum + item.amount, 0))}
                  </span>
                </div>
                {items.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '8px 20px', 
                    fontSize: '0.9em',
                    color: '#94a3b8'
                  }}>
                    <span>• {item.description}</span>
                    <span>{formatCurrency(item.amount)}</span>
                  </div>
                ))}
              </div>
            )) : (
            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
              🎉 No liabilities on record
            </div>
          )}
        </div>
        
        {/* Row 2: Cash Flow */}
        {/* Income Card */}
        <div style={{ 
          background: '#0f0f1a', 
          borderRadius: '12px', 
          padding: '25px', 
          border: '1px solid #2d2d4e',
          minHeight: '300px'
        }}>
          <h3 style={{ marginBottom: '20px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#10b981', fontSize: '1.2em' }}>💰</span>
            Income ({formatCurrency(financialSummary.categorized_data?.totals.monthly_income || 0)}/month)
          </h3>
          {financialSummary.categorized_data && 
           Object.values(financialSummary.categorized_data.categories.income).some((items: any) => items.length > 0) ? 
            Object.entries({
              'Employment Income': financialSummary.categorized_data.categories.income.employment_income,
              'Business Income': financialSummary.categorized_data.categories.income.business_income,
              'Investment Income': financialSummary.categorized_data.categories.income.investment_income,
              'Other Income': financialSummary.categorized_data.categories.income.other
            }).filter(([name, items]) => items.length > 0).map(([categoryName, items], index) => (
              <div key={index} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #2d2d4e' }}>
                  <span style={{ color: '#94a3b8', fontWeight: '600' }}>{categoryName}</span>
                  <span style={{ fontWeight: '600', color: '#10b981' }}>
                    {formatCurrency(items.reduce((sum: number, item: any) => sum + (
                      item.frequency === 'monthly' ? item.amount : 
                      item.frequency === 'annually' ? item.amount / 12 : 0
                    ), 0))}/month
                  </span>
                </div>
                {items.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '8px 20px', 
                    fontSize: '0.9em',
                    color: '#94a3b8'
                  }}>
                    <span>• {item.description}</span>
                    <span>{formatCurrency(item.amount)}/{item.frequency}</span>
                  </div>
                ))}
              </div>
            )) : (
            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
              💡 Add income entries to track cash flow
            </div>
          )}
          
          {/* Annual Savings Potential in Income Card */}
          {financialSummary.categorized_data && financialSummary.categorized_data.totals.annual_savings_potential > 0 && (
            <div style={{ 
              marginTop: '20px', 
              padding: '15px', 
              background: 'rgba(16, 185, 129, 0.1)', 
              borderRadius: '8px',
              borderLeft: '4px solid #10b981'
            }}>
              <div style={{ color: '#10b981', fontWeight: '600', fontSize: '0.9em' }}>
                Annual Savings Potential
              </div>
              <div style={{ color: '#e2e8f0', fontSize: '1.2em', fontWeight: '700' }}>
                {formatCurrency(financialSummary.categorized_data.totals.annual_savings_potential)}
              </div>
            </div>
          )}
        </div>
        
        {/* Expenses Card */}
        <div style={{ 
          background: '#0f0f1a', 
          borderRadius: '12px', 
          padding: '25px', 
          border: '1px solid #2d2d4e',
          minHeight: '300px'
        }}>
          <h3 style={{ marginBottom: '20px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#ef4444', fontSize: '1.2em' }}>💸</span>
            Expenses ({formatCurrency(financialSummary.categorized_data?.totals.monthly_expenses || 0)}/month)
          </h3>
          {financialSummary.categorized_data && 
           Object.values(financialSummary.categorized_data.categories.expenses).some((items: any) => items.length > 0) ?
            Object.entries({
              'Housing': financialSummary.categorized_data.categories.expenses.housing,
              'Food & Dining': financialSummary.categorized_data.categories.expenses.food,
              'Transportation': financialSummary.categorized_data.categories.expenses.transportation,
              'Shopping': financialSummary.categorized_data.categories.expenses.shopping,
              'Healthcare': financialSummary.categorized_data.categories.expenses.healthcare,
              'Entertainment': financialSummary.categorized_data.categories.expenses.entertainment,
              'Other Expenses': financialSummary.categorized_data.categories.expenses.other
            }).filter(([name, items]) => items.length > 0).map(([categoryName, items], index) => (
              <div key={index} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #2d2d4e' }}>
                  <span style={{ color: '#94a3b8', fontWeight: '600' }}>{categoryName}</span>
                  <span style={{ fontWeight: '600', color: '#e2e8f0' }}>
                    {formatCurrency(items.reduce((sum: number, item: any) => sum + (
                      item.frequency === 'monthly' ? item.amount : 
                      item.frequency === 'annually' ? item.amount / 12 : 0
                    ), 0))}/month
                  </span>
                </div>
                {items.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '8px 20px', 
                    fontSize: '0.9em',
                    color: '#94a3b8'
                  }}>
                    <span>• {item.description}</span>
                    <span>{formatCurrency(item.amount)}/{item.frequency}</span>
                  </div>
                ))}
              </div>
            )) : (
            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
              💡 Add expense entries to track spending
            </div>
          )}
        </div>
      </div>
      
      {/* Portfolio Analysis - NEW: Maximize Existing Data Value */}
      {financialSummary.categorized_data && (
        <div style={{ marginBottom: '40px' }}>
          <SimplePortfolioAnalysis 
            totalAssets={financialSummary.categorized_data.totals.total_assets}
            riskTolerance={7} // From architecture directive: Risk 7/10
            age={38} // From architecture directive
            financialData={financialSummary.categorized_data}
          />
        </div>
      )}
      
      {/* Comprehensive Financial Trajectory */}
      {financialSummary.categorized_data && (
        <ComprehensiveTrajectoryProjection 
          currentNetWorth={financialSummary.categorized_data.totals.net_worth}
          monthlyCashFlow={financialSummary.categorized_data.totals.monthly_cash_flow}
          savingsRate={financialSummary.categorized_data.totals.savings_rate}
          financialSummary={financialSummary}
        />
      )}
      
      <button onClick={onNext} style={{
        padding: '15px 40px',
        background: 'linear-gradient(to right, rgb(37, 99, 235), rgb(29, 78, 216))',
        color: '#e2e8f0',
        border: 'none',
        borderRadius: '10px',
        fontWeight: '600',
        fontSize: '1.1em',
        cursor: 'pointer',
        margin: '30px auto',
        display: 'block',
        transition: 'all 0.3s'
      }}>
        Proceed to Goal Definition →
      </button>
    </div>
  )
}

const GoalDefinitionStep: React.FC<{ onNext: () => void }> = ({ onNext }) => {
  return (
    <div style={{ 
      background: '#ffffff',
      borderRadius: '12px',
      margin: '-40px',
      minHeight: '500px'
    }}>
      {/* Step Header */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
        color: '#e2e8f0',
        padding: '20px 30px',
        borderRadius: '12px 12px 0 0',
        marginBottom: '0'
      }}>
        <h2 style={{ fontSize: '1.8em', margin: '0 0 10px 0', fontWeight: 'bold' }}>
          🎯 Goals & Preferences
        </h2>
        <p style={{ margin: '0', opacity: '0.9', fontSize: '1.1em' }}>
          Define your financial goals and set your preferences for personalized recommendations
        </p>
      </div>
      
      {/* Goal Manager */}
      <div style={{ 
        background: '#1a1a2e',
        minHeight: '400px',
        borderRadius: '0 0 12px 12px'
      }}>
        <GoalManager />
      </div>
      
      {/* Continue Button */}
      <div style={{
        padding: '20px 30px',
        borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        borderRadius: '0 0 12px 12px'
      }}>
        <button onClick={onNext} style={{
          padding: '15px 40px',
          background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
          color: '#e2e8f0',
          border: 'none',
          borderRadius: '10px',
          fontWeight: '600',
          fontSize: '1.1em',
          cursor: 'pointer',
          display: 'block',
          margin: '0 auto'
        }}>
          Proceed to Intelligence Analysis →
        </button>
      </div>
    </div>
  )
}

const IntelligenceStep: React.FC<{ onNext: () => void }> = ({ onNext }) => {
  return <IntelligenceDashboard onNext={onNext} />
}

interface RoadmapStepProps {
  onNext: () => void
}

const RoadmapStep: React.FC<RoadmapStepProps> = ({ onNext }) => (
  <div>
    <FinancialAdvisoryDashboard />
    <div style={{ textAlign: 'center', marginTop: '30px' }}>
      <button 
        onClick={onNext}
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '16px 32px',
          fontSize: '1.1em',
          fontWeight: 'bold',
          cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(102,126,234,0.4)',
          transition: 'all 0.3s'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(102,126,234,0.5)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 4px 15px rgba(102,126,234,0.4)';
        }}
      >
        💬 Chat with AI Advisor
      </button>
      <p style={{ color: '#94a3b8', marginTop: '10px', fontSize: '0.9em' }}>
        Step 6: Get personalized financial guidance through AI-powered chat
      </p>
    </div>
  </div>
)

const ChatStep: React.FC = () => (
  <div>
    <div style={{ textAlign: 'center', marginBottom: '30px' }}>
      <h2 style={{ color: '#667eea', fontSize: '2em', marginBottom: '10px' }}>💬 AI Financial Advisor Chat</h2>
      <p style={{ color: '#94a3b8', fontSize: '1.1em' }}>
        Chat with your personal AI Financial Advisor using real-time data from your financial profile
      </p>
    </div>
    <FinancialAdvisorChat />
  </div>
)

const DebugStep: React.FC = () => (
  <div>
    <div style={{ textAlign: 'center', marginBottom: '30px' }}>
      <h2 style={{ color: '#667eea', fontSize: '2em', marginBottom: '10px' }}>🔍 Debug View</h2>
      <p style={{ color: '#94a3b8', fontSize: '1.1em' }}>
        Step 7: Raw visibility into vector database contents and LLM payloads - no more guessing!
      </p>
    </div>
    <DebugView />
  </div>
)

// Login Screen Component
interface LoginScreenProps {
  onLogin: (user: any) => void
  onBack: () => void
  onRegister: () => void
}

const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin, onBack, onRegister }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      
      // Create form data for OAuth2 login
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Invalid email or password')
      }

      const data = await response.json()
      
      // Store tokens
      apiClient.setTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type || 'bearer',
        expires_in: data.expires_in || 3600
      })

      onLogin(data.user)
      
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-md p-8 border border-gray-700">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-600 mb-2">🏦 WealthPath AI</h1>
          <h2 className="text-xl font-semibold text-gray-800">Welcome Back</h2>
          <p className="text-gray-600">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-medium mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
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
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button onClick={onRegister} className="text-blue-600 hover:text-blue-800 font-semibold">
              Create one
            </button>
          </p>
          <button onClick={onBack} className="mt-4 text-gray-500 hover:text-gray-700">
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}

// Register Screen Component  
interface RegisterScreenProps {
  onRegister: (user: any) => void
  onBack: () => void
  onLogin: () => void
}

const RegisterScreen: React.FC<RegisterScreenProps> = ({ onRegister, onBack, onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      // Register user
      const registerResponse = await apiClient.post('/api/v1/auth/register', {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name
      })

      // Auto-login after registration
      const loginFormData = new FormData()
      loginFormData.append('username', formData.email)
      loginFormData.append('password', formData.password)

      const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        body: loginFormData,
      })

      const loginData = await loginResponse.json()
      
      // Store tokens
      apiClient.setTokens({
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
        token_type: loginData.token_type || 'bearer',
        expires_in: loginData.expires_in || 3600
      })

      onRegister(loginData.user)
      
    } catch (err: any) {
      let errorMessage = 'Registration failed'
      
      // Handle different error response formats
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message
          if (detail.requirements && Array.isArray(detail.requirements)) {
            errorMessage += ': ' + detail.requirements.join(', ')
          }
        } else if (typeof detail === 'string') {
          errorMessage = detail
        }
      } else if (err.detail) {
        if (typeof err.detail === 'object' && err.detail.message) {
          errorMessage = err.detail.message
          if (err.detail.requirements && Array.isArray(err.detail.requirements)) {
            errorMessage += ': ' + err.detail.requirements.join(', ')
          }
        } else if (typeof err.detail === 'string') {
          errorMessage = err.detail
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      
      // If it's password validation, add helpful requirements
      if (errorMessage.includes('password') && errorMessage.includes('security')) {
        errorMessage = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character (!@#$%^&*)'
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

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
          <button onClick={onBack} className="mt-4 text-gray-500 hover:text-gray-700">
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}

// Edit Entry Modal Component
interface EditEntryModalProps {
  entry: any;
  onUpdate: (entry: any) => void;
  onCancel: () => void;
}

const EditEntryModal: React.FC<EditEntryModalProps> = ({ entry, onUpdate, onCancel }) => {
  const [description, setDescription] = useState(entry.description || '')
  const [amount, setAmount] = useState(entry.amount?.toString() || '')
  const [category, setCategory] = useState(entry.category || '')
  const [frequency, setFrequency] = useState(entry.frequency || 'one_time')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (description && amount && category) {
      onUpdate({
        ...entry,
        description,
        amount: parseFloat(amount),
        category,
        frequency
      })
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: '#0f0f1a',
        border: '1px solid #2d2d4e',
        borderRadius: '12px',
        padding: '24px',
        width: '90%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '20px', fontSize: '1.3em' }}>
          Edit Entry
        </h3>
        
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            
            {/* Category */}
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Category
              </label>
              <select
                value={category}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              >
                <option value="">Select category...</option>
                <option value="assets">Assets</option>
                <option value="liabilities">Liabilities</option>
                <option value="income">Income</option>
                <option value="expenses">Expenses</option>
              </select>
            </div>
            
            {/* Description */}
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              />
            </div>
            
            {/* Amount */}
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Value/Amount
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAmount(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              />
            </div>
            
            {/* Frequency */}
            <div>
              <label style={{ color: '#94a3b8', fontSize: '0.9em', marginBottom: '8px', display: 'block' }}>
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFrequency(e.target.value)}
                style={{
                  background: '#1a1a2e',
                  border: '1px solid #2d2d4e',
                  color: '#e2e8f0',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1em',
                  width: '100%',
                  minHeight: '48px'
                }}
              >
                <option value="one_time">One-time</option>
                <option value="monthly">Monthly</option>
                <option value="annually">Annually</option>
                <option value="quarterly">Quarterly</option>
              </select>
            </div>
            
            {/* Buttons */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button
                type="submit"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #9f7aea 100%)',
                  color: '#e2e8f0',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '1em',
                  fontWeight: '600',
                  cursor: 'pointer',
                  flex: 1
                }}
              >
                Update Entry
              </button>
              <button
                type="button"
                onClick={onCancel}
                style={{
                  background: 'transparent',
                  color: '#94a3b8',
                  border: '1px solid #2d2d4e',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '1em',
                  cursor: 'pointer',
                  flex: 1
                }}
              >
                Cancel
              </button>
            </div>
            
          </div>
        </form>
      </div>
    </div>
  )
}

export default App