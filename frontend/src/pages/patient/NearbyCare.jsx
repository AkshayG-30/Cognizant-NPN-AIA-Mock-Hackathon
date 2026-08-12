import { Card } from "@/components/ui/card";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { MapPin, Building2, Star } from "lucide-react";



export default function NearbyCare() {

  const [hospitals, setHospitals] = useState([]);

  useEffect(() => { api.get("/hospitals").then((r) => setHospitals(r.data)).catch(() => {}); }, []);

  return (

    <div className="space-y-6">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Nearby care</h1>

        <p className="text-slate-600 mt-1">Trusted hospitals and clinics near you.</p>

      </div>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">

        {hospitals.map((h) => (

          <Card key={h.id} className="p-5 card-lift">

            <div className="flex items-center gap-3">

              <div className="h-10 w-10 rounded-lg bg-blue-50 grid place-items-center text-blue-700"><Building2 className="h-5 w-5" /></div>

              <div>

                <div className="font-display text-lg font-semibold">{h.name}</div>

                <div className="text-xs text-slate-500 flex items-center gap-1"><MapPin className="h-3 w-3" />{h.city} · {h.zone}</div>

              </div>

            </div>

            <div className="mt-4 flex items-center justify-between text-sm">

              <div className="flex items-center gap-1 text-amber-600"><Star className="h-4 w-4 fill-amber-500 stroke-amber-500" />{h.rating}</div>

              <div className="text-slate-600">{h.beds} beds</div>

            </div>

            <div className="mt-3 flex flex-wrap gap-1.5">

              {(h.specialties || []).map((s) => (

                <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">{s}</span>

              ))}

            </div>

          </Card>

        ))}

      </div>

    </div>

  );

}





