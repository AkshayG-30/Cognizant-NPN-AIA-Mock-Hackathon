import { Card } from "@/components/ui/card";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, CartesianGrid } from "recharts";

import { Users, UserCog, CalendarClock, ClipboardList, TimerReset, Network } from "lucide-react";



const COLORS = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#14B8A6", "#EF4444", "#6366F1", "#F97316"];



export default function AdminDashboard() {

  const [stats, setStats] = useState(null);

  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {

    api.get("/admin/stats").then((r) => setStats(r.data));

    api.get("/admin/analytics").then((r) => setAnalytics(r.data));

  }, []);

  return (

    <div className="space-y-6">

      <div>

        <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight">CarePath AI Operations</h1>

        <p className="text-slate-600 mt-1">Monitor specialty access, referrals and provider capacity.</p>

      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">

        <Metric icon={Users} label="Patients" value={stats?.patients} />

        <Metric icon={UserCog} label="Doctors" value={stats?.doctors} />

        <Metric icon={CalendarClock} label="Appointments" value={stats?.appointments} />

        <Metric icon={ClipboardList} label="Referrals" value={stats?.referrals} />

        <Metric icon={TimerReset} label="Avg Wait" value={stats ? `${stats.avg_wait}d` : "—"} />

        <Metric icon={Network} label="Network Adequacy" value={stats ? `${stats.network_adequacy}%` : "—"} />

      </div>



      <div className="grid lg:grid-cols-3 gap-6">

        <ChartCard title="Referral Volume" className="lg:col-span-2">

          <ResponsiveContainer width="100%" height={260}>

            <BarChart data={analytics?.referral_volume || []}>

              <CartesianGrid stroke="#F1F5F9" vertical={false} />

              <XAxis dataKey="month" stroke="#94A3B8" fontSize={12} tickLine={false} />

              <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />

              <Tooltip cursor={{ fill: "#F1F5F9" }} />

              <Bar dataKey="count" fill="#2563EB" radius={[6,6,0,0]} />

            </BarChart>

          </ResponsiveContainer>

        </ChartCard>

        <ChartCard title="Specialty Distribution">

          <ResponsiveContainer width="100%" height={260}>

            <PieChart>

              <Pie data={analytics?.specialty_distribution || []} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>

                {(analytics?.specialty_distribution || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}

              </Pie>

              <Tooltip />

            </PieChart>

          </ResponsiveContainer>

        </ChartCard>

      </div>



      <div className="grid lg:grid-cols-3 gap-6">

        <ChartCard title="Wait-Time Trend" className="lg:col-span-2">

          <ResponsiveContainer width="100%" height={260}>

            <LineChart data={analytics?.wait_time_trend || []}>

              <CartesianGrid stroke="#F1F5F9" vertical={false} />

              <XAxis dataKey="month" stroke="#94A3B8" fontSize={12} tickLine={false} />

              <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />

              <Tooltip />

              <Line type="monotone" dataKey="wait" stroke="#0EA5E9" strokeWidth={2.5} dot={{ r: 3 }} />

            </LineChart>

          </ResponsiveContainer>

        </ChartCard>

        <ChartCard title="Provider Quality">

          <ResponsiveContainer width="100%" height={260}>

            <BarChart data={analytics?.quality || []}>

              <CartesianGrid stroke="#F1F5F9" vertical={false} />

              <XAxis dataKey="band" stroke="#94A3B8" fontSize={12} tickLine={false} />

              <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />

              <Tooltip />

              <Bar dataKey="count" fill="#10B981" radius={[6,6,0,0]} />

            </BarChart>

          </ResponsiveContainer>

        </ChartCard>

      </div>



      <ChartCard title="Geographic Access">

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">

          {(analytics?.geographic || []).map((g) => (

            <div key={g.zone} className="rounded-lg bg-slate-50 border border-slate-200 p-4">

              <div className="text-xs text-slate-500">{g.zone}</div>

              <div className="font-display text-2xl font-semibold mt-1">{g.coverage}%</div>

              <div className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">

                <div className="h-full bg-blue-600" style={{ width: `${g.coverage}%` }} />

              </div>

            </div>

          ))}

        </div>

      </ChartCard>

    </div>

  );

}



function Metric({ icon: Icon, label, value }) {

  return (

    <Card className="p-4">

      <div className="flex items-center gap-2 text-slate-500 text-xs"><Icon className="h-3.5 w-3.5" />{label}</div>

      <div className="font-display text-2xl font-semibold mt-1">{value ?? "—"}</div>

    </Card>

  );

}

function ChartCard({ title, className = "", children }) {

  return (

    <Card className={`p-6 ${className}`}>

      <div className="font-medium mb-3">{title}</div>

      {children}

    </Card>

  );

}





