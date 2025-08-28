/**
 * Trading Dashboard - Real-time Exchange Integration
 * Demonstrates WebSocket connectivity based on exchange-integration-system.mmd
 */

import { useState, useEffect, useRef } from 'react';
import { useExchange } from '../hooks/useExchange';
import { useAuth } from '../hooks/useAuth';

export function meta() {
  return [
    { title: "Trading Dashboard - BrokerPro" },
    { name: "description", content: "Real-time trading with WebSocket integration" },
  ];
}

export default function Trading() {
  const { isLoggedIn, isLoading, userInfo, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  
  const {
    state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    placeOrder,
    refreshExchangeStatus,
    getPriceForSymbol,
    clearAlerts,
    clearOrderHistory,
    loadCurrentPrices
  } = useExchange();

  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'BTC-USD']);
  const [orderForm, setOrderForm] = useState({
    symbol: 'AAPL',
    side: 'buy' as 'buy' | 'sell',
    quantity: 100,
    orderType: 'market' as 'market' | 'limit',
    price: 0
  });

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

  // Auto-connect on mount (only when authenticated)
  useEffect(() => {
    if (isLoggedIn && !state.isConnected) {
      connect();
    }
  }, [connect, state.isConnected, isLoggedIn]);

  // Auto-subscribe to selected symbols when authenticated
  useEffect(() => {
    if (state.isAuthenticated && selectedSymbols.length > 0) {
      subscribe(selectedSymbols);
    }
  }, [state.isAuthenticated, selectedSymbols, subscribe]);

  // Load initial market data for default symbols
  useEffect(() => {
    if (isLoggedIn) {
      loadCurrentPrices(['AAPL', 'GOOGL', 'BTC-USD', 'ETH-USD', 'MSFT', 'TSLA', 'SPY', 'QQQ']);
    }
  }, [isLoggedIn, loadCurrentPrices]);

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

  const handleSymbolToggle = (symbol: string) => {
    const isSubscribed = state.subscribedSymbols.includes(symbol);
    if (isSubscribed) {
      unsubscribe([symbol]);
      setSelectedSymbols(prev => prev.filter(s => s !== symbol));
    } else {
      subscribe([symbol]);
      setSelectedSymbols(prev => [...prev, symbol]);
    }
  };

  const handlePlaceOrder = (e: React.FormEvent) => {
    e.preventDefault();
    placeOrder(
      orderForm.symbol,
      orderForm.side,
      orderForm.quantity,
      orderForm.orderType,
      orderForm.orderType === 'limit' ? orderForm.price : undefined
    );
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  const formatChange = (change: number, changePercent: number) => {
    const isPositive = change >= 0;
    const className = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
    const prefix = isPositive ? '+' : '';
    
    return (
      <span className={className}>
        {prefix}{formatPrice(change)} ({prefix}{changePercent.toFixed(2)}%)
      </span>
    );
  };

  const formatVolume = (volume: number) => {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(volume);
  };

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
                <a href="/dashboard" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Dashboard
                </a>
                <a href="/banking" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Banking
                </a>
                <a href="/trading" className="text-blue-600 dark:text-blue-400 font-medium">
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Trading Dashboard</h1>
          <p className="text-slate-600 dark:text-slate-300">Real-time market data with WebSocket integration</p>
        </div>

        {/* Connection Status */}
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-slate-200 dark:border-slate-700 shadow-xl">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Connection Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${state.isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-slate-600 dark:text-slate-300">WebSocket: {state.isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${state.isAuthenticated ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-sm text-slate-600 dark:text-slate-300">Auth: {state.isAuthenticated ? 'Authenticated' : 'Pending'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-slate-600 dark:text-slate-300">Subscriptions: {state.subscribedSymbols.length}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-slate-600 dark:text-slate-300">Alerts: {state.marketAlerts.length}</span>
            </div>
          </div>
          
          <div className="mt-4 flex space-x-2">
            <button
              onClick={state.isConnected ? disconnect : connect}
              className={`px-4 py-2 rounded text-white font-medium transition-colors ${
                state.isConnected 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              disabled={state.isLoading}
            >
              {state.isConnected ? 'Disconnect' : 'Connect'}
            </button>
            <button
              onClick={refreshExchangeStatus}
              className="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors"
              disabled={state.isLoading}
            >
              Refresh Status
            </button>
          </div>

          {state.connectionError && (
            <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded text-red-700 dark:text-red-400">
              {state.connectionError}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Market Data */}
          <div className="lg:col-span-2">
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-xl">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Real-time Market Data</h2>
              
              {/* Symbol Selection */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Available Symbols</h3>
                <div className="flex flex-wrap gap-2">
                  {['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'BTC-USD', 'ETH-USD', 'SPY', 'QQQ'].map((symbol) => (
                    <button
                      key={symbol}
                      onClick={() => handleSymbolToggle(symbol)}
                      className={`px-3 py-1 text-sm rounded border transition-colors ${
                        state.subscribedSymbols.includes(symbol)
                          ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300'
                          : 'bg-slate-100 dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                      }`}
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Data Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-700">
                      <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Symbol</th>
                      <th className="text-right py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Price</th>
                      <th className="text-right py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Change</th>
                      <th className="text-right py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Volume</th>
                      <th className="text-right py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Bid/Ask</th>
                      <th className="text-right py-3 px-4 font-medium text-slate-700 dark:text-slate-300">Last Update</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(state.marketData).map((symbol) => {
                      const priceData = getPriceForSymbol(symbol);
                      const isSubscribed = state.subscribedSymbols.includes(symbol);
                      return (
                        <tr key={symbol} className={`border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${!isSubscribed ? 'opacity-60' : ''}`}>
                          <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">
                            {symbol}
                            {!isSubscribed && <span className="ml-2 text-xs text-slate-400">(static)</span>}
                          </td>
                          <td className="py-3 px-4 text-right text-slate-900 dark:text-white">
                            {priceData ? formatPrice(priceData.price) : '--'}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {priceData ? formatChange(priceData.change, priceData.change_percent) : '--'}
                          </td>
                          <td className="py-3 px-4 text-right text-slate-900 dark:text-white">
                            {priceData ? formatVolume(priceData.volume) : '--'}
                          </td>
                          <td className="py-3 px-4 text-right text-sm text-slate-600 dark:text-slate-400">
                            {priceData ? `${formatPrice(priceData.bid)} / ${formatPrice(priceData.ask)}` : '--'}
                          </td>
                          <td className="py-3 px-4 text-right text-sm text-slate-500 dark:text-slate-400">
                            {priceData ? new Date(priceData.timestamp).toLocaleTimeString() : '--'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                
                {Object.keys(state.marketData).length === 0 && (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    Loading market data...
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Trading Panel */}
          <div className="space-y-6">
            {/* Order Form */}
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-xl">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Place Order</h2>
              <form onSubmit={handlePlaceOrder} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Symbol</label>
                  <select
                    value={orderForm.symbol}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, symbol: e.target.value }))}
                    className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 rounded px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  >
                    {['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'BTC-USD', 'ETH-USD'].map((symbol) => (
                      <option key={symbol} value={symbol}>{symbol}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Side</label>
                  <select
                    value={orderForm.side}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, side: e.target.value as 'buy' | 'sell' }))}
                    className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 rounded px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  >
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Quantity</label>
                  <input
                    type="number"
                    value={orderForm.quantity}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, quantity: parseInt(e.target.value) || 0 }))}
                    className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 rounded px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                    min="1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Order Type</label>
                  <select
                    value={orderForm.orderType}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, orderType: e.target.value as 'market' | 'limit' }))}
                    className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 rounded px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  >
                    <option value="market">Market</option>
                    <option value="limit">Limit</option>
                  </select>
                </div>
                
                {orderForm.orderType === 'limit' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Price</label>
                    <input
                      type="number"
                      value={orderForm.price}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                      className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 rounded px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                      min="0"
                      step="0.01"
                    />
                  </div>
                )}
                
                <button
                  type="submit"
                  disabled={!state.isAuthenticated}
                  className={`w-full py-2 rounded font-medium transition-colors ${
                    orderForm.side === 'buy'
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-red-600 text-white hover:bg-red-700'
                  } ${!state.isAuthenticated ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {orderForm.side === 'buy' ? 'Buy' : 'Sell'} {orderForm.symbol}
                </button>
              </form>
            </div>

            {/* Order History */}
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Order History</h2>
                <button
                  onClick={clearOrderHistory}
                  className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {state.orderHistory.map((order, index) => (
                  <div key={index} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded text-sm">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-slate-900 dark:text-white">{order.symbol}</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        order.status === 'filled' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                      }`}>
                        {order.status}
                      </span>
                    </div>
                    <div className="text-slate-600 dark:text-slate-300 mt-1">
                      {order.quantity} @ {formatPrice(order.price)}
                    </div>
                    <div className="text-slate-500 dark:text-slate-400 text-xs mt-1">
                      {new Date(order.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
                {state.orderHistory.length === 0 && (
                  <div className="text-center py-4 text-slate-500 dark:text-slate-400">No orders yet</div>
                )}
              </div>
            </div>

            {/* Market Alerts */}
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Market Alerts</h2>
                <button
                  onClick={clearAlerts}
                  className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {state.marketAlerts.map((alert, index) => (
                  <div key={index} className={`p-3 rounded text-sm border-l-4 ${
                    alert.severity === 'high' || alert.severity === 'critical' 
                      ? 'bg-red-50 dark:bg-red-900/30 border-red-400 dark:border-red-600'
                      : alert.severity === 'medium'
                      ? 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-400 dark:border-yellow-600'
                      : 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 dark:border-blue-600'
                  }`}>
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-slate-900 dark:text-white">{alert.title}</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{alert.symbol}</span>
                    </div>
                    <div className="text-slate-600 dark:text-slate-300 mt-1">{alert.message}</div>
                    <div className="text-slate-500 dark:text-slate-400 text-xs mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
                {state.marketAlerts.length === 0 && (
                  <div className="text-center py-4 text-slate-500 dark:text-slate-400">No alerts</div>
                )}
              </div>
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
                <li><a href="/dashboard" className="hover:text-white transition-colors">Portfolio</a></li>
                <li><a href="/banking" className="hover:text-white transition-colors">Banking</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4">Markets</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Stocks</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Options</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Crypto</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4">Support</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Docs</a></li>
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