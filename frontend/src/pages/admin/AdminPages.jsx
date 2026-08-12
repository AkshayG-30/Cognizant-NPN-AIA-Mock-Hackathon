import { Card } from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";

import { Input } from "@/components/ui/input";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { Search } from "lucide-react";



export function AdminDoctors() {

  const [items, setItems] = useState([]);

  const [q, setQ] = useState("");

  useEffect(() => { api.get(`/doctors?q=${q}`).then((r) => setItems(r.data)).catch(() => {}); }, [q]);

  return (

    <div className="space-y-4">

      <div className="flex items-end justify-between gap-3">

        <div>

          <h1 className="font-display text-3xl font-semibold tracking-tight">Doctors</h1>

          <p className="text-slate-600 mt-1">Provider directory across the network.</p>

        </div>

        <div className="relative w-64">

          <Search className="absolute h-4 w-4 left-3 top-1/2 -translate-y-1/2 text-slate-400" />

          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search doctors" className="pl-9" />

        </div>

      </div>

      <Card>

        <Table>

          <TableHeader>

            <TableRow>

              <TableHead>Name</TableHead><TableHead>Specialty</TableHead><TableHead>Hospital</TableHead>

              <TableHead>Quality</TableHead><TableHead>Wait</TableHead><TableHead>Distance</TableHead>

            </TableRow>

          </TableHeader>

          <TableBody>

            {items.map((d) => (

              <TableRow key={d.id}>

                <TableCell className="font-medium">{d.name}</TableCell>

                <TableCell>{d.specialty}</TableCell>

                <TableCell className="text-slate-600">{d.hospital}</TableCell>

                <TableCell><Badge variant="secondary">{d.quality}</Badge></TableCell>

                <TableCell>{d.wait_days}d</TableCell>

                <TableCell>{d.distance_km}km</TableCell>

              </TableRow>

            ))}

          </TableBody>

        </Table>

      </Card>

    </div>

  );

}



export function AdminHospitals() {

  const [items, setItems] = useState([]);

  useEffect(() => { api.get("/hospitals").then((r) => setItems(r.data)); }, []);

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Hospitals</h1>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">

        {items.map((h) => (

          <Card key={h.id} className="p-5">

            <div className="font-display text-lg font-semibold">{h.name}</div>

            <div className="text-xs text-slate-500 mt-0.5">{h.city} · {h.zone}</div>

            <div className="mt-3 grid grid-cols-2 text-sm">

              <div><span className="text-slate-500">Beds </span>{h.beds}</div>

              <div><span className="text-slate-500">Rating </span>{h.rating}</div>

            </div>

            <div className="mt-3 flex flex-wrap gap-1.5">

              {(h.specialties || []).map((s) => <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-slate-100">{s}</span>)}

            </div>

          </Card>

        ))}

      </div>

    </div>

  );

}



export function AdminReferrals() {

  const [items, setItems] = useState([]);

  useEffect(() => { api.get("/referrals").then((r) => setItems(r.data)); }, []);

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Referrals</h1>

      <Card>

        <Table>

          <TableHeader>

            <TableRow><TableHead>Patient</TableHead><TableHead>Reason</TableHead><TableHead>Urgency</TableHead><TableHead>Suggested</TableHead><TableHead>Confidence</TableHead></TableRow>

          </TableHeader>

          <TableBody>

            {items.map((r) => (

              <TableRow key={r.id}>

                <TableCell className="font-medium">{r.patient_name}</TableCell>

                <TableCell className="text-slate-600">{r.reason}</TableCell>

                <TableCell><Badge variant="secondary" className="capitalize">{r.urgency}</Badge></TableCell>

                <TableCell>{r.suggested_specialty || "—"}</TableCell>

                <TableCell>{r.confidence ? `${r.confidence}%` : "—"}</TableCell>

              </TableRow>

            ))}

          </TableBody>

        </Table>

      </Card>

    </div>

  );

}



export function AdminAppointments() {

  const [items, setItems] = useState([]);

  useEffect(() => { api.get("/appointments").then((r) => setItems(r.data)); }, []);

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Appointments</h1>

      <Card>

        <Table>

          <TableHeader>

            <TableRow><TableHead>Date</TableHead><TableHead>Time</TableHead><TableHead>Patient</TableHead><TableHead>Doctor</TableHead><TableHead>Specialty</TableHead><TableHead>Status</TableHead></TableRow>

          </TableHeader>

          <TableBody>

            {items.map((a) => (

              <TableRow key={a.id}>

                <TableCell>{a.date}</TableCell><TableCell>{a.time}</TableCell>

                <TableCell>{a.patient_name}</TableCell><TableCell>{a.doctor_name}</TableCell>

                <TableCell>{a.specialty}</TableCell>

                <TableCell><Badge className="capitalize bg-blue-600">{a.status}</Badge></TableCell>

              </TableRow>

            ))}

          </TableBody>

        </Table>

      </Card>

    </div>

  );

}



export function AdminAuditLogs() {

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Audit Logs</h1>

      <Card className="p-6 text-slate-500 text-sm">Nothing here yet.</Card>

    </div>

  );

}



export function AdminSchedules() {

  return (

    <div className="space-y-4">

      <h1 className="font-display text-3xl font-semibold tracking-tight">Schedules</h1>

      <Card className="p-6 text-slate-500 text-sm">Schedule overview coming soon.</Card>

    </div>

  );

}





