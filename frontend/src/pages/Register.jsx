import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { CarePathLogo } from "@/components/CarePathLogo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Eye, EyeOff, Loader2, CheckCircle2, ShieldCheck } from "lucide-react";

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "patient",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const { register } = useAuth();
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErrorMessage("");

    const cleanEmail = form.email.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!form.name.trim()) {
      toast.error("Please enter your full name");
      return;
    }

    if (!emailRegex.test(cleanEmail)) {
      toast.error("Please enter a valid email address (e.g. user@gmail.com)");
      return;
    }

    if (form.password.length < 6) {
      toast.error("Password must be at least 6 characters long");
      return;
    }

    setBusy(true);

    try {
      const res = await register({
        ...form,
        email: cleanEmail,
      });

      toast.success(res?.message || "Account created successfully! Please sign in with your credentials.");

      // Direct user to login with prefilled email
      nav("/login", {
        state: {
          email: cleanEmail,
          registered: true,
        },
      });
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Registration failed. Please check your details and try again.";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">
      {/* Left branding banner */}
      <div className="hidden lg:flex flex-col justify-between p-10 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white border-r border-slate-800">
        <div className="brightness-150">
          <CarePathLogo />
        </div>

        <div className="max-w-md space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-medium border border-blue-400/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            Verified Patient & Specialist Network
          </div>

          <h1 className="font-display text-4xl sm:text-5xl font-semibold tracking-tight text-white leading-tight">
            Start your CarePath journey today.
          </h1>

          <p className="text-slate-300 text-base leading-relaxed">
            Create an account to upload clinical notes, receive queue-optimized specialist matching, and schedule priority care appointments in seconds.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2">
            {[
              "Queue-theory wait estimates",
              "Evidence-backed AI triage",
              "Direct instant booking",
              "HIPAA & FHIR compliant",
            ].map((feature) => (
              <div
                key={feature}
                className="flex items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-800/50 px-3 py-2.5 text-xs text-slate-200"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="text-xs text-slate-400">
          © 2026 CarePath AI · Clinical Decision Support System
        </div>
      </div>

      {/* Right registration form */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-slate-50/50">
        <Card className="w-full max-w-md p-6 sm:p-8 border-slate-200 shadow-md bg-white">
          <div className="lg:hidden mb-6">
            <CarePathLogo variant="compact" />
          </div>

          <h2 className="font-display text-2xl font-bold text-slate-900 tracking-tight">
            Create your account
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Sign up with your Gmail or work email to begin.
          </p>

          {errorMessage && (
            <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs leading-relaxed">
              {errorMessage}
            </div>
          )}

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-slate-700 font-medium text-xs">
                Full Name
              </Label>
              <Input
                id="name"
                placeholder="e.g. Jane Doe"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                data-testid="reg-name"
                className="h-10"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-slate-700 font-medium text-xs">
                Email Address (Gmail / Corporate)
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="e.g. yourname@gmail.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
                data-testid="reg-email"
                className="h-10"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-slate-700 font-medium text-xs">
                Password (min. 6 characters)
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  minLength={6}
                  data-testid="reg-password"
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

            <div className="space-y-1.5">
              <Label className="text-slate-700 font-medium text-xs">I am registering as</Label>
              <Select
                value={form.role}
                onValueChange={(v) => setForm({ ...form, role: v })}
              >
                <SelectTrigger data-testid="reg-role" className="h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="patient">Patient (Seeking specialist care)</SelectItem>
                  <SelectItem value="doctor">Doctor (Specialist / Provider)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              type="submit"
              disabled={busy}
              className="w-full h-11 bg-blue-700 hover:bg-blue-800 text-white font-medium shadow-sm transition-all mt-2"
              data-testid="reg-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating account…
                </>
              ) : (
                "Create account & Go to Login"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-700 font-semibold hover:underline">
              Sign in here
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
