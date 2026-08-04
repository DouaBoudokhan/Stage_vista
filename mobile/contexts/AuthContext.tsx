// Authentication Context and Provider
import React, { createContext, useContext, useState, useEffect } from 'react';
import { secureAuth } from '../services/auth';
import { storage } from '../services/storage';
import { authApi } from '../api/auth';
import { STORAGE_KEYS } from '../constants/config';
import type { User, LoginRequest } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on app start
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setIsLoading(true);
    try {
      const accessToken = await secureAuth.getAccessToken();
      const userData = await storage.getObject<User>(STORAGE_KEYS.USER_DATA);
      
      if (accessToken && userData) {
        setUser(userData);
      } else {
        // Clear anything corrupted
        await secureAuth.clearTokens();
        await storage.remove(STORAGE_KEYS.USER_DATA);
        setUser(null);
      }
    } catch (e) {
      console.error('Check auth error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      // Call real backend login API
      const response = await authApi.login(credentials);
      
      // Save real JWT tokens securely
      await secureAuth.saveTokens({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });

      // Create user object (extract from JWT or use credentials)
      const userData: User = {
        id: credentials.email, // Use email as ID for now
        name: credentials.email.split('@')[0], // Extract name from email
        email: credentials.email,
        role: 'admin', // Default role
      };
      
      // Save user details
      await storage.setObject(STORAGE_KEYS.USER_DATA, userData);
      setUser(userData);
    } catch (error: any) {
      setUser(null);
      console.error('Login error:', error);
      const errorMsg = error?.response?.data?.detail || error?.message || 'Login failed';
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      const refreshToken = await secureAuth.getRefreshToken();
      if (refreshToken) {
        try {
          await authApi.logout(refreshToken);
        } catch (e) {
          // Ignore network errors on logout to guarantee local clean up
        }
      }
    } finally {
      await secureAuth.clearTokens();
      await storage.remove(STORAGE_KEYS.USER_DATA);
      setUser(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
