import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import API_BASE_URL from "@/config/api";
import { Calendar, MapPin, Clock, CheckCircle2, User, Stethoscope, Plus, FileText } from "lucide-react";
import { CareJourney } from "@/components/CareJourney";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export default function Appointments({ scope = "upcoming" }) {
  const [items, setItems] = useState([]);
  const { user } = useAuth();
  const nav = useNavigate();

  const load = () => {
    api.get(`/appointments?scope=${scope}`).then((r) => setItems(r.data)).catch(() => {});
  };

  useEffect(() => {
    load();
  }, [scope]);

  const isPatient = user?.role === "patient";

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight capitalize">
            {scope} Appointments
          </h1>
          <p className="text-slate-600 mt-1">Your confirmed specialist appointments and care schedule.</p>
        </div>

        {isPatient && (
          <Button onClick={() => nav("/patient/referral")} className="bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="h-4 w-4 mr-1.5" /> Book New Referral
          </Button>
        )}
      </div>

      {isPatient && (
        <Card className="p-5 border-slate-200 shadow-sm">
          <CareJourney current={4} />
        </Card>
      )}

      {items.length === 0 ? (
        <Card className="p-10 text-center space-y-3">
          <div className="h-12 w-12 rounded-full bg-blue-50 text-blue-600 grid place-items-center mx-auto">
            <Calendar className="h-6 w-6" />
          </div>
          <div className="font-semibold text-slate-800">No scheduled appointments found</div>
          <p className="text-slate-500 text-sm max-w-md mx-auto">
            You don't have any appointments on your calendar yet. Complete your clinical referral to book with top matched specialists.
          </p>
          {isPatient && (
            <Button onClick={() => nav("/patient/referral")} className="mt-2 bg-blue-600 text-white">
              Start Referral Process
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {items.map((a) => (
            <Card key={a.id} className="p-5 border-slate-200 shadow-xs hover:border-blue-200 transition-colors" data-testid={`appt-${a.id}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-display text-lg font-bold text-slate-900">{a.doctor_name}</div>
                  <div className="text-sm text-blue-700 font-semibold">{a.specialty}</div>
                </div>
                <Badge className="capitalize bg-emerald-100 text-emerald-800 border-emerald-200">
                  <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-700" />
                  {a.status}
                </Badge>
              </div>

              <div className="mt-4 space-y-2 text-sm text-slate-700 bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600 shrink-0" />
                  <span className="font-medium text-slate-900">{a.date}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600 shrink-0" />
                  <span>{a.time}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-slate-500 shrink-0" />
                  <span className="text-slate-600 truncate">{a.hospital}</span>
                </div>
              </div>

              {a.notes && (
                <div className="mt-3 text-xs text-slate-500 italic">
                  Note: {a.notes}
                </div>
              )}

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-500 font-medium">CarePath Reference Slip</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => window.open(`${API_BASE_URL}/appointments/${a.id}/document?print=true`, "_blank")}
                  className="h-8 text-xs font-semibold text-blue-700 border-blue-200 bg-blue-50/50 hover:bg-blue-100/70"
                >
                  <FileText className="h-3.5 w-3.5 mr-1 text-blue-600" /> Download Document
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
