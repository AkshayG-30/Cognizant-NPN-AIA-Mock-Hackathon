import { Card } from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";



export function DoctorReferrals() {

  const [items, setItems] = useState([]);

  useEffect(() => { api.get("/referrals").then((r) => setItems(r.data)).catch(() => {}); }, []);

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Referrals</h1>

      <div className="grid md:grid-cols-2 gap-4">

        {items.map((r) => (

          <Card key={r.id} className="p-5">

            <div className="flex items-center justify-between">

              <div className="font-semibold">{r.patient_name}</div>

              <Badge variant="secondary" className="capitalize">{r.urgency}</Badge>

            </div>

            <div className="mt-1 text-sm text-slate-700">{r.reason}</div>

            <div className="text-xs text-slate-500 mt-1">{r.symptoms}</div>

            {r.suggested_specialty && (

              <div className="mt-3 text-sm">

                Suggested: <span className="font-semibold text-blue-700">{r.suggested_specialty}</span>

                <span className="text-slate-500"> · {r.confidence}%</span>

              </div>

            )}

          </Card>

        ))}

        {items.length === 0 && <div className="text-slate-500 text-sm">Nothing here yet.</div>}

      </div>

    </div>

  );

}



export function DoctorPatients() {

  const [items, setItems] = useState([]);

  useEffect(() => { api.get("/doctor/patients").then((r) => setItems(r.data)).catch(() => {}); }, []);

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Patients</h1>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">

        {items.map((p) => (

          <Card key={p.id} className="p-5">

            <div className="font-display text-lg font-semibold">{p.name}</div>

            <div className="text-xs text-slate-500">{p.email}</div>

          </Card>

        ))}

        {items.length === 0 && <div className="text-slate-500 text-sm">Nothing here yet.</div>}

      </div>

    </div>

  );

}



export function DoctorSchedule() {

  const slots = ["Mon","Tue","Wed","Thu","Fri","Sat"];

  const hours = ["09:00","10:00","11:00","14:00","15:00","16:00"];

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">My Schedule</h1>

      <Card className="p-6 overflow-auto">

        <div className="grid grid-cols-7 gap-2 min-w-[600px]">

          <div />

          {slots.map((d) => <div key={d} className="text-xs font-medium text-slate-500 text-center">{d}</div>)}

          {hours.map((h) => (

            <>

              <div key={h} className="text-xs text-slate-500 pr-2 text-right">{h}</div>

              {slots.map((d, i) => (

                <div key={`${d}-${h}`} className={`h-12 rounded-md border ${i === 2 || (i === 3 && h === "10:00") ? "bg-blue-50 border-blue-200" : "border-slate-100 bg-white"}`}></div>

              ))}

            </>

          ))}

        </div>

      </Card>


    </div>

  );

}



