export interface User {
  id: string;
  email: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface ApiErrorShape {
  detail?: string | Array<{ msg?: string }>;
}
