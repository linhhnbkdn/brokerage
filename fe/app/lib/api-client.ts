/**
 * Generated API client for the Brokerage backend
 * Fully typed client using openapi-fetch and generated types
 */
import createClient from "openapi-fetch";
import type { paths } from "./api-types";

// Configuration
const API_BASE_URL = "http://localhost:8000";

// Create the typed client
export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
});

// Auth Types (manually defined for better type safety)
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface RegisterResponse {
  access_token: string;
  refresh_token: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface LogoutResponse {
  message: string;
}

export interface ProtectedResponse {
  message: string;
  user_id: number;
  email: string;
}

// Authentication token management
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

/**
 * Store authentication tokens in localStorage
 */
export function storeTokens(tokens: AuthTokens): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

/**
 * Get stored access token
 */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get stored refresh token
 */
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Clear all stored tokens
 */
export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;

  try {
    // Simple token expiry check (decode JWT payload)
    const payload = JSON.parse(atob(token.split(".")[1]));
    const now = Date.now() / 1000;
    return payload.exp > now;
  } catch {
    return false;
  }
}

/**
 * Get user info from stored token
 */
export function getUserInfo(): { userId: number; email?: string } | null {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return {
      userId: payload.user_id,
      email: payload.email || null,
    };
  } catch {
    return null;
  }
}

/**
 * Set up automatic token refresh and authorization headers
 */
export function setupAuth() {
  // For now, we'll handle auth headers manually in each request
  // This avoids middleware issues
}

/**
 * Login user with email and password
 */
export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  console.log("🔄 Making login request to:", API_BASE_URL + "/api/auth/login/");
  console.log("📝 Login data:", { email });

  try {
    const response = await fetch(API_BASE_URL + "/api/auth/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: window.location.origin,
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    console.log("📡 Login response status:", response.status);
    console.log(
      "📡 Login response headers:",
      Object.fromEntries(response.headers.entries())
    );

    const data = await response.json();
    console.log("✅ Login response data:", data);

    if (!response.ok) {
      throw new Error(data?.error || "Login failed");
    }

    // Store tokens
    storeTokens(data);
    return data;
  } catch (error) {
    console.error("❌ Login error:", error);
    throw error;
  }
}

/**
 * Register new user
 */
export async function register(
  email: string,
  password: string,
  firstName: string,
  lastName: string
): Promise<RegisterResponse> {
  console.log(
    "🔄 Making registration request to:",
    API_BASE_URL + "/api/auth/register/"
  );
  console.log("📝 Registration data:", {
    email: email.toLowerCase().trim(),
    firstName: firstName.trim(),
    lastName: lastName.trim(),
  });

  try {
    const response = await fetch(API_BASE_URL + "/api/auth/register/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Origin: window.location.origin,
      },
      body: JSON.stringify({
        email: email.toLowerCase().trim(),
        password,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
      }),
    });

    console.log("📡 Registration response status:", response.status);
    console.log(
      "📡 Registration response headers:",
      Object.fromEntries(response.headers.entries())
    );

    const data = await response.json();
    console.log("✅ Registration response data:", data);

    if (!response.ok) {
      throw new Error(data?.error || "Registration failed");
    }

    // Store tokens
    storeTokens(data);
    return data;
  } catch (error) {
    console.error("❌ Registration error:", error);
    throw error;
  }
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  console.log("🔄 Attempting to refresh access token...");

  try {
    const { data, error } = await api.POST("/api/auth/refresh/", {
      body: {
        refresh_token: refreshToken,
      },
    });

    if (error || !data) {
      console.error("❌ Token refresh failed:", error);
      clearTokens(); // Clear invalid tokens
      return false;
    }

    console.log("✅ Token refreshed successfully");
    storeTokens(data as AuthTokens);
    return true;
  } catch (error) {
    console.error("❌ Token refresh error:", error);
    clearTokens(); // Clear invalid tokens
    return false;
  }
}

/**
 * Make an authenticated request with automatic token refresh
 */
