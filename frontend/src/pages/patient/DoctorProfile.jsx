import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { MapPin, TimerReset, Award, Phone, Calendar, Loader2, CheckCircle2, ShieldCheck, Clock } from "lucide-react";
import { CareJourney } from "@/components/CareJourney";

export default function DoctorProfile() {
  const { id } = useParams();
  const [doctor, setDoctor] = useState(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("10:00 AM");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/doctors/${id}`).then((r) => setDoctor(r.data)).catch(() => {});
  }, [id]);

  const today = new Date();
  const min = today.toISOString().slice(0, 10);

  useEffect(() => {
    if (!date) setDate(min);
  }, [min]);

  async function book() {
    if (!date) {
      toast.error("Please select a date for your appointment.");
      return;
    }

    setBusy(true);
    let refId = null;
    try {
      const stored = localStorage.getItem("cp_carepath_result");
      if (stored) {
        const parsed = JSON.parse(stored);
        refId = parsed.referral_id || null;
      }
    } catch (_) {}

    try {
      // Use carepath booking endpoint with fallback
      await api.post("/carepath/book", {
        provider_id: id,
        doctor_id: id,
        date,
        time,
        referral_id: refId,
        reason: `Specialist Consultation with ${doctor?.name || "Doctor"}`,
      });

      toast.success("Appointment Confirmed!", {
        description: `Scheduled with ${doctor?.name || "Specialist"} on ${date} at ${time}.`,
      });

      setTimeout(() => {
        nav("/patient/appointments");
      }, 600);
    } catch {
      try {
        await api.post("/appointments", {
          doctor_id: id,
          provider_id: id,
          date,
          time,
          referral_id: refId,
          reason: "Specialist consultation",
        });
        toast.success("Appointment Confirmed!");
        nav("/patient/appointments");
      } catch {
        toast.error("Could not complete booking. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (!doctor) {
    return (
      <div className="space-y-6 max-w-5xl">
        <div className="flex items-center gap-3 text-slate-600 p-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          <span>Loading specialist profile…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Specialist Profile</h1>
        <p className="text-slate-600 mt-1">Verified in-network specialist matched via CarePath AI clinical routing.</p>
      </div>

      <Card className="p-5">
        <CareJourney current={4} />
      </Card>

      <Card className="p-6 shadow-sm border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="font-display text-3xl font-bold text-slate-900">{doctor.name}</div>
            <div className="text-blue-700 font-semibold text-lg mt-0.5">{doctor.specialty}</div>
            <div className="text-sm text-slate-500 mt-1 flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-slate-400" /> {doctor.hospital}
            </div>
          </div>

          <div className="flex flex-wrap gap-2.5 text-sm">
            <Chip icon={Award} label={`Quality Score: ${doctor.quality}/100`} />
            <Chip icon={MapPin} label={`${doctor.distance_km} km away`} />
            <Chip icon={TimerReset} label={`~${doctor.wait_days} days predicted wait`} />
            <Chip icon={Phone} label={doctor.phone || "+1 (555) 234-8901"} />
          </div>
        </div>

        <p className="mt-5 text-slate-700 leading-relaxed max-w-3xl text-sm border-t border-slate-100 pt-4">
          {doctor.bio}
        </p>
      </Card>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="md:col-span-2 p-6 shadow-sm border-slate-200">
          <div className="font-display text-xl font-semibold text-slate-900 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-600" /> Schedule Your Appointment
          </div>

          <div className="mt-5 grid sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="date">Appointment Date</Label>
              <Input
                id="date"
                type="date"
                min={min}
                value={date}
                onChange={(e) => setDate(e.target.value)}
                data-testid="book-date"
              />
            </div>

            <div className="space-y-1.5">
              <Label>Select Time Slot</Label>
              <div className="grid grid-cols-4 gap-2">
                {["09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTime(t)}
                    data-testid={`slot-${t}`}
                    className={`px-2 py-2 rounded-md text-xs font-medium border transition-colors ${
                      time === t
                        ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                        : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Button
            className="mt-6 h-11 px-8 bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm"
            onClick={book}
            disabled={busy}
            data-testid="confirm-book"
          >
            {busy ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Confirming…
              </>
            ) : (
              "Confirm Booking"
            )}
          </Button>
        </Card>

        <Card className="p-6 self-start space-y-4">
          <div className="font-semibold text-slate-900">Next Available Opening</div>
          <div className="text-xl font-bold text-blue-700 font-display">
            {doctor.next_available || "This Week"}
          </div>

          <div className="text-xs text-slate-600 space-y-2.5 pt-2 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>Board Certified & State Licensed</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-blue-600 shrink-0" />
              <span>Accepts Direct Electronic Referrals</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-500 shrink-0" />
              <span>Queue-optimized wait time</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

function Chip({ icon: Icon, label }) {
  return (
    <div className="flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-slate-700 text-xs font-medium">
      <Icon className="h-3.5 w-3.5 text-slate-500" />
      {label}
    </div>
  );
}
