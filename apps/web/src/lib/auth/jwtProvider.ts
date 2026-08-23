import { apiClient } from "@/lib/api/client";
import {
  AuthProviderClient,
  AuthResult,
  LoginData,
  MeResult,
  RegisterData,
  Tokens,
} from "./types";

export class JwtAuthProviderClient implements AuthProviderClient {
  async register(data: RegisterData): Promise<AuthResult> {
    const res = await apiClient.post<AuthResult>("/api/v1/auth/register", data);
    return res.data;
  }

  async login(data: LoginData): Promise<AuthResult> {
    const res = await apiClient.post<AuthResult>("/api/v1/auth/login", data);
    return res.data;
  }

  async guest(): Promise<AuthResult> {
    const res = await apiClient.post<AuthResult>("/api/v1/auth/guest");
    return res.data;
  }

  async refresh(refreshToken: string): Promise<Tokens> {
    const res = await apiClient.post<Tokens>("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    return res.data;
  }

  async getMe(accessToken?: string): Promise<MeResult> {
    const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined;
    const res = await apiClient.get<MeResult>("/api/v1/auth/me", { headers });
    return res.data;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post("/api/v1/auth/logout");
    } catch {
      // Stateless logout: proceed even if API call fails
    }
  }
}

export const jwtAuthProvider = new JwtAuthProviderClient();
