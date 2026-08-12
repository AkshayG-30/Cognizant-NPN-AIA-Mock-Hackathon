import { Card } from "@/components/ui/card";

import { Input } from "@/components/ui/input";

import { Label } from "@/components/ui/label";

import { Button } from "@/components/ui/button";

import { Switch } from "@/components/ui/switch";

import { useAuth } from "@/lib/auth";

import { toast } from "sonner";

import { useState } from "react";



export function ProfilePage() {

  const { user } = useAuth();

  return (

    <div className="space-y-6 max-w-3xl">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Profile</h1>

        <p className="text-slate-600 mt-1">How you appear on CarePath AI.</p>

      </div>

      <Card className="p-6 space-y-4">

        <div className="grid sm:grid-cols-2 gap-4">

          <Field label="Full name" value={user?.name} />

          <Field label="Email" value={user?.email} />

          <Field label="Role" value={user?.role} />

          <Field label="User ID" value={user?.id} mono />

        </div>

      </Card>

    </div>

  );

}



export function SettingsPage() {

  const [prefs, setPrefs] = useState({ emails: true, sms: false, contrast: false });

  return (

    <div className="space-y-6 max-w-2xl">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Settings</h1>

        <p className="text-slate-600 mt-1">Preferences and accessibility.</p>

      </div>

      <Card className="p-6 space-y-4">

        <Toggle label="Email notifications" checked={prefs.emails} onChange={(v) => setPrefs({...prefs, emails: v})} />

        <Toggle label="SMS reminders" checked={prefs.sms} onChange={(v) => setPrefs({...prefs, sms: v})} />

        <Toggle label="High contrast mode" checked={prefs.contrast} onChange={(v) => setPrefs({...prefs, contrast: v})} />

        <Button onClick={() => toast.success("Preferences saved")}>Save changes</Button>

      </Card>

    </div>

  );

}



export function HelpPage() {

  return (

    <div className="space-y-6 max-w-3xl">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Help & Support</h1>

        <p className="text-slate-600 mt-1">We're here whenever you need us.</p>

      </div>

      <Card className="p-6 space-y-3">

        <FAQ q="What is CarePath AI?" a="An intelligent path to the right care — from your health information to the specialist that fits you." />

        <FAQ q="Is the AI diagnosing me?" a="No. CarePath AI provides clinical decision support and specialty recommendations only. Diagnosis is done by licensed clinicians." />

        <FAQ q="How do I book an appointment?" a="Open Find Specialists, choose a doctor, and click View & Book." />

        <FAQ q="How do I contact support?" a="Reach us at support@carepath.ai — average response time under 6 hours." />

      </Card>

    </div>

  );

}



function Field({ label, value, mono }) {

  return (

    <div className="space-y-1.5">

      <Label>{label}</Label>

      <Input value={value || ""} readOnly className={mono ? "font-mono text-xs" : ""} />

    </div>

  );

}

function Toggle({ label, checked, onChange }) {

  return (

    <div className="flex items-center justify-between py-1">

      <div className="text-sm">{label}</div>

      <Switch checked={checked} onCheckedChange={onChange} />

    </div>

  );

}

function FAQ({ q, a }) {

  return (

    <div className="border-b border-slate-100 pb-3 last:border-0">

      <div className="font-medium">{q}</div>

      <div className="text-sm text-slate-600 mt-1">{a}</div>

    </div>

  );

}





