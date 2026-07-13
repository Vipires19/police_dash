import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/types";
import { APPROVER_ROLES, canRegisterCompensationRole, isDejemAdminRole } from "@/types";
import * as authApi from "@/services/authApi";
import { ApiError } from "@/services/api";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  isApprover: boolean;
  isDejemAdmin: boolean;
  canRegisterCompensation: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (payload: authApi.RegisterPayload) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = "token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const me = await authApi.meRequest(token);
      setUser(me);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      } else if (e instanceof Error) {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const res = await authApi.loginRequest({ email, password });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setToken(res.access_token);
    const me = await authApi.meRequest(res.access_token);
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const register = useCallback(async (payload: authApi.RegisterPayload) => {
    setError(null);
    await authApi.registerRequest(payload);
  }, []);

  const isApprover = useMemo(
    () => (user ? APPROVER_ROLES.includes(user.role) : false),
    [user],
  );

  const isDejemAdmin = useMemo(
    () => (user ? isDejemAdminRole(user.role) : false),
    [user],
  );

  const canRegisterCompensation = useMemo(
    () => (user ? canRegisterCompensationRole(user.role) : false),
    [user],
  );

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      error,
      isApprover,
      isDejemAdmin,
      canRegisterCompensation,
      login,
      logout,
      register,
      refreshUser,
    }),
    [
      token,
      user,
      loading,
      error,
      isApprover,
      isDejemAdmin,
      canRegisterCompensation,
      login,
      logout,
      register,
      refreshUser,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return ctx;
}
