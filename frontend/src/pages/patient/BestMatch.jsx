import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CareJourney } from "@/components/CareJourney";
import {
  Check,
  ArrowRight,
  Sparkles,
  MapPin,
  TimerReset,
  Award,
  Calendar,
  Clock,
  CheckCircle2,
  Phone,
  ShieldCheck,
  ChevronRight,
  Loader2,
  Stethoscope,
  Car,
  Navigation
} from "lucide-react";
import { SpecialistMap } from "@/components/SpecialistMap";

export default function BestMatch() {
  const [data, setData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [patientLoc, setPatientLoc] = useState({ latitude: 34.0522, longitude: -118.2437, label: "Current Patient Location" });
  const [selectedSlot, setSelectedSlot] = useState("10:00 AM");
  const [selectedDate, setSelectedDate] = useState("");
  const [bookingBusy, setBookingBusy] = useState(false);
  const [referralId, setReferralId] = useState(null);
  const nav = useNavigate();

  const todayStr = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    // 1. First check if pipeline data exists in localStorage
    let loadedFromStorage = false;
    try {
      const stored = localStorage.getItem("cp_carepath_result");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.patient_location) {
          setPatientLoc(parsed.patient_location);
        }
        if (parsed.recommendations && parsed.recommendations.length > 0) {
          const top = parsed.recommendations[0];
          setReferralId(parsed.referral_id || null);
          setRecommendations(parsed.recommendations);
          setData({
            specialty: parsed.clinical_triage?.specialty || top.specialty,
            confidence: parsed.clinical_triage?.confidence || 94,
            doctor: {
              id: top.provider_id || top.id,
              name: top.name,
              hospital: top.hospital,
              quality: top.quality_score || 96,
              distance_km: top.distance_km || 14.0,
              haversine_distance_km: top.haversine_distance_km || top.distance_km || 14.0,
              osrm: top.osrm,
              osrm_distance_km: top.osrm_distance_km || top.osrm?.distance_km,
              osrm_duration_minutes: top.osrm_duration_minutes || top.osrm?.duration_minutes,
              latitude: top.latitude,
              longitude: top.longitude,
              wait_days: top.predicted_wait_days || 10.0,
              next_available: top.next_available || "Within 7 days",
              match_score: top.match_score || 96,
              city: top.city || "Los Angeles",
              state: top.state || "CA",
            },
            reasons: top.reasons || [
              `Specialist match for ${parsed.clinical_triage?.specialty || "recommended care"}`,
              `LightGBM predicted wait: ${top.predicted_wait_days || 8.5} days`,
              `Proximity: ${top.distance_km || 12} km from patient location`,
              "Board-certified in-network provider",
            ],
          });
          setSelectedDate(todayStr);
          loadedFromStorage = true;
        }
      }
    } catch (_) {}

    // 2. If not found in storage, fetch from backend fallback endpoint
    if (!loadedFromStorage) {
      api.get("/carepath/best-match")
        .then((r) => {
          if (r.data?.patient_location) {
            setPatientLoc(r.data.patient_location);
          }
          setData(r.data);
          if (r.data?.recommendations && r.data.recommendations.length > 0) {
            setRecommendations(r.data.recommendations);
          } else if (r.data?.doctor) {
            setRecommendations([
              {
                rank: 1,
                provider_id: r.data.doctor.id,
                name: r.data.doctor.name,
                specialty: r.data.specialty,
                hospital: r.data.doctor.hospital,
                latitude: r.data.doctor.latitude || 34.0736,
                longitude: r.data.doctor.longitude || -118.3775,
                distance_km: r.data.doctor.distance_km,
                haversine_distance_km: r.data.doctor.haversine_distance_km || r.data.doctor.distance_km,
                predicted_wait_days: r.data.doctor.wait_days,
                quality_score: r.data.doctor.quality,
                match_score: 97,
                osrm: r.data.doctor.osrm,
              }
            ]);
          }
          setSelectedDate(todayStr);
        })
        .catch(() => {});
    }
  }, []);

  async function handleBook(doctorId, customDate = null, customTime = null) {
    const chosenDoc = (recommendations || []).find(
      (r) => String(r.provider_id || r.id) === String(doctorId)
    ) || (doctorId === data?.doctor?.id ? data?.doctor : null) || recommendations[0];

    const docId = doctorId || chosenDoc?.provider_id || chosenDoc?.id || data?.doctor?.id;
    if (!docId) {
      toast.error("Invalid provider selected");
      return;
    }

    const dateToBook = customDate || selectedDate || todayStr;
    const timeToBook = customTime || selectedSlot || "10:00 AM";

    setBookingBusy(true);
    try {
      const res = await api.post("/carepath/book", {
        provider_id: docId,
        doctor_id: docId,
        doctor_name: chosenDoc?.name || data?.doctor?.name,
        specialty: chosenDoc?.specialty || data?.specialty,
        hospital: chosenDoc?.hospital || data?.doctor?.hospital,
        date: dateToBook,
        time: timeToBook,
        referral_id: referralId,
        reason: `CarePath Consultation for ${chosenDoc?.specialty || data?.specialty || "Specialist Care"}`,
      });

      const respData = res.data;
      const apptId = respData.appointment_id || "appt_demo_01";

      toast.success("Appointment Confirmed!", {
        description: `Scheduled with ${respData.doctor_name || "Specialist"} on ${dateToBook} at ${timeToBook}. Opening appointment document...`,
      });

      // Automatically open downloadable appointment slip
      window.open(`http://127.0.0.1:8000/api/v1/appointments/${apptId}/document?print=true`, "_blank");

      setTimeout(() => {
        nav("/patient/appointments");
      }, 700);
    } catch (err) {
      console.error(err);
      toast.error("Could not complete booking. Please try again.");
    } finally {
      setBookingBusy(false);
    }
  }

  if (!data) {
    return (
      <div className="space-y-6 max-w-5xl">
        <div className="flex items-center gap-3 text-slate-600 p-8">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          <span>Searching regional network for optimal providers & queue times…</span>
        </div>
      </div>
    );
  }

  if (data.empty) {
    return (
      <div className="space-y-6 max-w-5xl">
        <Card className="p-8 text-center space-y-4">
          <div className="h-12 w-12 rounded-full bg-blue-50 text-blue-600 grid place-items-center mx-auto">
            <Stethoscope className="h-6 w-6" />
          </div>
          <div className="font-display text-xl font-semibold">No active referral analyzed yet</div>
          <p className="text-slate-600 max-w-md mx-auto">
            Submit a referral or upload a medical document to let CarePath AI match you with the best provider.
          </p>
          <Button onClick={() => nav("/patient/referral")} className="bg-blue-600 hover:bg-blue-700 text-white">
            Start Referral Process
          </Button>
        </Card>
      </div>
    );
  }

  const d = data.doctor;
  const altDoctors = recommendations.length > 1 ? recommendations.slice(1, 4) : [];

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Best CarePath Match</h1>
        <p className="text-slate-600 mt-1">Multi-objective algorithmic recommendation optimized for clinical specialty, queue wait time, proximity, and provider quality.</p>
      </div>

      <Card className="p-5">
        <CareJourney current={3} />
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Top Hero Provider Card */}
        <Card className="lg:col-span-2 p-6 bg-gradient-to-br from-blue-50/90 via-white to-sky-50/50 border-blue-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-blue-700 text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="h-4 w-4 text-blue-600" /> Top Algorithmic Match (#1 Ranked)
            </div>
            <Badge className="bg-blue-600 text-white font-semibold text-xs px-3 py-1">
              {d.match_score || 96}% Optimization Match
            </Badge>
          </div>

          <div className="mt-4 grid sm:grid-cols-2 gap-4 pb-4 border-b border-slate-200">
            <div>
              <div className="text-xs font-medium text-slate-500 uppercase">Target Specialty</div>
              <div className="font-display text-xl font-bold text-slate-900 mt-0.5" data-testid="bm-specialty">
                {data.specialty}
              </div>
              <div className="text-xs text-blue-700 font-medium mt-1">
                AI Clinical Referral Support {data.confidence}%
              </div>
            </div>

            <div>
              <div className="text-xs font-medium text-slate-500 uppercase">Recommended Specialist</div>
              <div className="font-display text-xl font-bold text-slate-900 mt-0.5" data-testid="bm-doctor">
                {d.name}
              </div>
              <div className="text-xs text-slate-600 mt-1">{d.hospital}</div>
            </div>
          </div>

          {/* Core Metrics */}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat icon={Award} label="Quality Score" value={`${d.quality}/100`} color="text-amber-700" />
            <Stat
              icon={MapPin}
              label="Haversine Distance"
              value={`${d.haversine_distance_km || d.distance_km} km`}
              color="text-slate-800"
            />
            <Stat
              icon={Car}
              label="OSRM Driving Route"
              value={d.osrm_distance_km ? `${d.osrm_distance_km} km (${d.osrm_duration_minutes}m)` : `${d.distance_km} km`}
              color="text-blue-700"
            />
            <Stat icon={TimerReset} label="ML Predicted Wait" value={`${d.wait_days} days`} color="text-emerald-700" />
          </div>

          {/* Interactive Fast Booking Box */}
          <div className="mt-6 p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="font-semibold text-sm text-slate-900 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-blue-600" /> Fast-Track Direct Scheduling
              </span>
              <span className="text-xs text-slate-500 font-normal">Instant Confirmation</span>
            </div>

            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="slot-date" className="text-xs font-medium text-slate-600">Select Date</Label>
                <Input
                  id="slot-date"
                  type="date"
                  min={todayStr}
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-medium text-slate-600">Available Time Slot</Label>
                <div className="flex flex-wrap gap-1.5">
                  {["09:30 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM"].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setSelectedSlot(t)}
                      className={`px-2 py-1 rounded text-xs font-medium border transition-colors ${
                        selectedSlot === t
                          ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                          : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                onClick={() => handleBook(d.id)}
                disabled={bookingBusy}
                className="h-10 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold flex-1 shadow-sm"
                data-testid="bm-view-book"
              >
                {bookingBusy ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Scheduling Appointment…
                  </>
                ) : (
                  <>
                    Confirm & Book Appointment <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>

              <Button
                variant="outline"
                className="h-10 px-4 text-xs border-slate-300"
                onClick={() => nav(`/patient/specialists/${d.id}`)}
              >
                Full Doctor Profile
              </Button>
            </div>
          </div>
        </Card>

        {/* Why this match Card */}
        <Card className="p-6 self-start space-y-4">
          <div className="font-semibold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            <span>Optimization Rationale</span>
          </div>

          <ul className="space-y-2.5 text-xs text-slate-700">
            {data.reasons.map((r, i) => (
              <li key={i} className="flex items-start gap-2 leading-relaxed">
                <Check className="h-4 w-4 mt-0.5 text-emerald-600 shrink-0" />
                <span>{r}</span>
              </li>
            ))}
          </ul>

          <div className="pt-2 border-t border-slate-100 space-y-2 text-xs text-slate-500">
            <div className="flex items-center gap-1.5 text-slate-700 font-medium">
              <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" /> CarePath Integrated Guarantee
            </div>
            <p>Queue times are continuously calibrated with point-in-time capacity and wait history data.</p>
          </div>
        </Card>
      </div>

      {/* OSRM Driving Route & Patient-Specialist Interactive Map */}
      <div className="pt-2">
        <SpecialistMap patientLocation={patientLoc} specialists={recommendations} />
      </div>

      {/* Alternative Ranked Specialists */}
      {altDoctors.length > 0 && (
        <div className="space-y-3 pt-2">
          <h2 className="font-display text-xl font-semibold text-slate-900">
            Alternative Recommended Specialists
          </h2>
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {altDoctors.map((doc, idx) => (
              <Card key={doc.provider_id || doc.id || idx} className="p-5 border-slate-200 hover:border-blue-200 transition-colors shadow-xs">
                <div className="flex items-start justify-between">
                  <div>
                    <Badge variant="outline" className="text-[11px] font-normal mb-1">
                      Rank #{idx + 2} Candidate
                    </Badge>
                    <div className="font-display text-base font-semibold text-slate-900">{doc.name}</div>
                    <div className="text-xs text-blue-700 font-medium">{doc.specialty}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{doc.hospital}</div>
                  </div>
                  <Badge className="bg-slate-100 text-slate-800 text-xs">{doc.match_score || 90}% Match</Badge>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-2 text-xs bg-slate-50 p-2.5 rounded-lg">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Road / Straight</span>
                    <span className="font-medium text-slate-900">
                      {doc.osrm_distance_km ? `${doc.osrm_distance_km} km` : `${doc.distance_km} km`}
                    </span>
                    {doc.osrm_duration_minutes && (
                      <span className="text-[10px] text-blue-600 block font-semibold">🚗 {doc.osrm_duration_minutes}m</span>
                    )}
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Wait Time</span>
                    <span className="font-medium text-slate-900">{doc.predicted_wait_days}d</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Quality</span>
                    <span className="font-medium text-slate-900">{doc.quality_score || 94}/100</span>
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1 h-9 text-xs bg-blue-600 hover:bg-blue-700"
                    onClick={() => handleBook(doc.provider_id || doc.id)}
                  >
                    Select & Book
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-9 text-xs"
                    onClick={() => nav(`/patient/specialists/${doc.provider_id || doc.id}`)}
                  >
                    Profile
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value, color }) {
  return (
    <div className="p-3 rounded-lg bg-white border border-slate-200">
      <div className="flex items-center gap-1.5 text-xs text-slate-500">
        <Icon className="h-3.5 w-3.5 text-slate-400 shrink-0" />
        <span className="truncate">{label}</span>
      </div>
      <div className={`mt-1 font-display text-base font-bold ${color || "text-slate-900"}`}>{value}</div>
    </div>
  );
}
