import { Card } from "@/components/ui/card";

import { Button } from "@/components/ui/button";

import { Input } from "@/components/ui/input";

import { Badge } from "@/components/ui/badge";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

import { Link, useNavigate } from "react-router-dom";

import { MapPin, TimerReset, Award, Search } from "lucide-react";



export default function FindSpecialists() {

  const [doctors, setDoctors] = useState([]);

  const [specialties, setSpecialties] = useState([]);

  const [specialty, setSpecialty] = useState("all");

  const [q, setQ] = useState("");

  const nav = useNavigate();



  useEffect(() => {

    api.get("/specialties").then((r) => setSpecialties(r.data)).catch(() => {});

  }, []);

  useEffect(() => {

    const params = new URLSearchParams();

    if (specialty !== "all") params.set("specialty", specialty);

    if (q) params.set("q", q);

    api.get(`/doctors?${params}`).then((r) => setDoctors(r.data)).catch(() => {});

  }, [specialty, q]);



  return (

    <div className="space-y-6">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Find the right specialist</h1>

        <p className="text-slate-600 mt-1">Filter by specialty or search by name and hospital.</p>

      </div>



      <Card className="p-4 flex flex-col md:flex-row gap-3 md:items-center">

        <div className="relative flex-1">

          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />

          <Input placeholder="Search doctors, specialties, hospitals…" value={q} onChange={(e) => setQ(e.target.value)} className="pl-9" data-testid="spec-search" />

        </div>

        <Select value={specialty} onValueChange={setSpecialty}>

          <SelectTrigger className="w-56" data-testid="spec-filter"><SelectValue /></SelectTrigger>

          <SelectContent>

            <SelectItem value="all">All specialties</SelectItem>

            {specialties.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}

          </SelectContent>

        </Select>

      </Card>



      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">

        {doctors.map((d) => (

          <Card key={d.id} className="p-5 card-lift" data-testid={`doctor-card-${d.id}`}>

            <div className="flex items-start justify-between">

              <div>

                <div className="font-display text-lg font-semibold">{d.name}</div>

                <div className="text-sm text-blue-700 font-medium">{d.specialty}</div>

                <div className="text-xs text-slate-500 mt-0.5">{d.hospital}</div>

              </div>

              <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 border border-blue-100">Q {d.quality}</Badge>

            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">

              <Meta icon={MapPin} label={`${d.distance_km} km`} />

              <Meta icon={TimerReset} label={`${d.wait_days}d wait`} />

              <Meta icon={Award} label={`${d.quality}/100`} />

            </div>

            <div className="mt-4 text-sm text-slate-600">Next available <span className="text-slate-900 font-medium">{d.next_available}</span></div>

            <div className="mt-4 flex gap-2">

              <Button className="flex-1" onClick={() => nav(`/patient/specialists/${d.id}`)} data-testid={`view-book-${d.id}`}>View & Book</Button>

              <Link to={`/patient/specialists/${d.id}`}><Button variant="outline">Profile</Button></Link>

            </div>

          </Card>

        ))}

      </div>

      {doctors.length === 0 && <div className="text-slate-500 text-sm">Nothing here yet.</div>}

    </div>

  );

}



function Meta({ icon: Icon, label }) {

  return (

    <div className="flex items-center gap-1.5 text-slate-600">

      <Icon className="h-3.5 w-3.5" />

      <span>{label}</span>

    </div>

  );

}





