import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authApi } from "../services/api";
import type { AuthCredentials, User } from "../types/auth";

const TOKEN_STORAGE_KEY = "ai_document_rag_access_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (credentials: AuthCredentials) => Promise<void>;
  register: (credentials: AuthCredentials) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY),
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      if (!token) {
        if (!cancelled) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const currentUser = await authApi.me(token);
        if (!cancelled) setUser(currentUser);
      } catch {
        if (!cancelled) clearAuth();
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void restore();

    return () => {
      cancelled = true;
    };
  }, [clearAuth, token]);

  const login = useCallback(async (credentials: AuthCredentials) => {
    const response = await authApi.login(credentials);
    localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setUser(await authApi.me(response.access_token));
  }, []);

  const register = useCallback(
    (credentials: AuthCredentials) => authApi.register(credentials),
    [],
  );

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      login,
      register,
      logout: clearAuth,
    }),
    [clearAuth, isLoading, login, register, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

export { TOKEN_STORAGE_KEY };
