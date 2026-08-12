import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { CarePathLogo } from "@/components/CarePathLogo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, CheckCircle2, UserCheck, Stethoscope, Shield } from "lucide-react";

export default function Login() {
  const location = useLocation();
  const nav = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successNotice, setSuccessNotice] = useState("");

  useEffect(() => {
    // If redirected from registration with pre-filled email
    if (location.state?.email) {
      setEmail(location.state.email);
    } else {
      // Default to demo patient if first visit
      setEmail("patient@carepath.ai");
      setPassword("Patient@2026");
    }

    if (location.state?.registered) {
      setSuccessNotice("Account created successfully! Please enter your password to sign in.");
    }
  }, [location.state]);

  function fillDemo(demoEmail, demoPass) {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMessage("");
    toast.info(`Filled credentials for ${demoEmail}`);
  }

  async function submit(e) {
    e.preventDefault();
    setErrorMessage("");
    setSuccessNotice("");

    const cleanEmail = email.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!cleanEmail) {
      toast.error("Please enter your email address");
      return;
    }

    if (!emailRegex.test(cleanEmail)) {
      toast.error("Please enter a valid email address (e.g. user@gmail.com)");
      return;
    }

    if (!password) {
      toast.error("Please enter your password");
      return;
    }

    setBusy(true);

    try {
      const u = await login(cleanEmail, password);
      toast.success(`Welcome back, ${u.name || u.email}!`);
      nav(`/${u.role || "patient"}`);
    } catch (err) {
      const detailMsg =
        err?.response?.data?.detail ||
        err?.message ||
        "Invalid email or password. Please verify your credentials.";
      setErrorMessage(detailMsg);
      toast.error(detailMsg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">
      {/* Left branding banner */}
      <div className="hidden lg:flex flex-col justify-between p-10 bg-slate-900 border-r border-slate-800 text-white">
        <div className="brightness-150">
          <CarePathLogo />
        </div>

        <div className="max-w-md space-y-6">
          <h1 className="font-display text-4xl sm:text-5xl font-semibold tracking-tight text-white leading-tight">
            Your intelligent path to the right care.
          </h1>

          <p className="text-slate-300 text-base leading-relaxed">
            From your clinical notes to queue-optimized specialist scheduling. Sign in with your registered credentials to access your care dashboard.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2">
            {[
              "Right Care.",
              "Right Path.",
              "AI-Assisted Triage.",
              "Human-First.",
            ].map((t) => (
              <div
                key={t}
                className="rounded-lg border border-slate-700/70 bg-slate-800/60 px-3.5 py-2.5 text-xs text-slate-200 font-medium"
              >
                {t}
              </div>
            ))}
          </div>
        </div>

        <div className="text-xs text-slate-400">
          © 2026 CarePath AI · Clinical Decision Support System
        </div>
      </div>

      {/* Right sign-in card */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-slate-50/50">
        <Card className="w-full max-w-md p-6 sm:p-8 border-slate-200 shadow-md bg-white">
          <div className="lg:hidden mb-6">
            <CarePathLogo variant="compact" />
          </div>

          <h2 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
            Sign in to CarePath
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Enter your email (Gmail/Work) and password to continue.
          </p>

          {successNotice && (
            <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{successNotice}</span>
            </div>
          )}

          {errorMessage && (
            <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs leading-relaxed">
              {errorMessage}
            </div>
          )}

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-slate-700 font-medium text-xs">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="name@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="login-email"
                className="h-10"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-slate-700 font-medium text-xs">
                  Password
                </Label>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  data-testid="login-password"
                  className="h-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={busy}
              className="w-full h-11 bg-blue-700 hover:bg-blue-800 text-white font-medium shadow-sm transition-all mt-2"
              data-testid="login-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Verifying credentials…
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500">
            Don't have an account?{" "}
            <Link to="/register" className="text-blue-700 font-semibold hover:underline">
              Create an account
            </Link>
          </div>

          {/* Quick Demo Credentials */}
          <div className="mt-6 rounded-lg bg-slate-50 border border-slate-200/80 p-3.5 space-y-2">
            <div className="text-xs font-semibold text-slate-700">Quick Test Accounts:</div>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => fillDemo("patient@carepath.ai", "Patient@2026")}
                className="flex items-center justify-center gap-1 px-2 py-1.5 rounded text-[11px] font-medium bg-white border border-slate-200 hover:bg-blue-50 hover:border-blue-200 text-slate-700 transition-colors"
              >
                <UserCheck className="w-3 h-3 text-blue-600" /> Patient
              </button>
              <button
                type="button"
                onClick={() => fillDemo("sarah.williams@carepath.ai", "Doctor@2026")}
                className="flex items-center justify-center gap-1 px-2 py-1.5 rounded text-[11px] font-medium bg-white border border-slate-200 hover:bg-emerald-50 hover:border-emerald-200 text-slate-700 transition-colors"
              >
                <Stethoscope className="w-3 h-3 text-emerald-600" /> Doctor
              </button>
              <button
                type="button"
                onClick={() => fillDemo("admin@carepath.ai", "Admin@2026")}
                className="flex items-center justify-center gap-1 px-2 py-1.5 rounded text-[11px] font-medium bg-white border border-slate-200 hover:bg-purple-50 hover:border-purple-200 text-slate-700 transition-colors"
              >
                <Shield className="w-3 h-3 text-purple-600" /> Admin
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
