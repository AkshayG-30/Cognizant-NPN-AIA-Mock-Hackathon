import { Navigate } from "react-router-dom";

import { useAuth } from "@/lib/auth";

import { AppLayout } from "@/components/AppLayout";



export function RequireAuth({ role, children }) {

  const { user, loading } = useAuth();

  if (loading) return <div className="min-h-screen grid place-items-center text-slate-500">Loading CarePath AI…</div>;

  if (!user) return <Navigate to="/login" replace />;

  if (role && user.role !== role) return <Navigate to={`/${user.role}`} replace />;

  return <AppLayout>{children}</AppLayout>;

}





