import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CareJourney } from "@/components/CareJourney";
import { useAuth } from "@/lib/auth";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  Search,
  Calendar,
  Sparkles,
  ArrowRight,
  ChevronRight,
  Stethoscope,
  Activity,
  CheckCircle2,
  Clock
} from "lucide-react";

export default function PatientDashboard() {
  const { user } = useAuth();
  const [appts, setAppts] = useState([]);
  const [refLatest, setRefLatest] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [reports, setReports] = useState([]);
  const nav = useNavigate();

  useEffect(() => {
    // Check local storage for active pipeline results
    try {
      const stored = localStorage.getItem("cp_carepath_result");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.clinical_triage) {
          setAnalysis({
            specialty: parsed.clinical_triage.specialty,
            confidence: parsed.clinical_triage.confidence || 95,
            priority: parsed.clinical_triage.urgency || "routine",
            reasoning: parsed.clinical_triage.summary,
            doctor_name: parsed.recommendations?.[0]?.name,
          });
        }
      }
    } catch (_) {}

    api.get("/appointments?scope=upcoming").then((r) => setAppts(r.data)).catch(() => {});
    api.get("/referrals/mine/latest").then((r) => setRefLatest(r.data)).catch(() => {});
    api.get("/ai/analyses/mine").then((r) => {
      if (r.data?.[0] && !analysis) setAnalysis(r.data[0]);
    }).catch(() => {});
    api.get("/reports/mine").then((r) => setReports(r.data)).catch(() => {});
  }, []);

  const step = appts.length > 0 ? 4 : analysis ? 3 : reports.length > 0 ? 2 : refLatest && refLatest.id ? 1 : 0;
  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-slate-900" data-testid="patient-greeting">
            {greet}, {user?.name?.split(" ")[0] || "Patient"}
          </h1>
          <p className="text-slate-600 mt-1">
            Welcome to CarePath AI — your intelligent clinical referral and appointment orchestration portal.
          </p>
        </div>

        <Button
          className="h-11 px-5 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm"
          onClick={() => nav(step >= 3 ? "/patient/best-match" : "/patient/referral")}
          data-testid="continue-journey-btn"
        >
          Continue Care Journey <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>

      <Card className="p-5 border-slate-200 shadow-sm">
        <div className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4 text-blue-600" /> Your Active Referral Pathway
        </div>
        <CareJourney current={step} />
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <QuickAction
          icon={FileText}
          label="Start Referral"
          desc="Submit symptoms & notes"
          onClick={() => nav("/patient/referral")}
          testid="qa-referral"
        />
        <QuickAction
          icon={Upload}
          label="Upload Reports"
          desc="PDFs & medical scans"
          onClick={() => nav("/patient/reports")}
          testid="qa-upload"
        />
        <QuickAction
          icon={Sparkles}
          label="AI Triage"
          desc="Groq clinical analysis"
          onClick={() => nav("/patient/ai-analysis")}
          testid="qa-analysis"
        />
        <QuickAction
          icon={Calendar}
          label="Appointments"
          desc="View care schedule"
          onClick={() => nav("/patient/appointments")}
          testid="qa-appointment"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 p-6 bg-gradient-to-br from-blue-50/90 via-white to-sky-50/50 border-blue-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-blue-700 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-blue-600" /> Recommended Care Pathway
            </div>
            <Badge variant="outline" className="text-xs bg-white border-blue-200 text-blue-800">
              AI Decision Support
            </Badge>
          </div>

          {analysis ? (
            <div className="mt-4 space-y-4">
              <div className="grid sm:grid-cols-3 gap-4 p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
                <div>
                  <div className="text-xs font-medium text-slate-500 uppercase">Target Specialty</div>
                  <div className="font-display text-xl font-bold text-slate-900 mt-0.5" data-testid="rec-specialty">
                    {analysis.specialty}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-medium text-slate-500 uppercase">AI Confidence</div>
                  <div className="font-display text-xl font-bold text-blue-700 mt-0.5" data-testid="rec-confidence">
                    {analysis.confidence}%
                  </div>
                </div>

                <div>
                  <div className="text-xs font-medium text-slate-500 uppercase">Priority</div>
                  <div className="mt-1">
                    <Badge className="capitalize bg-blue-600 text-white font-semibold">
                      {analysis.priority}
                    </Badge>
                  </div>
                </div>
              </div>

              {analysis.reasoning && (
                <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 leading-relaxed">
                  {analysis.reasoning}
                </p>
              )}

              <div className="flex flex-wrap gap-3 pt-2">
                <Button
                  onClick={() => nav("/patient/best-match")}
                  className="h-10 px-5 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm"
                  data-testid="explore-specialists"
                >
                  View Best Matched Specialists <ChevronRight className="h-4 w-4 ml-1" />
                </Button>

                <Button
                  variant="outline"
                  onClick={() => nav("/patient/ai-analysis")}
                  className="h-10 px-4 text-xs border-slate-300"
                >
                  View AI Triage Breakdown
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <p className="text-slate-600 text-sm">
                No active referral recommendation yet. Complete the referral form or upload your medical report to receive personalized specialist recommendations.
              </p>
              <Button
                onClick={() => nav("/patient/referral")}
                className="h-10 bg-blue-600 hover:bg-blue-700 text-white text-sm"
              >
                Start Referral Now <ArrowRight className="h-4 w-4 ml-1.5" />
              </Button>
            </div>
          )}
        </Card>

        <Card className="p-6 self-start space-y-4 shadow-sm border-slate-200">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-blue-600" /> Upcoming Care
            </div>
            <span
              onClick={() => nav("/patient/appointments")}
              className="text-xs text-blue-600 hover:underline cursor-pointer font-medium"
            >
              View All
            </span>
          </div>

          {appts.length === 0 ? (
            <div className="text-sm text-slate-500 py-3">No upcoming appointments scheduled yet.</div>
          ) : (
            <div className="space-y-2.5">
              {appts.slice(0, 3).map((a) => (
                <div
                  key={a.id}
                  className="p-3 rounded-lg border border-slate-100 bg-slate-50/70 space-y-1 hover:bg-blue-50/40 transition-colors cursor-pointer"
                  onClick={() => nav("/patient/appointments")}
                >
                  <div className="font-semibold text-sm text-slate-900">{a.doctor_name}</div>
                  <div className="text-xs text-blue-700 font-medium">{a.specialty}</div>
                  <div className="text-xs text-slate-500 flex items-center justify-between pt-1">
                    <span>{a.hospital}</span>
                    <span className="font-medium text-slate-700">{a.date} · {a.time}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function QuickAction({ icon: Icon, label, desc, onClick, testid }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className="card-lift group flex flex-col items-start gap-2 p-4 rounded-xl bg-white border border-slate-200 text-left hover:border-blue-300 hover:shadow-xs transition-all"
    >
      <div className="h-9 w-9 rounded-lg bg-blue-50 grid place-items-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <div className="font-semibold text-sm text-slate-900">{label}</div>
        {desc && <div className="text-xs text-slate-500">{desc}</div>}
      </div>
    </button>
  );
}
