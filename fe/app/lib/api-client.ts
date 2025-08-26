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

// Types for convenience (exported from generated types)
export type LoginRequest =
  paths["/api/auth/login/"]["post"]["requestBody"]["content"]["application/json"];
export type LoginResponse =
  paths["/api/auth/login/"]["post"]["responses"]["200"]["content"]["application/json"];

export type RegisterRequest =
  paths["/api/auth/register/"]["post"]["requestBody"]["content"]["application/json"];
export type RegisterResponse =
  paths["/api/auth/register/"]["post"]["responses"]["201"]["content"]["application/json"];

export type RefreshRequest =
  paths["/api/auth/refresh/"]["post"]["requestBody"]["content"]["application/json"];
export type RefreshResponse =
  paths["/api/auth/refresh/"]["post"]["responses"]["200"]["content"]["application/json"];

export type LogoutRequest =
  paths["/api/auth/logout/"]["post"]["requestBody"]["content"]["application/json"];
export type LogoutResponse =
  paths["/api/auth/logout/"]["post"]["responses"]["200"]["content"]["application/json"];

export type ProtectedResponse =
  paths["/api/auth/protected/"]["get"]["responses"]["200"]["content"]["application/json"];

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

  try {
    const { data, error } = await api.POST("/api/auth/refresh/", {
      body: {
        refresh_token: refreshToken,
      },
    });

    if (error || !data) return false;

    storeTokens(data);
    return true;
  } catch (error) {
    console.error("Token refresh failed:", error);
    return false;
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
  const { data, error } = await api.GET("/api/auth/protected/");

  if (error || !data) {
    throw new Error(error?.error || "Failed to get user info");
  }

  return data;
}

/**
 * Link a new bank account
 */
export async function linkBankAccount(
  routingNumber: string,
  accountNumber: string,
  accountType: 'checking' | 'savings',
  accountHolderName: string
) {
  console.log('🔄 Making bank account link request to:', API_BASE_URL + "/api/banking/link-account/");
  console.log('📝 Bank account data:', { routingNumber, accountType, accountHolderName });
  
  try {
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
      throw new Error(data?.error || 'Failed to link bank account');
    }

    return data;
  } catch (error) {
    console.error('❌ Bank link error:', error);
    throw error;
  }
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
 * Initialize the API client
 * Call this once in your app initialization
 */
export function initializeApiClient() {
  // Client is initialized, no middleware setup needed for now
}

// Default export for convenience
export default api;
