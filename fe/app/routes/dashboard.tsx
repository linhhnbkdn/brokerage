import type { Route } from "./+types/dashboard";
import { useAuth } from "../hooks/useAuth";
import { useState, useEffect, useRef } from "react";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard - BrokerPro" },
    { name: "description", content: "Your trading dashboard and portfolio overview" },
  ];
}

// Mock data for demonstration
const portfolioData = {
  totalValue: 125420.50,
  dailyChange: 2340.75,
  dailyChangePercent: 1.87,
  availableCash: 5432.10
};

const positions = [
  { symbol: "AAPL", name: "Apple Inc.", shares: 50, price: 175.23, change: 2.45, changePercent: 1.42 },
  { symbol: "GOOGL", name: "Alphabet Inc.", shares: 25, price: 2435.67, change: -12.33, changePercent: -0.50 },
  { symbol: "MSFT", name: "Microsoft Corp.", shares: 75, price: 378.92, change: 5.67, changePercent: 1.52 },
  { symbol: "TSLA", name: "Tesla Inc.", shares: 30, price: 245.18, change: -8.42, changePercent: -3.32 },
];

const watchlist = [
  { symbol: "NVDA", price: 423.45, change: 15.67, changePercent: 3.84 },
  { symbol: "AMD", price: 98.76, change: -2.34, changePercent: -2.32 },
  { symbol: "NFLX", price: 456.78, change: 8.90, changePercent: 1.99 },
];

export default function Dashboard() {
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

  // Add redirect logic here - always call hooks in same order
  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      window.location.href = '/login';
    }
  }, [isLoading, isLoggedIn]);

  // Early returns after all hooks are called
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                BrokerPro
              </h1>
              <div className="hidden md:flex items-center gap-6">
                <a href="/" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Home
                </a>
                <a href="/dashboard" className="text-blue-600 dark:text-blue-400 font-medium">
                  Dashboard
                </a>
                <a href="#" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Trading
                </a>
                <a href="#" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Research
                </a>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-700 dark:text-green-400">Market Open</span>
              </div>
              <button className="btn-primary">
                Quick Trade
              </button>
              
              {/* User Avatar and Menu */}
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                    {userInfo?.email ? userInfo.email.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="hidden md:block text-left">
                    <div className="text-sm font-medium text-slate-900 dark:text-white">
                      {userInfo?.email ? userInfo.email.split('@')[0] : 'User'}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      ID: {userInfo?.userId || 'N/A'}
                    </div>
                  </div>
                  <svg className="w-4 h-4 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </button>
                
                {/* Dropdown Menu */}
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
                    <a href="#" className="flex items-center px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700">
                      <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                      </svg>
                      Profile
                    </a>
                    <a href="#" className="flex items-center px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700">
                      <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      </svg>
                      Settings
                    </a>
                    <hr className="my-1 border-slate-200 dark:border-slate-700" />
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
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Portfolio Overview */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Portfolio Overview</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="trading-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Value</span>
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
              </div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                ${portfolioData.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>
            
            <div className="trading-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Today's Change</span>
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 17l9.2-9.2M17 17V7H7"></path>
                </svg>
              </div>
              <div className="text-2xl font-bold price-up">
                +${portfolioData.dailyChange.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
              <div className="text-sm price-up">
                +{portfolioData.dailyChangePercent}%
              </div>
            </div>
            
            <div className="trading-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Available Cash</span>
                <svg className="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"></path>
                </svg>
              </div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                ${portfolioData.availableCash.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>
            
            <div className="trading-card">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Quick Actions</span>
              </div>
              <div className="flex gap-2">
                <button className="btn-success text-sm px-3 py-1 flex-1">Buy</button>
                <button className="btn-danger text-sm px-3 py-1 flex-1">Sell</button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Positions */}
          <div className="lg:col-span-2">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Your Positions</h3>
            <div className="glass-card rounded-xl overflow-hidden">
              <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full">
                  <thead className="bg-slate-50/50 dark:bg-slate-700/50">
                    <tr>
                      <th className="text-left p-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Symbol</th>
                      <th className="text-left p-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Shares</th>
                      <th className="text-right p-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Price</th>
                      <th className="text-right p-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Change</th>
                      <th className="text-right p-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position) => (
                      <tr key={position.symbol} className="border-t border-slate-200/50 dark:border-slate-700/50 hover:bg-slate-50/50 dark:hover:bg-slate-700/50 transition-colors">
                        <td className="p-4">
                          <div>
                            <div className="font-semibold text-slate-900 dark:text-white">{position.symbol}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">{position.name}</div>
                          </div>
                        </td>
                        <td className="p-4 text-slate-900 dark:text-white">{position.shares}</td>
                        <td className="p-4 text-right text-slate-900 dark:text-white font-medium">
                          ${position.price.toFixed(2)}
                        </td>
                        <td className={`p-4 text-right font-medium ${position.change >= 0 ? 'price-up' : 'price-down'}`}>
                          {position.change >= 0 ? '+' : ''}${position.change.toFixed(2)}
                          <div className="text-sm">
                            ({position.changePercent >= 0 ? '+' : ''}{position.changePercent.toFixed(2)}%)
                          </div>
                        </td>
                        <td className="p-4 text-right text-slate-900 dark:text-white font-semibold">
                          ${(position.shares * position.price).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Watchlist */}
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Watchlist</h3>
            <div className="space-y-3">
              {watchlist.map((stock) => (
                <div key={stock.symbol} className="trading-card">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-900 dark:text-white">{stock.symbol}</span>
                    <button className="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                      </svg>
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-slate-900 dark:text-white">
                      ${stock.price.toFixed(2)}
                    </span>
                    <div className={`text-right text-sm font-medium ${stock.change >= 0 ? 'price-up' : 'price-down'}`}>
                      {stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}
                      <div>
                        ({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Market News */}
            <div className="mt-8">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Market News</h3>
              <div className="space-y-3">
                <div className="glass-card rounded-lg p-4">
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2">
                    Tech Stocks Rally on Earnings Beat
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">
                    Major technology companies showed strong quarterly results...
                  </p>
                  <span className="text-xs text-slate-500 dark:text-slate-400">2 hours ago</span>
                </div>
                <div className="glass-card rounded-lg p-4">
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2">
                    Federal Reserve Signals Rate Cuts
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">
                    The Fed indicated potential monetary policy changes...
                  </p>
                  <span className="text-xs text-slate-500 dark:text-slate-400">4 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}