export async function makeAuthenticatedRequest<T>(
  requestFn: () => Promise<T>
): Promise<T> {
  try {
    return await requestFn();
  } catch (error: any) {
    // Check if it's a 401 error (token expired)
    if (error?.status === 401 || (error?.response?.status === 401)) {
      console.log("🔄 Got 401, attempting token refresh...");
      
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        console.log("✅ Token refreshed, retrying request...");
        return await requestFn();
      } else {
        console.log("❌ Token refresh failed, redirecting to login");
        clearTokens();
        // In a real app, you might redirect to login here
        throw new Error("Authentication failed - please login again");
      }
    }
    throw error;
  }
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();

  if (refreshToken) {
    try {
      await api.POST("/api/auth/logout/", {
        body: {
          refresh_token: refreshToken,
        },
      });
    } catch (error) {
      console.error("Logout API call failed:", error);
    }
  }

  clearTokens();
}

/**
 * Get current user information (requires authentication)
 */
export async function getCurrentUser(): Promise<ProtectedResponse> {
  const response = await fetch(API_BASE_URL + "/api/auth/protected/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getAccessToken()}`,
      "Origin": window.location.origin,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get user info");
  }

  const data = await response.json();
  return data;
}

/**
 * Link a new bank account with automatic token refresh
 */
export async function linkBankAccount(
  routingNumber: string,
  accountNumber: string,
  accountType: 'checking' | 'savings',
  accountHolderName: string
) {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Making bank account link request to:', API_BASE_URL + "/api/banking/link-account/");
    console.log('📝 Bank account data:', { routingNumber, accountType, accountHolderName });
    
    const response = await fetch(API_BASE_URL + "/api/banking/link-account/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify({
        bank_routing_number: routingNumber,
        account_number: accountNumber,
        account_type: accountType,
        account_holder_name: accountHolderName,
      }),
    });

    console.log('📡 Bank link response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Bank link response data:', data);

    if (!response.ok) {
      const error = new Error(data?.error || 'Failed to link bank account') as any;
      error.status = response.status;
      throw error;
    }

    return data;
  });
}

/**
 * Initiate deposit
 */
export async function initiateDeposit(
  accountLinkId: string,
  amount: number,
  currency: string = 'USD'
) {
  console.log('🔄 Making deposit request to:', API_BASE_URL + "/api/banking/deposit/");
  console.log('📝 Deposit data:', { accountLinkId, amount, currency });
  
  try {
    const response = await fetch(API_BASE_URL + "/api/banking/deposit/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify({
        account_link_id: accountLinkId,
        amount,
        currency,
      }),
    });

    console.log('📡 Deposit response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Deposit response data:', data);

    if (!response.ok) {
      throw new Error(data?.error || 'Deposit failed');
    }

    return data;
  } catch (error) {
    console.error('❌ Deposit error:', error);
    throw error;
  }
}

/**
 * Initiate withdrawal
 */
export async function initiateWithdrawal(
  accountLinkId: string,
  amount: number,
  currency: string = 'USD'
) {
  console.log('🔄 Making withdrawal request to:', API_BASE_URL + "/api/banking/withdraw/");
  console.log('📝 Withdrawal data:', { accountLinkId, amount, currency });
  
  try {
    const response = await fetch(API_BASE_URL + "/api/banking/withdraw/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify({
        account_link_id: accountLinkId,
        amount,
        currency,
      }),
    });

    console.log('📡 Withdrawal response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Withdrawal response data:', data);

    if (!response.ok) {
      throw new Error(data?.error || 'Withdrawal failed');
    }

    return data;
  } catch (error) {
    console.error('❌ Withdrawal error:', error);
    throw error;
  }
}

/**
 * Verify bank account with micro-deposits
 */
export async function verifyBankAccount(
  accountLinkId: string,
  depositAmounts: [number, number]
) {
  console.log('🔄 Making account verification request to:', API_BASE_URL + "/api/banking/verify-account/");
  console.log('📝 Verification data:', { accountLinkId, depositAmounts });
  
  try {
    const response = await fetch(API_BASE_URL + "/api/banking/verify-account/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify({
        account_link_id: accountLinkId,
        deposit_amounts: depositAmounts,
      }),
    });

    console.log('📡 Verification response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Verification response data:', data);

    if (!response.ok) {
      throw new Error(data?.error || 'Account verification failed');
    }

    return data;
  } catch (error) {
    console.error('❌ Verification error:', error);
    throw error;
  }
}

/**
 * Get user's bank accounts with automatic token refresh
 */
export async function getBankAccounts() {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Making get bank accounts request to:', API_BASE_URL + "/api/banking/accounts/");
    
    const response = await fetch(API_BASE_URL + "/api/banking/accounts/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    console.log('📡 Bank accounts response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Bank accounts response data:', data);

    if (!response.ok) {
      const error = new Error(data?.error || 'Failed to fetch bank accounts') as any;
      error.status = response.status;
      throw error;
    }

    return data;
  });
}

