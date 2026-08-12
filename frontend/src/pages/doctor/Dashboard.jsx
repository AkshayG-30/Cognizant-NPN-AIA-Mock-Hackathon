import { Card } from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { useAuth } from "@/lib/auth";



export default function DoctorDashboard() {

  const { user } = useAuth();

  const [appts, setAppts] = useState([]);

  const [patients, setPatients] = useState([]);

  useEffect(() => {

    api.get("/appointments?scope=upcoming").then((r) => setAppts(r.data)).catch(() => {});

    api.get("/doctor/patients").then((r) => setPatients(r.data)).catch(() => {});

  }, []);

  const today = new Date().toISOString().slice(0, 10);

  const todays = appts.filter((a) => a.date === today);

  const slots = ["09:00","09:30","10:00","10:30","11:00","11:30","14:00","14:30","15:00","15:30"];

  const map = new Map(todays.map((a) => [a.time, a]));



  return (

    <div className="space-y-6">

      <div>

        <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight">Good morning, {user?.name?.split(" ")[1] || user?.name}</h1>

        <p className="text-slate-600 mt-1">Here's what needs your attention today.</p>

      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

        <Stat label="Today's Appointments" value={todays.length} />

        <Stat label="Pending Referrals" value={4} />

        <Stat label="Patients" value={patients.length} />

        <Stat label="Completion Rate" value="96%" />

      </div>

      <Card className="p-6">

        <div className="font-display text-xl font-semibold mb-3">Today's Schedule</div>

        <div className="divide-y divide-slate-100">

          {slots.map((s) => {

            const a = map.get(s);

            return (

              <div key={s} className="flex items-center justify-between py-3">

                <div className="w-16 font-medium text-slate-700">{s}</div>

                {a ? (

                  <div className="flex-1 flex items-center justify-between">

                    <div>

                      <div className="font-medium">{a.patient_name}</div>

                      <div className="text-xs text-slate-500">{a.reason || "Follow-up"}</div>

                    </div>

                    <Badge className="capitalize bg-blue-600">{a.status}</Badge>

                  </div>

                ) : (

                  <div className="text-sm text-slate-500">Available</div>

                )}

              </div>

            );

          })}

        </div>

      </Card>

    </div>

  );

}

function Stat({ label, value }) {

  return (

    <Card className="p-4">

      <div className="text-xs text-slate-500">{label}</div>

      <div className="mt-1 font-display text-2xl font-semibold">{value}</div>

    </Card>

  );

}





