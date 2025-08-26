import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { isAuthenticated, clearTokens, getUserInfo } from '../lib/api-client';

export function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);
  const [userInfo, setUserInfo] = useState<{ userId: number; email?: string } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const authenticated = isAuthenticated();
      setIsLoggedIn(authenticated);
      if (authenticated) {
        setUserInfo(getUserInfo());
      } else {
        setUserInfo(null);
      }
      return authenticated;
    };

    // Initial check
    checkAuth();

    // Check periodically (every minute)
    const interval = setInterval(() => {
      if (!checkAuth()) {
        // Token expired, clear tokens and redirect
        clearTokens();
        navigate('/login');
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [navigate]);

  const logout = () => {
    clearTokens();
    setIsLoggedIn(false);
    setUserInfo(null);
    navigate('/login');
  };

  return {
    isLoggedIn,
    isLoading: isLoggedIn === null,
    userInfo,
    logout,
  };
}

export function useRequireAuth() {
  const { isLoggedIn, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      navigate('/login');
    }
  }, [isLoggedIn, isLoading, navigate]);

  return { isLoggedIn, isLoading };
}