/**
 * Get transaction history with automatic token refresh
 */
export async function getTransactionHistory() {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Making get transactions request to:', API_BASE_URL + "/api/banking/transactions/");
    
    const response = await fetch(API_BASE_URL + "/api/banking/transactions/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    console.log('📡 Transactions response status:', response.status);
    
    const data = await response.json();
    console.log('✅ Transactions response data:', data);

    if (!response.ok) {
      const error = new Error(data?.error || 'Failed to fetch transactions') as any;
      error.status = response.status;
      throw error;
    }

    return data;
  });
}

/**
 * Initialize the API client with automatic token refresh
 * Call this once in your app initialization
 */
export function initializeApiClient() {
  // Set up periodic token refresh (every 10 minutes)
  if (typeof window !== "undefined") {
    setInterval(async () => {
      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();
      
      if (accessToken && refreshToken) {
        try {
          // Check if token is close to expiry (within 2 minutes)
          const payload = JSON.parse(atob(accessToken.split(".")[1]));
          const now = Date.now() / 1000;
          const timeUntilExpiry = payload.exp - now;
          
          if (timeUntilExpiry < 120) { // 2 minutes
            console.log("🔄 Token expiring soon, refreshing proactively...");
            await refreshAccessToken();
          }
        } catch (error) {
          console.error("❌ Error checking token expiry:", error);
        }
      }
    }, 10 * 60 * 1000); // Every 10 minutes
  }
}

// Portfolio API Types (manually defined based on schema for better type safety)
export interface PortfolioOverviewResponse {
  total_value: string;
  cash_balance: string;
  total_portfolio_value: string;
  total_cost_basis: string;
  total_gain_loss: string;
  total_gain_loss_percent: string;
  day_gain_loss: string;
  day_gain_loss_percent: string;
  positions_count: number;
  last_updated: string;
  asset_allocation: Record<string, any>;
  top_positions: Array<any>;
}

export interface PortfolioPerformanceResponse {
  period: string;
  period_display: string;
  start_date: string;
  end_date: string;
  total_return: string;
  annualized_return?: string;
  volatility?: string;
  sharpe_ratio?: string;
  max_drawdown?: string;
  benchmark_return?: string;
  alpha?: string;
  beta?: string;
  outperformed_benchmark: boolean;
  starting_value: string;
  ending_value: string;
  peak_value?: string;
  is_profitable: boolean;
  trading_days: number;
  snapshots: Array<any>;
}

export interface Position {
  position_id: string;
  symbol: string;
  instrument_type: string;
  name: string;
  quantity: string;
  average_cost: string;
  current_price?: string;
  cost_basis: string;
  current_value: string;
  unrealized_gain_loss: string;
  unrealized_gain_loss_percent: string;
  status: string;
  opened_at: string;
  is_profitable: boolean;
}

export interface PositionCreateRequest {
  symbol: string;
  instrument_type: "stock" | "bond" | "crypto" | "etf" | "mutual_fund" | "option" | "future";
  name: string;
  quantity: string;
  average_cost: string;
}

export interface PortfolioSnapshot {
  snapshot_id: string;
  snapshot_date: string;
  snapshot_time: string;
  total_value: string;
  cash_balance: string;
  total_portfolio_value: string;
  total_cost_basis: string;
  day_gain_loss: string;
  day_gain_loss_percent: string;
  total_gain_loss: string;
  total_gain_loss_percent: string;
  cash_allocation_percent: string;
  holdings_data: Record<string, any>;
  holdings_count: number;
  is_profitable: boolean;
}

export interface PerformanceMetrics {
  metrics_id: string;
  period: string;
  period_display: string;
  start_date: string;
  end_date: string;
  calculated_at: string;
  total_return: string;
  annualized_return?: string;
  volatility?: string;
  sharpe_ratio?: string;
  max_drawdown?: string;
  benchmark_return?: string;
  alpha?: string;
  beta?: string;
  starting_value: string;
  ending_value: string;
  outperformed_benchmark: boolean;
  is_profitable: boolean;
  risk_adjusted_return?: string;
}

export interface MetricsCalculationRequest {
  period: "1D" | "1W" | "1M" | "3M" | "6M" | "1Y" | "3Y" | "5Y" | "ALL";
  force_recalculate?: boolean;
  include_benchmark?: boolean;
  benchmark_symbol?: string;
}

