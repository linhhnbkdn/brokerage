import type { Route } from "./+types/home";
import { useAuth } from "../hooks/useAuth";
import { useState, useEffect, useRef } from "react";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Brokerage Platform" },
    { name: "description", content: "Modern brokerage platform for trading and investments" },
  ];
}

export default function Home() {
  const { isLoggedIn, isLoading, userInfo, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                BrokerPro
              </h1>
            </div>
            <div className="flex items-center gap-4">
              {isLoggedIn ? (
                <>
                  <a href="/dashboard" className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">
                    Dashboard
                  </a>
                  <a href="/banking" className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">
                    Banking
                  </a>
                  
                  {/* User Avatar and Menu */}
                  <div className="relative" ref={userMenuRef}>
                    <button
                      onClick={() => setShowUserMenu(!showUserMenu)}
                      className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                        {userInfo?.email ? userInfo.email.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <div className="hidden md:block">
                        <div className="text-sm font-medium text-slate-900 dark:text-white">
                          {userInfo?.email ? userInfo.email.split('@')[0] : 'User'}
                        </div>
                      </div>
                    </button>
                    
                    {showUserMenu && (
                      <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50">
                        <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-700">
                          <div className="font-medium text-slate-900 dark:text-white">
                            {userInfo?.email ? userInfo.email.split('@')[0] : 'User'}
                          </div>
                          <div className="text-sm text-slate-500 dark:text-slate-400">
                            {userInfo?.email || 'user@example.com'}
                          </div>
                        </div>
                        <button 
                          onClick={logout}
                          className="flex items-center w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                        >
                          <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                          </svg>
                          Sign Out
                        </button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <a href="/login" className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">
                    Login
                  </a>
                  <a href="/register" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    Get Started
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-slate-900 dark:text-white mb-6">
            Trade Smarter, 
            <span className="text-blue-600 dark:text-blue-400"> Invest Better</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto mb-8">
            Access global markets with advanced trading tools, real-time analytics, 
            and institutional-grade security. Start your investment journey today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isLoggedIn ? (
              <>
                <a href="/dashboard" className="px-8 py-4 bg-blue-600 text-white text-lg font-medium rounded-lg hover:bg-blue-700 transition-all transform hover:scale-105 shadow-lg text-center">
                  Go to Dashboard
                </a>
                <a href="/banking" className="px-8 py-4 border-2 border-blue-600 text-blue-600 dark:text-blue-400 text-lg font-medium rounded-lg hover:bg-blue-600 hover:text-white transition-all text-center">
                  Manage Banking
                </a>
              </>
            ) : (
              <>
                <a href="/register" className="px-8 py-4 bg-blue-600 text-white text-lg font-medium rounded-lg hover:bg-blue-700 transition-all transform hover:scale-105 shadow-lg text-center">
                  Start Trading
                </a>
                <a href="/login" className="px-8 py-4 border-2 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 text-lg font-medium rounded-lg hover:border-blue-600 hover:text-blue-600 dark:hover:border-blue-400 dark:hover:text-blue-400 transition-colors text-center">
                  Sign In
                </a>
              </>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl p-8 border border-slate-200 dark:border-slate-700 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
              Real-Time Trading
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Execute trades instantly with real-time market data and advanced order types.
            </p>
          </div>

          <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl p-8 border border-slate-200 dark:border-slate-700 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
              Advanced Analytics
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Make informed decisions with comprehensive market analysis and portfolio insights.
            </p>
          </div>

          <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl p-8 border border-slate-200 dark:border-slate-700 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
              Bank-Level Security
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Your investments are protected with enterprise-grade security and encryption.
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-8 border border-slate-200 dark:border-slate-700">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">$2.5B+</div>
              <div className="text-slate-600 dark:text-slate-300">Assets Under Management</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">50K+</div>
              <div className="text-slate-600 dark:text-slate-300">Active Traders</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">99.9%</div>
              <div className="text-slate-600 dark:text-slate-300">Uptime</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600 dark:text-orange-400 mb-2">24/7</div>
              <div className="text-slate-600 dark:text-slate-300">Support</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-300 py-12 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white font-semibold mb-4">BrokerPro</h3>
              <p className="text-sm">
                Modern brokerage platform for the next generation of investors.
              </p>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4">Platform</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/trading" className="hover:text-white transition-colors">Trading</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Portfolio</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Analytics</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">API Docs</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Education</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Support</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700 mt-8 pt-8 text-center text-sm">
            <p>&copy; 2024 BrokerPro. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
