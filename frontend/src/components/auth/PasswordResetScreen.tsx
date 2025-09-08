import React, { useState, useEffect } from 'react'
import { getApiBaseUrl } from '../../utils/getApiBaseUrl'

interface PasswordResetScreenProps {
  onBack: () => void
  onSuccess: () => void
}

const PasswordResetScreen: React.FC<PasswordResetScreenProps> = ({ onBack, onSuccess }) => {
  const [formData, setFormData] = useState({
    token: '',
    new_password: '',
    confirm_password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    // Extract token from URL hash
    const hash = window.location.hash.substring(1)
    const params = new URLSearchParams(hash.split('?')[1] || '')
    const token = params.get('token')
    
    if (token) {
      setFormData(prev => ({ ...prev, token }))
    }
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (error) setError(null)
  }

  const validateForm = () => {
    if (!formData.token.trim()) {
      setError('Invalid or missing reset token')
      return false
    }
    if (!formData.new_password.trim()) {
      setError('Password is required')
      return false
    }
    if (formData.new_password.length < 8) {
      setError('Password must be at least 8 characters long')
      return false
    }
    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match')
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/password-reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: formData.token,
          new_password: formData.new_password
        }),
      })

      if (response.ok) {
        setSuccess(true)
        setTimeout(() => {
          onSuccess()
        }, 2000)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Password reset failed')
      }
    } catch (err: any) {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold text-gray-100">
              Password Reset Successful
            </h2>
            <div className="mt-8 bg-green-900 border border-green-700 text-green-100 px-4 py-3 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Your password has been successfully reset. Redirecting to login...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-100">
            Reset Your Password
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Enter your new password below
          </p>
        </div>

        <div className="mt-8 bg-gray-800 border border-gray-700 py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Hidden token field for debugging */}
            {formData.token && (
              <div>
                <label className="block text-sm font-medium text-gray-300">
                  Reset Token (auto-filled)
                </label>
                <input
                  type="text"
                  name="token"
                  value={formData.token}
                  onChange={handleInputChange}
                  className="mt-1 appearance-none block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-gray-100 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  readOnly
                />
              </div>
            )}

            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-300">
                New Password
              </label>
              <div className="mt-1">
                <input
                  id="new_password"
                  name="new_password"
                  type="password"
                  required
                  value={formData.new_password}
                  onChange={handleInputChange}
                  className="appearance-none block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-gray-100 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your new password"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-300">
                Confirm Password
              </label>
              <div className="mt-1">
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  required
                  value={formData.confirm_password}
                  onChange={handleInputChange}
                  className="appearance-none block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-gray-100 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Confirm your new password"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded-lg">
                <div className="flex">
                  <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm">{error}</span>
                </div>
              </div>
            )}

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={onBack}
                className="flex-1 flex justify-center py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Back to Login
              </button>
              
              <button
                type="submit"
                disabled={loading}
                className="flex-1 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Resetting...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default PasswordResetScreen