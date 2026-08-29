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

  // Save tokens and user data to localStorage
  const saveAuthState = useCallback((accessToken, refreshToken, userData) => {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      }
      if (userData) {
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
      }
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

  // Load tokens and user data from localStorage on mount and verify with /auth/me
  useEffect(() => {
    const loadAuthState = async () => {
      try {
        const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
        const userData = localStorage.getItem(USER_DATA_KEY);

        if (accessToken) {
          if (userData) {
            setUser(JSON.parse(userData));
            setIsAuthenticated(true);
          }

          // Verify with backend
          try {
            const me = await authService.getCurrentUser(accessToken);
            if (me) {
              const updatedUserData = {
                user_id: me.user_id,
                email: me.email,
                display_name: me.display_name,
                tier: me.tier,
              };
              setUser(updatedUserData);
              setIsAuthenticated(true);
              localStorage.setItem(USER_DATA_KEY, JSON.stringify(updatedUserData));
            }
          } catch (meErr) {
            console.warn('Session verification failed on mount:', meErr.message);
          }
        }
      } catch (error) {
        console.error('Failed to load auth state:', error);
        clearAuthState();
      } finally {
        setIsLoading(false);
      }
    };

    loadAuthState();
  }, [clearAuthState]);

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
        error: error.message || 'Invalid email or password',
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
        error: error.message || 'Registration failed',
      };
    }
  }, [saveAuthState]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
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
      saveAuthState(response.access_token, response.refresh_token, null);
      return response.access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  }, [logout, saveAuthState]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
