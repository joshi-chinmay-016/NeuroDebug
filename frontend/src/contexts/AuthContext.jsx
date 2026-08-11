import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

const ACCESS_TOKEN_KEY = 'neurodebug_access_token';
const REFRESH_TOKEN_KEY = 'neurodebug_refresh_token';
const USER_DATA_KEY = 'neurodebug_user_data';

const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refreshAccessToken: async () => {},
});

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load tokens and user data from localStorage on mount
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
        const userData = localStorage.getItem(USER_DATA_KEY);

        if (accessToken && userData) {
          setUser(JSON.parse(userData));
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Failed to load auth state:', error);
        // Clear corrupted data
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_DATA_KEY);
      } finally {
        setIsLoading(false);
      }
    };

    loadAuthState();
  }, []);

  // Save tokens and user data to localStorage
  const saveAuthState = useCallback((accessToken, refreshToken, userData) => {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
    } catch (error) {
      console.error('Failed to save auth state:', error);
    }
  }, []);

  // Clear tokens and user data from localStorage
  const clearAuthState = useCallback(() => {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);
    } catch (error) {
      console.error('Failed to clear auth state:', error);
    }
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    try {
      const response = await authService.login(email, password);
      const userData = {
        user_id: response.user_id,
        email: response.email,
        display_name: response.display_name,
        tier: response.tier,
      };

      saveAuthState(response.access_token, response.refresh_token, userData);
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Login failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail?.message || 'Login failed',
      };
    }
  }, [saveAuthState]);

  // Register function
  const register = useCallback(async (email, password, displayName = null) => {
    try {
      const response = await authService.register(email, password, displayName);
      const userData = {
        user_id: response.user_id,
        email: response.email,
        display_name: response.display_name,
        tier: response.tier,
      };

      saveAuthState(response.access_token, response.refresh_token, userData);
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail?.message || 'Registration failed',
      };
    }
  }, [saveAuthState]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      clearAuthState();
      setUser(null);
      setIsAuthenticated(false);
    }
  }, [clearAuthState]);

  // Refresh access token
  const refreshAccessToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await authService.refreshToken(refreshToken);
      const userData = {
        user_id: response.user_id,
        email: response.email,
        display_name: response.display_name,
        tier: response.tier,
      };

      saveAuthState(response.access_token, response.refresh_token, userData);
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear auth state on refresh failure
      clearAuthState();
      setUser(null);
      setIsAuthenticated(false);
      return { success: false, error: 'Session expired' };
    }
  }, [saveAuthState, clearAuthState]);

  // Get access token for API calls
  const getAccessToken = useCallback(() => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }, []);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshAccessToken,
    getAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
