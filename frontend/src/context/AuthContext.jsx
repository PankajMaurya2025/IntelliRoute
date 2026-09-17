import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { login as apiLogin, signup as apiSignup, fetchCurrentUser } from "../api/auth";

const AuthContext = createContext(null);

const TOKEN_KEY = "intelliroute_token";
const USER_KEY = "intelliroute_user";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [loading, setLoading] = useState(true);

  // On first load, if a token exists, validate it against /api/auth/me
  // rather than trusting the cached user object blindly.
  useEffect(() => {
    let cancelled = false;

    async function validate() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const current = await fetchCurrentUser();
        if (!cancelled) {
          setUser(current);
          localStorage.setItem(USER_KEY, JSON.stringify(current));
        }
      } catch {
        if (!cancelled) {
          setUser(null);
          setToken(null);
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    validate();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin({ email, password });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const signup = useCallback(async (name, email, password) => {
    const data = await apiSignup({ name, email, password });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = { user, token, loading, isAuthenticated: !!token && !!user, login, signup, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
