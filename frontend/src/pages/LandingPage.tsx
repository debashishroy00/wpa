import React from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, Shield, Users, Star, ChartBar, Brain, 
  Target, Lightbulb, Rocket, Clock, CreditCard, CheckCircle 
} from 'lucide-react';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm z-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <ChartBar className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">WealthPath AI</span>
            </Link>
            <div className="flex items-center space-x-6">
              <a href="#features" className="text-gray-600 hover:text-gray-900 font-medium">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 font-medium">Pricing</a>
              <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium">Login</Link>
              <Link to="/register" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-blue-600 via-purple-600 to-purple-700">
        <div className="max-w-7xl mx-auto text-center text-white">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Your AI-Powered Financial Advisor
          </h1>
          <p className="text-xl md:text-2xl mb-8 opacity-95 max-w-3xl mx-auto">
            Transform your financial future with personalized AI insights and comprehensive planning.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <Link to="/register" className="bg-white text-blue-600 px-8 py-4 rounded-xl font-bold text-lg hover:shadow-xl transition transform hover:-translate-y-1">
              <Rocket className="inline-block mr-2 h-5 w-5" />
              Start Your Free Analysis
            </Link>
            <a href="#demo" className="border-2 border-white/30 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-white/10 transition">
              See How It Works
            </a>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-yellow-400" />
              <span>Bank-Level Security</span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-yellow-400" />
              <span>10,000+ Users</span>
            </div>
            <div className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-400" />
              <span>4.9/5 Rating</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <span className="bg-blue-100 text-blue-600 px-4 py-2 rounded-full text-sm font-semibold">
              Why Choose WealthPath AI
            </span>
            <h2 className="text-4xl font-bold text-gray-900 mt-4 mb-4">
              Everything You Need for Financial Success
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Comprehensive financial analysis and personalized recommendations.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <ChartBar className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Complete Analysis</h3>
              <p className="text-gray-600">360° view of your financial health with institutional-grade accuracy.</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Powered Insights</h3>
              <p className="text-gray-600">Machine learning algorithms provide personalized recommendations.</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Goal Tracking</h3>
              <p className="text-gray-600">Set and monitor financial milestones with intelligent progress tracking.</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lightbulb className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Smart Recommendations</h3>
              <p className="text-gray-600">Specific advice on tax optimization and wealth-building strategies.</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Enterprise Security</h3>
              <p className="text-gray-600">Bank-level encryption and zero-knowledge architecture.</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Market Intelligence</h3>
              <p className="text-gray-600">Real-time market insights based on your risk profile.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <span className="bg-blue-100 text-blue-600 px-4 py-2 rounded-full text-sm font-semibold">
              Early Access Pricing
            </span>
            <h2 className="text-4xl font-bold text-gray-900 mt-4 mb-4">
              Start Your Financial Journey Today
            </h2>
            <p className="text-xl text-gray-600">Join our early access program.</p>
          </div>
          
          <div className="max-w-md mx-auto">
            <div className="bg-white border-4 border-blue-600 rounded-3xl shadow-2xl p-8 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-yellow-500 text-white px-4 py-1 rounded-full font-bold text-sm">
                Limited Time
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Early Access</h3>
              <div className="text-5xl font-bold text-blue-600 mb-1">FREE</div>
              <p className="text-gray-600 mb-6">During beta • No credit card required</p>
              
              <ul className="space-y-3 mb-8">
                {[
                  'Complete financial analysis',
                  'AI investment recommendations',
                  'Retirement planning',
                  'Tax optimization',
                  '24/7 AI advisor chat',
                  'Portfolio rebalancing',
                  'Goal tracking',
                  'Bank-level security'
                ].map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Link to="/register" className="block w-full bg-blue-600 text-white text-center py-4 rounded-xl font-bold text-lg hover:bg-blue-700 transition">
                <Rocket className="inline-block mr-2 h-5 w-5" />
                Claim Your Free Access
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to Transform Your Financial Future?</h2>
          <p className="text-xl mb-8 opacity-95">Join thousands building wealth with AI-powered planning.</p>
          <Link to="/register" className="inline-flex items-center bg-white text-blue-600 px-8 py-4 rounded-xl font-bold text-lg hover:shadow-xl transition">
            <Rocket className="mr-2 h-5 w-5" />
            Get Early Access Now
          </Link>
          <div className="flex justify-center gap-6 mt-6 text-sm">
            <span className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Limited spots
            </span>
            <span className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              No credit card
            </span>
            <span className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              100% secure
            </span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex justify-center gap-6 mb-4 flex-wrap">
            <a href="/privacy" className="hover:text-gray-300">Privacy Policy</a>
            <a href="/terms" className="hover:text-gray-300">Terms of Service</a>
            <a href="/security" className="hover:text-gray-300">Security</a>
            <a href="mailto:support@smartfinanceadvisor.net" className="hover:text-gray-300">Contact</a>
            <a href="/help" className="hover:text-gray-300">Help Center</a>
          </div>
          <p className="text-gray-400 text-sm">© 2025 WealthPath AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;