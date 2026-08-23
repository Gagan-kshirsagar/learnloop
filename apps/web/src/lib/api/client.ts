import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/stores/authStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach in-memory access token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: auto-refresh on 401 with loop protection
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // Exclude auth routes from retry loop
    const url = originalRequest.url || "";
    if (
      url.includes("/auth/refresh") ||
      url.includes("/auth/login") ||
      url.includes("/auth/register") ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          },
          reject: (err) => reject(err),
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken =
      useAuthStore.getState().refreshToken ||
      (typeof window !== "undefined" ? localStorage.getItem("learnloop_refresh_token") : null);

    if (!refreshToken) {
      isRefreshing = false;
      useAuthStore.getState().clearAuth();
      return Promise.reject(error);
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token } = response.data;
      useAuthStore.getState().setAccessToken(access_token);
      if (typeof window !== "undefined") {
        localStorage.setItem("learnloop_refresh_token", refresh_token);
      }

      processQueue(null, access_token);
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return apiClient(originalRequest);
    } catch (refreshErr) {
      processQueue(refreshErr, null);
      useAuthStore.getState().clearAuth();
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }
);
