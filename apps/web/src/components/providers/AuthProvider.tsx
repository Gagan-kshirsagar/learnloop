"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { authProvider } from "@/lib/auth";
import { useAuthStore } from "@/stores/authStore";

export function AuthProvider({ children }: { children: ReactNode }) {
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    async function bootstrapSession() {
      const storedRefreshToken =
        typeof window !== "undefined"
          ? localStorage.getItem("learnloop_refresh_token")
          : null;

      if (!storedRefreshToken) {
        useAuthStore.getState().setStatus("unauthenticated");
        return;
      }

      try {
        const tokens = await authProvider.refresh(storedRefreshToken);
        useAuthStore.getState().setAccessToken(tokens.access_token);
        if (typeof window !== "undefined") {
          localStorage.setItem("learnloop_refresh_token", tokens.refresh_token);
        }
        const me = await authProvider.getMe(tokens.access_token);
        useAuthStore.getState().setUserAndTenant(me.user, me.tenant);
        const isGuest = me.user.email.includes("@guest.learnloop.dev") || me.user.email.includes("@demo.learnloop.dev");
        useAuthStore.getState().setStatus(isGuest ? "guest" : "authenticated");
      } catch {
        useAuthStore.getState().clearAuth();
      }
    }

    bootstrapSession();
  }, []);

  return <>{children}</>;
}
