import type { Route } from "./+types/banking";
import { useAuth } from "../hooks/useAuth";
import { useState, useEffect, useRef } from "react";
import { linkBankAccount, initiateDeposit, initiateWithdrawal, verifyBankAccount, getBankAccounts, getTransactionHistory, getAccessToken, getRefreshToken } from "../lib/api-client";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Banking - BrokerPro" },
    { name: "description", content: "Manage your bank accounts and transactions" },
  ];
}

// Define types for data from API
interface BankAccount {
  account_link_id: string;
  last_four_digits: string;
  bank_name: string;
  status: string;
  account_type: string;
  account_holder_name: string;
}

interface Transaction {
  transaction_id: string;
  type: string;
  amount: number;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export default function Banking() {
  const { isLoggedIn, isLoading, userInfo, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [activeTab, setActiveTab] = useState<'accounts' | 'deposit' | 'withdraw' | 'history'>('accounts');
  const [showLinkAccount, setShowLinkAccount] = useState(false);
  const [showVerifyAccount, setShowVerifyAccount] = useState(false);
  const [selectedAccountForVerification, setSelectedAccountForVerification] = useState<string | null>(null);
  const [linkAccountStep, setLinkAccountStep] = useState<'form' | 'processing' | 'verification'>('form');
  const userMenuRef = useRef<HTMLDivElement>(null);
  
  // API data state
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(false);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // Token status state
  const [tokenStatus, setTokenStatus] = useState<{
    hasTokens: boolean;
    accessTokenExpiry?: number;
    timeUntilExpiry?: number;
  }>({ hasTokens: false });

  // Update token status
  const updateTokenStatus = () => {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    
    if (accessToken && refreshToken) {
      try {
        const payload = JSON.parse(atob(accessToken.split(".")[1]));
        const now = Date.now() / 1000;
        const timeUntilExpiry = payload.exp - now;
        
        setTokenStatus({
          hasTokens: true,
          accessTokenExpiry: payload.exp,
          timeUntilExpiry
        });
      } catch {
        setTokenStatus({ hasTokens: false });
      }
    } else {
      setTokenStatus({ hasTokens: false });
    }
  };

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

  // Update token status periodically
  useEffect(() => {
    updateTokenStatus();
    const interval = setInterval(updateTokenStatus, 1000); // Update every second
    return () => clearInterval(interval);
  }, []);

  // Fetch bank accounts
  const fetchBankAccounts = async () => {
    if (!isLoggedIn) return;
    
    setIsLoadingAccounts(true);
    setApiError(null);
    try {
      const response = await getBankAccounts();
      setBankAccounts(response.accounts || []);
    } catch (error) {
      console.error('Error fetching bank accounts:', error);
      setApiError('Failed to load bank accounts');
      setBankAccounts([]);
    } finally {
      setIsLoadingAccounts(false);
    }
  };

  // Fetch transaction history
  const fetchTransactions = async () => {
    if (!isLoggedIn) return;
    
    setIsLoadingTransactions(true);
    setApiError(null);
    try {
      const response = await getTransactionHistory();
      setTransactions(response.transactions || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setApiError('Failed to load transactions');
      setTransactions([]);
    } finally {
      setIsLoadingTransactions(false);
    }
  };

  // Authentication redirect
  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      window.location.href = '/login';
    }
  }, [isLoading, isLoggedIn]);

  // Load data when component mounts and user is authenticated
  useEffect(() => {
    if (isLoggedIn && !isLoading) {
      fetchBankAccounts();
      fetchTransactions();
    }
  }, [isLoggedIn, isLoading]);

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
    return null;
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
                <a href="/dashboard" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Dashboard
                </a>
                <a href="/banking" className="text-blue-600 dark:text-blue-400 font-medium">
                  Banking
                </a>
                <a href="#" className="text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                  Trading
                </a>
              </div>
            </div>
            <div className="flex items-center gap-4">
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
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                Banking & Transfers
              </h1>
              <p className="text-slate-600 dark:text-slate-300">
                Link your bank accounts, deposit funds, and manage transfers
              </p>
            </div>
            
