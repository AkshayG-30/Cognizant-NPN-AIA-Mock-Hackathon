import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("cp_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("cp_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    // Verify session token with backend
    api.get("/auth/me")
      .then((r) => {
        if (r.data) {
          setUser(r.data);
          localStorage.setItem("cp_user", JSON.stringify(r.data));
        }
      })
      .catch((err) => {
        // If unauthorized or token invalid, clear stale credentials
        if (err?.response?.status === 401 || err?.response?.status === 403) {
          localStorage.removeItem("cp_token");
          localStorage.removeItem("cp_user");
          setUser(null);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const cleanEmail = (email || "").trim();
    const { data } = await api.post("/auth/login", {
      email: cleanEmail,
      password: password,
    });

    if (data?.token && data?.user) {
      localStorage.setItem("cp_token", data.token);
      localStorage.setItem("cp_user", JSON.stringify(data.user));
      setUser(data.user);
      return data.user;
    }
    throw new Error("Invalid response from authentication service.");
  };

  const register = async (payload) => {
    const cleanEmail = (payload.email || "").trim();
    const { data } = await api.post("/auth/register", {
      name: payload.name?.trim(),
      email: cleanEmail,
      password: payload.password,
      role: payload.role || "patient",
    });
    return data;
  };

  const logout = () => {
    localStorage.removeItem("cp_token");
    localStorage.removeItem("cp_user");
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
