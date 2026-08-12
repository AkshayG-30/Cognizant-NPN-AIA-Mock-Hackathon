import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Sparkles, Loader2, ArrowRight, FileText, CheckCircle2, Activity, Cpu, Stethoscope, AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { CareJourney } from "@/components/CareJourney";

export default function AIAnalysis() {
  const [reports, setReports] = useState([]);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [customText, setCustomText] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    // Check local storage for recent CarePath pipeline results
    try {
      const stored = localStorage.getItem("cp_carepath_result");
      if (stored) {
        const parsed = JSON.parse(stored);
        setPipelineData(parsed);
        if (parsed.clinical_triage) {
          setResult({
            specialty: parsed.clinical_triage.specialty,
            confidence: parsed.clinical_triage.confidence || 94,
            priority: parsed.clinical_triage.urgency || "routine",
            source: parsed.document?.filename ? "OCR Document + Groq NLP" : "Clinical NLP Triage",
            reasoning: parsed.clinical_triage.summary,
            symptoms: parsed.clinical_triage.symptoms || [],
            conditions: parsed.clinical_triage.conditions || [],
          });
        }
      }
    } catch (_) {}

    api.get("/reports/mine").then((r) => setReports(r.data)).catch(() => {});
    api.get("/ai/analyses/mine").then((r) => setHistory(r.data)).catch(() => {});
  }, []);

  async function runOrchestration(presetText = null) {
    setBusy(true);
    const textToRun = presetText || customText || (reports.length ? reports.map(r => `${r.name}: ${r.notes}`).join(". ") : "Patient with severe chest pressure on exertion and hyperlipidemia requiring cardiology evaluation.");

    try {
      const formData = new FormData();
      formData.append("clinical_text", textToRun);
      formData.append("urgency", "routine");
      formData.append("zip_code", "90024");
      formData.append("max_distance_km", "150");

      const res = await api.post("/carepath/process", formData);
      const data = res.data;

      if (data && data.success) {
        localStorage.setItem("cp_carepath_result", JSON.stringify(data));
        setPipelineData(data);
        const mappedResult = {
          specialty: data.clinical_triage.specialty,
          confidence: data.clinical_triage.confidence || 95,
          priority: data.clinical_triage.urgency || "routine",
          source: data.document?.filename ? "RapidOCR + Groq Llama-3.1" : "Groq Clinical AI",
          reasoning: data.clinical_triage.summary,
          symptoms: data.clinical_triage.symptoms || [],
          conditions: data.clinical_triage.conditions || [],
        };
        setResult(mappedResult);
        setHistory((h) => [mappedResult, ...h]);
        toast.success(`Triage complete: ${data.clinical_triage.specialty}`);
      } else {
        toast.error("Analysis could not be completed.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Analysis pipeline encountered an error.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">AI Clinical Triage & Analysis</h1>
        <p className="text-slate-600 mt-1">CarePath AI reviews clinical documents, lab reports, and symptoms using Groq LLM clinical reasoning and LightGBM wait-time prediction.</p>
      </div>

      <Card className="p-5">
        <CareJourney current={2} />
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 bg-gradient-to-br from-sky-50/80 via-white to-blue-50/40 border-sky-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-blue-800 font-semibold">
                <Sparkles className="h-5 w-5 text-blue-600" />
                <span>CarePath AI Clinical Decision Support</span>
              </div>
              <Badge variant="outline" className="bg-white text-blue-700 border-blue-200 font-medium">
                Groq + LightGBM + OR-Tools
              </Badge>
            </div>

            <p className="text-sm text-slate-600 mt-2">
              Run real-time multi-objective clinical routing on your referral data and medical records.
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
              <Button
                className="h-10 px-5 bg-blue-600 hover:bg-blue-700 font-medium text-white shadow-sm"
                onClick={() => runOrchestration()}
                disabled={busy}
                data-testid="run-ai"
              >
                {busy ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Orchestrating Pipeline…
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2 text-sky-200" /> Run AI Triage
                  </>
                )}
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="h-10 text-xs"
                onClick={() => runOrchestration("Patient with recurrent chest pain, elevated cardiac enzymes, and palpitations on exertion.")}
                disabled={busy}
              >
                Test Cardiology Case
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-10 text-xs"
                onClick={() => runOrchestration("Suspected dysplastic nevus on back with irregular borders, asymmetry, and color variegation.")}
                disabled={busy}
              >
                Test Dermatology Case
              </Button>
            </div>

            {result && (
              <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Recommended Specialty</div>
                    <div className="font-display text-2xl font-bold text-slate-900 mt-0.5" data-testid="ai-result-specialty">
                      {result.specialty}
                    </div>
                  </div>
                  <Badge className="bg-blue-600 text-white capitalize px-3 py-1 text-xs">
                    {result.priority} Priority
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <Stat label="AI Referral Confidence" value={`${result.confidence}%`} />
                  <Stat label="Urgency Protocol" value={<span className="capitalize font-semibold text-slate-800">{result.priority}</span>} />
                  <Stat label="Engine Source" value={<span className="capitalize text-xs text-slate-700">{result.source}</span>} />
                </div>

                {result.symptoms?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-500 mb-1.5">Extracted Symptoms</div>
                    <div className="flex flex-wrap gap-1.5">
                      {result.symptoms.map((s, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-100 font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {result.conditions?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-500 mb-1.5">Detected Clinical Conditions</div>
                    <div className="flex flex-wrap gap-1.5">
                      {result.conditions.map((c, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-100 font-medium">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-xs font-semibold text-slate-500 mb-1">Clinical Reasoning & Decision Support</div>
                  <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                    {result.reasoning}
                  </p>
                </div>

                {pipelineData?.ml_engine && (
                  <div className="p-3 rounded-lg bg-sky-50/60 border border-sky-100 text-xs text-slate-700 space-y-1">
                    <div className="font-semibold text-blue-900 flex items-center gap-1.5">
                      <Cpu className="h-3.5 w-3.5 text-blue-600" /> Machine Learning Optimization Snapshot
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <div>Evaluated Providers: <span className="font-semibold text-slate-900">{pipelineData.ml_engine.candidates_evaluated} in-network</span></div>
                      <div>Regional Avg Wait: <span className="font-semibold text-slate-900">{pipelineData.ml_engine.average_predicted_wait_days} days</span></div>
                    </div>
                  </div>
                )}

                <div className="pt-2">
                  <Button
                    onClick={() => nav("/patient/best-match")}
                    className="w-full sm:w-auto h-11 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center justify-center gap-2 shadow-sm"
                  >
                    View Best Matched Specialists & Book <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {pipelineData?.document?.extracted_text_preview && (
            <Card className="p-5">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm">
                <FileText className="h-4 w-4 text-blue-600" /> Document Ingestion & Extraction Log
              </div>
              <div className="text-xs text-slate-500 mt-1">
                File: {pipelineData.document.filename || "Clinical Referral"} · {pipelineData.document.character_count} characters extracted
              </div>
              <div className="mt-3 p-3 rounded-md bg-slate-900 text-slate-200 text-xs font-mono max-h-40 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {pipelineData.document.extracted_text_preview}
              </div>
            </Card>
          )}
        </div>

        <Card className="p-6 self-start">
          <div className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-600" /> Triage History
          </div>
          {history.length === 0 && <div className="text-sm text-slate-500">No previous analyses yet.</div>}
          <div className="space-y-3">
            {history.slice(0, 5).map((h, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-blue-50/50 transition-colors cursor-pointer"
                onClick={() => {
                  setResult(h);
                  nav("/patient/best-match");
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium text-sm text-slate-900">{h.specialty}</div>
                  <Badge variant="outline" className="text-[11px] capitalize">{h.priority}</Badge>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Confidence: {h.confidence}% · <span className="text-blue-600 font-medium">View Best Match</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{label}</div>
      <div className="mt-0.5 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