            {/* Token Status Display */}
            {tokenStatus.hasTokens && (
              <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-lg p-3 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Token Status</div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    tokenStatus.timeUntilExpiry && tokenStatus.timeUntilExpiry > 120 
                      ? 'bg-green-500' 
                      : tokenStatus.timeUntilExpiry && tokenStatus.timeUntilExpiry > 60
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`} />
                  <span className="text-sm font-mono text-slate-700 dark:text-slate-300">
                    {tokenStatus.timeUntilExpiry && tokenStatus.timeUntilExpiry > 0
                      ? `${Math.floor(tokenStatus.timeUntilExpiry / 60)}:${Math.floor(tokenStatus.timeUntilExpiry % 60).toString().padStart(2, '0')}`
                      : 'Expired'}
                  </span>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {tokenStatus.timeUntilExpiry && tokenStatus.timeUntilExpiry <= 120 ? 'Auto-refresh active' : 'Token valid'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { key: 'accounts', label: 'Bank Accounts', icon: '🏦' },
            { key: 'deposit', label: 'Deposit', icon: '⬇️' }, 
            { key: 'withdraw', label: 'Withdraw', icon: '⬆️' },
            { key: 'history', label: 'Transaction History', icon: '📊' },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab.key 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Bank Accounts Tab */}
          {activeTab === 'accounts' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                  Linked Bank Accounts
                </h2>
                <button
                  onClick={() => setShowLinkAccount(true)}
                  className="btn-primary flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Link New Account
                </button>
              </div>

              {isLoadingAccounts ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-slate-600 dark:text-slate-300">Loading accounts...</span>
                </div>
              ) : apiError ? (
                <div className="trading-card max-w-md">
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Error Loading Accounts</h3>
                    <p className="text-slate-600 dark:text-slate-300 mb-4">{apiError}</p>
                    <button onClick={fetchBankAccounts} className="btn-primary">Retry</button>
                  </div>
                </div>
              ) : bankAccounts.length === 0 ? (
                <div className="trading-card max-w-md">
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No Bank Accounts</h3>
                    <p className="text-slate-600 dark:text-slate-300 mb-4">You haven't linked any bank accounts yet.</p>
                    <button onClick={() => setShowLinkAccount(true)} className="btn-primary">Link Your First Account</button>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4">
                  {bankAccounts.map(account => (
                    <div key={account.account_link_id} className="trading-card">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                          <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                          </svg>
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900 dark:text-white">
                            {account.bank_name}
                          </h3>
                          <p className="text-sm text-slate-600 dark:text-slate-300">
                            {account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)} ••••{account.last_four_digits}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {account.status === 'verified' ? (
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                            ✓ Verified
                          </span>
                        ) : (
                          <button
                            onClick={() => {
                              setSelectedAccountForVerification(account.account_link_id);
                              setShowVerifyAccount(true);
                            }}
                            className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors"
                          >
                            ⏳ Verify Account
                          </button>
                        )}
                        <button className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Deposit Tab */}
          {activeTab === 'deposit' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                Deposit Funds
              </h2>
              
              {bankAccounts.filter(acc => acc.status === 'verified').length === 0 ? (
                <div className="trading-card max-w-md">
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      No Verified Bank Account
                    </h3>
                    <p className="text-slate-600 dark:text-slate-300 mb-4">
                      You need to link and verify a bank account before you can deposit funds.
                    </p>
                    <button 
                      onClick={() => setShowLinkAccount(true)}
                      className="btn-primary"
                    >
                      Link Bank Account
                    </button>
                  </div>
                </div>
              ) : (
                <div className="trading-card max-w-md">
                  <form onSubmit={async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target as HTMLFormElement);
                    const accountLinkId = formData.get('accountLinkId') as string;
                    const amount = parseFloat(formData.get('amount') as string);
                    
                    try {
                      await initiateDeposit(accountLinkId, amount);
                      alert('Deposit initiated successfully! Processing time: 1-3 business days.');
                      (e.target as HTMLFormElement).reset();
                      // Refresh transactions data
                      await fetchTransactions();
                    } catch (error) {
                      alert('Deposit failed: ' + (error as Error).message);
                    }
                  }} className="space-y-4">
                    <div>
                      <label className="form-label">From Bank Account</label>
                      <select name="accountLinkId" className="form-input" required>
                        <option value="">Select an account</option>
                        {bankAccounts.filter(acc => acc.status === 'verified').map(account => (
                          <option key={account.account_link_id} value={account.account_link_id}>
                            {account.bank_name} ••••{account.last_four_digits} ({account.account_type})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="form-label">Amount</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500">$</span>
                        <input 
                          type="number" 
                          name="amount"
                          className="form-input pl-8" 
                          placeholder="0.00"
                          min="1"
                          max="50000"
                          step="0.01"
                          required
                        />
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Daily limit: $50,000 • Processing time: 1-3 business days
                      </p>
                    </div>
                    
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                      <p className="text-xs text-blue-700 dark:text-blue-300">
                        💡 ACH transfers typically take 1-3 business days to complete. You'll receive a confirmation once the deposit is processed.
                      </p>
                    </div>
                    
                    <button type="submit" className="btn-primary w-full">
                      Initiate Deposit
                    </button>
                  </form>
                </div>
              )}
            </div>
          )}

          {/* Withdraw Tab */}
          {activeTab === 'withdraw' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                Withdraw Funds
              </h2>
              
              {bankAccounts.filter(acc => acc.status === 'verified').length === 0 ? (
                <div className="trading-card max-w-md">
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      No Verified Bank Account
                    </h3>
                    <p className="text-slate-600 dark:text-slate-300 mb-4">
                      You need to link and verify a bank account before you can withdraw funds.
                    </p>
                    <button 
                      onClick={() => setShowLinkAccount(true)}
                      className="btn-primary"
                    >
                      Link Bank Account
                    </button>
                  </div>
                </div>
              ) : (
                <div className="trading-card max-w-md">
                  <form onSubmit={async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target as HTMLFormElement);
                    const accountLinkId = formData.get('accountLinkId') as string;
                    const amount = parseFloat(formData.get('amount') as string);
                    
                    if (!accountLinkId) {
                      alert('Please select a bank account');
                      return;
                    }
                    
                    if (!amount || amount < 10) {
                      alert('Minimum withdrawal amount is $10.00');
                      return;
                    }
                    
                    if (amount > 15420.50) {
                      alert('Insufficient balance for this withdrawal');
                      return;
                    }
                    
                    try {
                      await initiateWithdrawal(accountLinkId, amount);
                      alert(`Withdrawal of $${amount.toFixed(2)} has been initiated successfully! Processing time: 1-3 business days.`);
                      (e.target as HTMLFormElement).reset();
                      // Refresh transactions data
                      await fetchTransactions();
                    } catch (error) {
                      alert('Withdrawal failed: ' + (error as Error).message);
                    }
                  }} className="space-y-4">
                    <div>
                      <label className="form-label">To Bank Account</label>
                      <select name="accountLinkId" className="form-input" required>
                        <option value="">Select an account</option>
                        {bankAccounts.filter(acc => acc.status === 'verified').map(account => (
                          <option key={account.account_link_id} value={account.account_link_id}>
                            {account.bank_name} ••••{account.last_four_digits} ({account.account_type})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="form-label">Amount</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500">$</span>
                        <input 
                          type="number" 
                          name="amount"
                          className="form-input pl-8" 
                          placeholder="0.00"
                          min="10"
                          max="15420.50"
                          step="0.01"
                          required
                        />
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Available balance: $15,420.50 • Minimum: $10.00 • Processing time: 1-3 business days
                      </p>
                    </div>
                    
                    <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                      <p className="text-xs text-red-700 dark:text-red-300">
                        ⚠️ Withdrawals typically take 1-3 business days to complete. Ensure you have sufficient balance before proceeding.
                      </p>
                    </div>
                    
                    <button type="submit" className="btn-primary w-full">
                      Initiate Withdrawal
                    </button>
                  </form>
                </div>
              )}
            </div>
          )}

          {/* Transaction History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                Transaction History
              </h2>
              {isLoadingTransactions ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-slate-600 dark:text-slate-300">Loading transactions...</span>
                </div>
              ) : transactions.length === 0 ? (
                <div className="trading-card max-w-md">
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No Transactions</h3>
                    <p className="text-slate-600 dark:text-slate-300">Your transaction history will appear here once you make deposits or withdrawals.</p>
                  </div>
                </div>
              ) : (
                <div className="trading-card">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200 dark:border-slate-700">
                          <th className="text-left py-3 font-medium text-slate-900 dark:text-white">Type</th>
                          <th className="text-left py-3 font-medium text-slate-900 dark:text-white">Amount</th>
                          <th className="text-left py-3 font-medium text-slate-900 dark:text-white">Status</th>
                          <th className="text-left py-3 font-medium text-slate-900 dark:text-white">Date</th>
                          <th className="text-left py-3 font-medium text-slate-900 dark:text-white">Completed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transactions.map(txn => (
                        <tr key={txn.transaction_id} className="border-b border-slate-100 dark:border-slate-800">
                          <td className="py-3">
                            <div className="flex items-center gap-2">
                              {txn.type === 'deposit' ? (
                                <span className="text-green-600 dark:text-green-400">⬇️ Deposit</span>
                              ) : (
                                <span className="text-blue-600 dark:text-blue-400">⬆️ Withdraw</span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 font-mono">
                            ${txn.amount.toFixed(2)}
                          </td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              txn.status === 'completed' 
                                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                : txn.status === 'processing'
                                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                                : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                            }`}>
                              {txn.status.charAt(0).toUpperCase() + txn.status.slice(1)}
                            </span>
                          </td>
                          <td className="py-3 text-sm text-slate-600 dark:text-slate-300">
                            {new Date(txn.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 text-sm text-slate-600 dark:text-slate-300">
                            {txn.completed_at ? new Date(txn.completed_at).toLocaleDateString() : '-'}
                          </td>
                        </tr>
                      ))}
                        </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Link Account Modal */}
      {showLinkAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                {linkAccountStep === 'form' ? 'Link Bank Account' : 
                 linkAccountStep === 'processing' ? 'Processing...' : 
                 'Verification Required'}
              </h3>
              <button 
                onClick={() => {
                  setShowLinkAccount(false);
                  setLinkAccountStep('form');
                }}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            {linkAccountStep === 'form' && (
              <form onSubmit={async (e) => {
                e.preventDefault();
                setLinkAccountStep('processing');
                
                const formData = new FormData(e.target as HTMLFormElement);
                try {
                  await linkBankAccount(
                    formData.get('routingNumber') as string,
                    formData.get('accountNumber') as string,
                    formData.get('accountType') as 'checking' | 'savings',
                    formData.get('accountHolderName') as string
                  );
                  setLinkAccountStep('verification');
                  // Refresh bank accounts data
                  await fetchBankAccounts();
                } catch (error) {
                  alert('Failed to link account: ' + (error as Error).message);
                  setLinkAccountStep('form');
                }
              }} className="space-y-4">
                <div>
                  <label className="form-label">Bank Routing Number</label>
                  <input 
                    type="text" 
                    name="routingNumber"
                    className="form-input" 
                    placeholder="021000021" 
                    required
                    pattern="[0-9]{9}"
                    title="Please enter a 9-digit routing number"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Test routing numbers: 021000021 (Chase), 026009593 (BofA), 122000247 (Wells Fargo)
                  </p>
                </div>
                <div>
                  <label className="form-label">Account Number</label>
                  <input 
                    type="text" 
                    name="accountNumber"
                    className="form-input" 
                    placeholder="1234567890" 
                    required
                    minLength="4"
                    maxLength="17"
                  />
                </div>
                <div>
                  <label className="form-label">Account Type</label>
                  <select name="accountType" className="form-input" required>
                    <option value="checking">Checking</option>
                    <option value="savings">Savings</option>
                  </select>
                </div>
                <div>
                  <label className="form-label">Account Holder Name</label>
                  <input 
                    type="text" 
                    name="accountHolderName"
                    className="form-input" 
                    placeholder="John Doe" 
                    required
                  />
                </div>
                
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div className="text-sm">
                      <p className="text-blue-900 dark:text-blue-100 font-medium mb-1">Secure Account Linking</p>
                      <p className="text-blue-700 dark:text-blue-300">
                        We'll send micro-deposits (under $1) to verify your account ownership. 
                        This process takes 2-3 business days.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button 
                    type="button"
                    onClick={() => {
                      setShowLinkAccount(false);
                      setLinkAccountStep('form');
                    }}
                    className="flex-1 px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 btn-primary">
                    Link Account
                  </button>
                </div>
              </form>
            )}

            {linkAccountStep === 'processing' && (
              <div className="flex flex-col items-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-slate-600 dark:text-slate-300">Linking your bank account...</p>
              </div>
            )}

            {linkAccountStep === 'verification' && (
              <div className="space-y-4">
                <div className="text-center py-4">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                  </div>
                  <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    Account Linked Successfully!
                  </h4>
                  <p className="text-slate-600 dark:text-slate-300 mb-4">
                    We're sending micro-deposits to verify your account. This typically takes 2-3 business days.
                  </p>
                </div>
                
                <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div className="text-sm">
                      <p className="text-yellow-900 dark:text-yellow-100 font-medium mb-1">Next Steps</p>
                      <ul className="text-yellow-700 dark:text-yellow-300 space-y-1">
                        <li>• Check your bank statement in 2-3 days</li>
                        <li>• Look for two deposits under $1.00</li>
                        <li>• Return here to enter the amounts for verification</li>
                        <li>• Once verified, you can deposit and withdraw funds</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => {
                    setShowLinkAccount(false);
                    setLinkAccountStep('form');
                  }}
                  className="w-full btn-primary"
                >
                  Got It
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Account Verification Modal */}
      {showVerifyAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Verify Bank Account
              </h3>
              <button 
                onClick={() => {
                  setShowVerifyAccount(false);
                  setSelectedAccountForVerification(null);
                }}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            
            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div className="text-sm">
                  <p className="text-blue-900 dark:text-blue-100 font-medium mb-1">Micro-deposit verification</p>
                  <p className="text-blue-700 dark:text-blue-300">
                    We've sent two small deposits (under $1.00) to your bank account. 
                    Check your bank statement and enter the amounts below to verify ownership.
                  </p>
                </div>
              </div>
            </div>

            <form onSubmit={async (e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              const amount1 = parseFloat(formData.get('amount1') as string);
              const amount2 = parseFloat(formData.get('amount2') as string);
              
              if (!selectedAccountForVerification) {
                alert('No account selected for verification');
                return;
              }
              
              try {
                const response = await verifyBankAccount(selectedAccountForVerification, [amount1, amount2]);
                alert('Account verified successfully!');
                setShowVerifyAccount(false);
                setSelectedAccountForVerification(null);
                // Refresh bank accounts data
                await fetchBankAccounts();
              } catch (error) {
                alert('Verification failed: ' + (error as Error).message);
              }
            }} className="space-y-4">
              <div>
                <label className="form-label">First Deposit Amount</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500">$</span>
                  <input 
                    type="number" 
                    name="amount1"
                    className="form-input pl-8" 
                    placeholder="0.01"
                    min="0.01"
                    max="0.99"
                    step="0.01"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="form-label">Second Deposit Amount</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500">$</span>
                  <input 
                    type="number" 
                    name="amount2"
                    className="form-input pl-8" 
                    placeholder="0.23"
                    min="0.01"
                    max="0.99"
                    step="0.01"
                    required
                  />
                </div>
              </div>
              
              <div className="text-xs text-slate-500 dark:text-slate-400">
                <p>• Micro-deposits typically appear within 2-3 business days</p>
                <p>• You have 3 attempts to verify</p>
                <p>• Contact support if you need help</p>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button 
                  type="button"
                  onClick={() => {
                    setShowVerifyAccount(false);
                    setSelectedAccountForVerification(null);
                  }}
                  className="flex-1 px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button type="submit" className="flex-1 btn-primary">
                  Verify Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}