export interface SnapshotCreateRequest {
  snapshot_date?: string;
  force_recreate?: boolean;
}

/**
 * PORTFOLIO API FUNCTIONS
 */

/**
 * Get portfolio overview with positions and performance
 */
export async function getPortfolioOverview(): Promise<PortfolioOverviewResponse> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting portfolio overview...');
    
    const response = await fetch(API_BASE_URL + "/api/portfolio/overview/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch portfolio overview') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Portfolio overview fetched successfully');
    return data;
  });
}

/**
 * Get portfolio performance data for specified period
 */
export async function getPortfolioPerformance(period?: string): Promise<PortfolioPerformanceResponse> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Getting portfolio performance for period: ${period || 'default'}`);
    
    const url = API_BASE_URL + "/api/portfolio/performance/" + (period ? `?period=${period}` : '');
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch portfolio performance') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Portfolio performance fetched successfully');
    return data;
  });
}

/**
 * Get quick performance summary for dashboard
 */
export async function getPortfolioPerformanceSummary(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting portfolio performance summary...');
    
    const { data, error } = await api.GET("/api/portfolio/performance/summary/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch portfolio performance summary");
    }

    console.log('✅ Portfolio performance summary fetched successfully');
    return data;
  });
}

/**
 * Get all user positions
 */
export async function getPositions(): Promise<any[]> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting portfolio positions...');
    
    const response = await fetch(API_BASE_URL + "/api/portfolio/positions/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch positions') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Portfolio positions fetched successfully');
    return data;
  });
}

/**
 * Create a new position
 */
export async function createPosition(positionData: PositionCreateRequest): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Creating new position...', positionData);
    
    const response = await fetch(API_BASE_URL + "/api/portfolio/positions/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify(positionData),
    });

    if (!response.ok) {
      const error = new Error('Failed to create position') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Position created successfully');
    return data;
  });
}

/**
 * Get detailed position information
 */
export async function getPosition(positionId: string): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Getting position ${positionId}...`);
    
    const response = await fetch(API_BASE_URL + `/api/portfolio/positions/${positionId}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch position details') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Position details fetched successfully');
    return data;
  });
}

/**
 * Update position price
 */
export async function updatePositionPrice(
  positionId: string, 
  newPrice: number
): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Updating price for position ${positionId} to ${newPrice}...`);
    
    const response = await fetch(API_BASE_URL + `/api/portfolio/positions/${positionId}/update_price/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify({ current_price: newPrice.toString() }),
    });

    if (!response.ok) {
      const error = new Error('Failed to update position price') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Position price updated successfully');
    return data;
  });
}

/**
 * Delete/close a position
 */
export async function deletePosition(positionId: string): Promise<void> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Deleting position ${positionId}...`);
    
    const { error } = await api.DELETE("/api/portfolio/positions/{position_id}/", {
      params: {
        path: { position_id: positionId },
      },
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error) {
      throw new Error("Failed to delete position");
    }

    console.log('✅ Position deleted successfully');
  });
}

/**
 * Get portfolio allocation breakdown
 */
export async function getPortfolioAllocation(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting portfolio allocation...');
    
    const { data, error } = await api.GET("/api/portfolio/positions/allocation/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch portfolio allocation");
    }

    console.log('✅ Portfolio allocation fetched successfully');
    return data;
  });
}

/**
 * Get portfolio snapshots with optional date filtering
 */
export async function getSnapshots(): Promise<any[]> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting portfolio snapshots...');
    
    const { data, error } = await api.GET("/api/portfolio/snapshots/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch snapshots");
    }

    console.log('✅ Portfolio snapshots fetched successfully');
    return data;
  });
}

/**
 * Create a new portfolio snapshot
 */
export async function createSnapshot(request?: SnapshotCreateRequest): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Creating portfolio snapshot...', request);
    
    const response = await fetch(API_BASE_URL + "/api/portfolio/snapshots/create_snapshot/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify(request || {
        snapshot_date: new Date().toISOString().split('T')[0],
        force_recreate: false,
      }),
    });

    if (!response.ok) {
      const error = new Error('Failed to create snapshot') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Portfolio snapshot created successfully');
    return data;
  });
}

/**
 * Get the most recent portfolio snapshot
 */
