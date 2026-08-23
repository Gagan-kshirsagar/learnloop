import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authProvider } from "@/lib/auth";
import { AuthResult, LoginData, MeResult, RegisterData } from "@/lib/auth/types";
import { useAuthStore } from "@/stores/authStore";

export const AUTH_KEYS = {
  me: ["auth", "me"] as const,
};

export function useMeQuery() {
  const status = useAuthStore((state) => state.status);
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery<MeResult>({
    queryKey: AUTH_KEYS.me,
    queryFn: async () => {
      const data = await authProvider.getMe(accessToken || undefined);
      useAuthStore.getState().setUserAndTenant(data.user, data.tenant);
      return data;
    },
    enabled: status === "authenticated" || status === "guest" || !!accessToken,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useRegisterMutation() {
  const queryClient = useQueryClient();

  return useMutation<AuthResult, Error, RegisterData>({
    mutationFn: (data: RegisterData) => authProvider.register(data),
    onSuccess: (data) => {
      useAuthStore.getState().setAuth(data.user, data.tenant, data.tokens, false);
      queryClient.setQueryData(AUTH_KEYS.me, { user: data.user, tenant: data.tenant });
    },
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();

  return useMutation<AuthResult, Error, LoginData>({
    mutationFn: (data: LoginData) => authProvider.login(data),
    onSuccess: (data) => {
      useAuthStore.getState().setAuth(data.user, data.tenant, data.tokens, false);
      queryClient.setQueryData(AUTH_KEYS.me, { user: data.user, tenant: data.tenant });
    },
  });
}

export function useGuestMutation() {
  const queryClient = useQueryClient();

  return useMutation<AuthResult, Error, void>({
    mutationFn: () => authProvider.guest(),
    onSuccess: (data) => {
      useAuthStore.getState().setAuth(data.user, data.tenant, data.tokens, true);
      queryClient.setQueryData(AUTH_KEYS.me, { user: data.user, tenant: data.tenant });
    },
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await authProvider.logout();
    },
    onSettled: () => {
      useAuthStore.getState().clearAuth();
      queryClient.removeQueries({ queryKey: ["auth"] });
    },
  });
}
