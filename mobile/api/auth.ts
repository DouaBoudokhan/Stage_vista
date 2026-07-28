// Authentication API calls
import axios from 'axios';
import { API_BASE_URL } from '../constants/config';
import type { LoginRequest, LoginResponse } from '../types';

// Auth endpoints don't use the interceptor-based instance to avoid circular refresh
export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const { data } = await axios.post<LoginResponse>(
      `${API_BASE_URL}/auth/login`,
      credentials,
    );
    return data;
  },

  refresh: async (refreshToken: string) => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    return data;
  },

  logout: async (refreshToken: string) => {
    await axios.post(`${API_BASE_URL}/auth/logout`, {
      refresh_token: refreshToken,
    });
  },
};
