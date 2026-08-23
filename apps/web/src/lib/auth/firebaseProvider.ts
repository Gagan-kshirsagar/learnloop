import {
  AuthProviderClient,
  AuthResult,
  LoginData,
  MeResult,
  RegisterData,
  Tokens,
} from "./types";

export class FirebaseAuthProviderClient implements AuthProviderClient {
  async register(_data: RegisterData): Promise<AuthResult> {
    void _data;
    throw new Error("Firebase auth provider is not configured");
  }

  async login(_data: LoginData): Promise<AuthResult> {
    void _data;
    throw new Error("Firebase auth provider is not configured");
  }

  async guest(): Promise<AuthResult> {
    throw new Error("Firebase auth provider is not configured");
  }

  async refresh(_refreshToken: string): Promise<Tokens> {
    void _refreshToken;
    throw new Error("Firebase auth provider is not configured");
  }

  async getMe(_accessToken?: string): Promise<MeResult> {
    void _accessToken;
    throw new Error("Firebase auth provider is not configured");
  }

  async logout(): Promise<void> {
    throw new Error("Firebase auth provider is not configured");
  }
}

export const firebaseAuthProvider = new FirebaseAuthProviderClient();