export async function getLatestSnapshot(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting latest portfolio snapshot...');
    
    const { data, error } = await api.GET("/api/portfolio/snapshots/latest/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch latest snapshot");
    }

    console.log('✅ Latest portfolio snapshot fetched successfully');
    return data;
  });
}

/**
 * Get chart data for visualization
 */
export async function getChartData(period?: string): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Getting chart data for period: ${period || 'default'}...`);
    
    const { data, error } = await api.GET("/api/portfolio/snapshots/chart_data/", {
      params: {
        query: period ? { period } : {},
      },
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch chart data");
    }

    console.log('✅ Chart data fetched successfully');
    return data;
  });
}

/**
 * Get performance metrics with optional period filtering
 */
export async function getPerformanceMetrics(): Promise<any[]> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting performance metrics...');
    
    const { data, error } = await api.GET("/api/portfolio/metrics/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch performance metrics");
    }

    console.log('✅ Performance metrics fetched successfully');
    return data;
  });
}

/**
 * Calculate performance metrics for a specified period
 */
export async function calculateMetrics(
  metricsRequest: MetricsCalculationRequest
): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Calculating performance metrics...', metricsRequest);
    
    const response = await fetch(API_BASE_URL + "/api/portfolio/metrics/calculate/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
      body: JSON.stringify(metricsRequest),
    });

    if (!response.ok) {
      const error = new Error('Failed to calculate performance metrics') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();

    console.log('✅ Performance metrics calculated successfully');
    return data;
  });
}

/**
 * Compare performance metrics across multiple periods
 */
export async function compareMetrics(periods?: string): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log(`🔄 Comparing metrics across periods: ${periods || 'default'}...`);
    
    const { data, error } = await api.GET("/api/portfolio/metrics/compare/", {
      params: {
        query: periods ? { periods } : {},
      },
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to compare metrics");
    }

    console.log('✅ Metrics comparison fetched successfully');
    return data;
  });
}

/**
 * Get performance metrics summary for all periods
 */
export async function getMetricsSummary(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting metrics summary...');
    
    const { data, error } = await api.GET("/api/portfolio/metrics/summary/", {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (error || !data) {
      throw new Error("Failed to fetch metrics summary");
    }

    console.log('✅ Metrics summary fetched successfully');
    return data;
  });
}

// Exchange API Types (based on generated schema)
export interface MarketDataSnapshot {
  id: string;
  symbol: string;
  price: string;
  change: string;
  change_percent: string;
  volume: number;
  bid: string;
  ask: string;
  spread: string;
  spread_percent: string;
  timestamp?: string;
  exchange?: string;
  created_at: string;
  updated_at: string;
}

export interface ExchangeStatus {
  status: string;
  message: string;
  uptime?: string;
  connected_clients?: number;
}

/**
 * EXCHANGE API FUNCTIONS
 */

/**
 * Get exchange system status
 */
export async function getExchangeStatus(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting exchange status...');
    
    const response = await fetch(API_BASE_URL + "/api/exchange/api/v1/status/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch exchange status') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Exchange status fetched successfully');
    return data;
  });
}

/**
 * Get market data for all symbols
 */
export async function getMarketData(): Promise<MarketDataSnapshot[]> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting market data...');
    
    const response = await fetch(API_BASE_URL + "/api/exchange/api/v1/market-data/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch market data') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Market data fetched successfully');
    return data;
  });
}

/**
 * Get current prices for symbols
 */
export async function getCurrentPrices(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting current prices...');
    
    const response = await fetch(API_BASE_URL + "/api/exchange/api/v1/market-data/current_prices/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch current prices') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Current prices fetched successfully');
    return data;
  });
}

/**
 * Get supported symbols
 */
export async function getSupportedSymbols(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting supported symbols...');
    
    const response = await fetch(API_BASE_URL + "/api/exchange/api/v1/market-data/supported_symbols/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch supported symbols') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Supported symbols fetched successfully');
    return data;
  });
}

/**
 * Get market statistics
 */
export async function getMarketStatistics(): Promise<any> {
  return makeAuthenticatedRequest(async () => {
    console.log('🔄 Getting market statistics...');
    
    const response = await fetch(API_BASE_URL + "/api/exchange/api/v1/market-data/statistics/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getAccessToken()}`,
        "Origin": window.location.origin,
      },
    });

    if (!response.ok) {
      const error = new Error('Failed to fetch market statistics') as any;
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    console.log('✅ Market statistics fetched successfully');
    return data;
  });
}

// Default export for convenience
export default api;
