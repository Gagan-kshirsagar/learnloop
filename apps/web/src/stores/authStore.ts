import { create } from "zustand";
import { Tenant, User } from "@/lib/auth/types";

export type AuthStatus = "loading" | "authenticated" | "guest" | "unauthenticated";

interface AuthState {
  status: AuthStatus;
  user: User | null;
  tenant: Tenant | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, tenant: Tenant, tokens: { access_token: string; refresh_token: string }, isGuest?: boolean) => void;
  setUserAndTenant: (user: User, tenant: Tenant) => void;
  setAccessToken: (token: string | null) => void;
  setStatus: (status: AuthStatus) => void;
  clearAuth: () => void;
}

const REFRESH_TOKEN_KEY = "learnloop_refresh_token";

export const useAuthStore = create<AuthState>((set) => ({
  status: "loading",
  user: null,
  tenant: null,
  accessToken: null,
  refreshToken: typeof window !== "undefined" ? localStorage.getItem(REFRESH_TOKEN_KEY) : null,

  setAuth: (user, tenant, tokens, isGuest = false) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    }
    set({
      status: isGuest ? "guest" : "authenticated",
      user,
      tenant,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    });
  },

  setUserAndTenant: (user, tenant) => {
    set((state) => ({
      user,
      tenant,
      status: state.status === "loading" || state.status === "unauthenticated" ? "authenticated" : state.status,
    }));
  },

  setAccessToken: (token) => {
    set({ accessToken: token });
  },

  setStatus: (status) => {
    set({ status });
  },

  clearAuth: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
    set({
      status: "unauthenticated",
      user: null,
      tenant: null,
      accessToken: null,
      refreshToken: null,
    });
  },
}));
