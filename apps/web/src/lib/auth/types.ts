export type UserRole = "owner" | "instructor" | "student";
export type UserStatus = "active" | "invited" | "inactive";

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResult {
  user: User;
  tenant: Tenant;
  tokens: Tokens;
}

export interface MeResult {
  user: User;
  tenant: Tenant;
}

export interface RegisterData {
  org_name: string;
  email: string;
  password: string;
  name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthProviderClient {
  register(data: RegisterData): Promise<AuthResult>;
  login(data: LoginData): Promise<AuthResult>;
  guest(): Promise<AuthResult>;
  refresh(refreshToken: string): Promise<Tokens>;
  getMe(accessToken?: string): Promise<MeResult>;
  logout(): Promise<void>;
}
