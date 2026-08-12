import { Card } from "@/components/ui/card";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, CartesianGrid } from "recharts";



const COLORS = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6", "#EF4444"];



function useAnalytics() {

  const [d, setD] = useState(null);

  useEffect(() => { api.get("/admin/analytics").then((r) => setD(r.data)); }, []);

  return d;

}

function Wrapper({ title, subtitle, children }) {

  return (

    <div className="space-y-4">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">{title}</h1>

        <p className="text-slate-600 mt-1">{subtitle}</p>

      </div>

      <Card className="p-6">{children}</Card>

    </div>

  );

}



export function ReferralAnalytics() {

  const d = useAnalytics();

  return (

    <Wrapper title="Referral Analytics" subtitle="Referral volume and specialty mix.">

      <div className="grid lg:grid-cols-2 gap-6">

        <ResponsiveContainer width="100%" height={280}>

          <BarChart data={d?.referral_volume || []}>

            <CartesianGrid stroke="#F1F5F9" vertical={false} />

            <XAxis dataKey="month" stroke="#94A3B8" fontSize={12} />

            <YAxis stroke="#94A3B8" fontSize={12} axisLine={false} tickLine={false} />

            <Tooltip />

            <Bar dataKey="count" fill="#2563EB" radius={[6,6,0,0]} />

          </BarChart>

        </ResponsiveContainer>

        <ResponsiveContainer width="100%" height={280}>

          <PieChart>

            <Pie data={d?.specialty_distribution || []} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100}>

              {(d?.specialty_distribution || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}

            </Pie>

            <Tooltip />

          </PieChart>

        </ResponsiveContainer>

      </div>

    </Wrapper>

  );

}



export function WaitTimeAnalytics() {

  const d = useAnalytics();

  return (

    <Wrapper title="Wait-Time Analytics" subtitle="Trailing 6-month wait time in days.">

      <ResponsiveContainer width="100%" height={320}>

        <LineChart data={d?.wait_time_trend || []}>

          <CartesianGrid stroke="#F1F5F9" vertical={false} />

          <XAxis dataKey="month" stroke="#94A3B8" fontSize={12} />

          <YAxis stroke="#94A3B8" fontSize={12} axisLine={false} tickLine={false} />

          <Tooltip />

          <Line type="monotone" dataKey="wait" stroke="#0EA5E9" strokeWidth={2.5} dot={{ r: 3 }} />

        </LineChart>

      </ResponsiveContainer>

    </Wrapper>

  );

}



export function NetworkAccess() {

  const d = useAnalytics();

  return (

    <Wrapper title="Network Access" subtitle="Geographic coverage by zone.">

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">

        {(d?.geographic || []).map((g) => (

          <div key={g.zone} className="rounded-lg bg-slate-50 border border-slate-200 p-4">

            <div className="text-xs text-slate-500">{g.zone}</div>

            <div className="font-display text-2xl font-semibold mt-1">{g.coverage}%</div>

            <div className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">

              <div className="h-full bg-blue-600" style={{ width: `${g.coverage}%` }} />

            </div>

          </div>

        ))}

      </div>

    </Wrapper>

  );

}



export function ProviderQuality() {

  const d = useAnalytics();

  return (

    <Wrapper title="Provider Quality" subtitle="Quality score distribution.">

      <ResponsiveContainer width="100%" height={320}>

        <BarChart data={d?.quality || []}>

          <CartesianGrid stroke="#F1F5F9" vertical={false} />

          <XAxis dataKey="band" stroke="#94A3B8" fontSize={12} />

          <YAxis stroke="#94A3B8" fontSize={12} axisLine={false} tickLine={false} />

          <Tooltip />

          <Bar dataKey="count" fill="#10B981" radius={[6,6,0,0]} />

        </BarChart>

      </ResponsiveContainer>

    </Wrapper>

  );

}





