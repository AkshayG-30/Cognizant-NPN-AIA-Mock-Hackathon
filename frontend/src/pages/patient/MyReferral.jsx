import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { CareJourney } from "@/components/CareJourney";
import { useNavigate } from "react-router-dom";
import { Sparkles, Upload, FileText, Loader2, ArrowRight, CheckCircle2 } from "lucide-react";

export default function MyReferral() {
  const [form, setForm] = useState({
    reason: "",
    symptoms: "",
    duration: "",
    urgency: "routine",
    zip_code: "90024",
    notes: "",
  });
  const [file, setFile] = useState(null);
  const [existing, setExisting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [stepMsg, setStepMsg] = useState("");
  const fileRef = useRef(null);
  const nav = useNavigate();

  useEffect(() => {
    api.get("/referrals/mine/latest")
      .then((r) => setExisting(r.data && r.data.id ? r.data : null))
      .catch(() => {});
  }, []);

  async function processWithCarePathAI(e) {
    if (e) e.preventDefault();
    if (!form.reason && !form.symptoms && !file) {
      toast.error("Please enter a reason/symptoms or attach a medical document.");
      return;
    }

    setBusy(true);
    setStepMsg("Ingesting clinical referral & document...");

    try {
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      }
      formData.append("clinical_text", `${form.reason}. Symptoms: ${form.symptoms}. Duration: ${form.duration}. Notes: ${form.notes}`);
      formData.append("urgency", form.urgency);
      if (form.zip_code && form.zip_code.trim()) {
        formData.append("zip_code", form.zip_code.trim());
        formData.append("patient_address", form.zip_code.trim());
      }
      formData.append("max_distance_km", "150");

      setStepMsg("Running Groq LLM clinical triage & specialty routing...");
      
      const res = await api.post("/carepath/process", formData);

      const data = res.data;
      if (data && data.success) {
        localStorage.setItem("cp_carepath_result", JSON.stringify(data));
        toast.success(`Matched to ${data.clinical_triage.specialty}! Routing to Best Match.`);
        setStepMsg("Predicting wait times with LightGBM & ranking providers...");
        
        setTimeout(() => {
          nav("/patient/best-match");
        }, 600);
      } else {
        toast.error("Could not process clinical document. Please try again.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Pipeline error during processing. Please verify server connection.");
    } finally {
      setBusy(false);
      setStepMsg("");
    }
  }

  async function saveDraft(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post("/referrals", form);
      setExisting(data);
      toast.success("Referral saved as draft.");
      setForm({ reason: "", symptoms: "", duration: "", urgency: "routine", zip_code: "90024", notes: "" });
    } catch {
      toast.error("Could not save draft referral.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Clinical Referral & Ingestion</h1>
        <p className="text-slate-600 mt-1">Submit your clinical notes or upload medical documents to initiate automated CarePath AI triage and wait-time optimized specialist matching.</p>
      </div>

      <Card className="p-5">
        <CareJourney current={existing ? 1 : 0} />
      </Card>

      {existing && (
        <Card className="p-5 bg-gradient-to-r from-blue-50/80 to-sky-50/40 border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-900">
              <CheckCircle2 className="h-4 w-4 text-blue-700" /> Active Referral in System
            </div>
            <Badge variant="secondary" className="capitalize bg-blue-100 text-blue-800 border-blue-200 font-medium">
              {existing.urgency || "routine"}
            </Badge>
          </div>
          <div className="mt-2 font-display text-lg font-semibold text-slate-900">{existing.reason}</div>
          <div className="text-sm text-slate-700 mt-1">{existing.symptoms}</div>
          {existing.suggested_specialty && (
            <div className="mt-3 text-sm flex items-center justify-between">
              <div>
                Triage Match: <span className="font-semibold text-blue-700">{existing.suggested_specialty}</span>
                <span className="text-slate-500"> · {existing.confidence || 94}% AI confidence</span>
              </div>
              <Button size="sm" onClick={() => nav("/patient/best-match")} className="h-8">
                View Recommendations <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            </div>
          )}
        </Card>
      )}

      <Card className="p-6 shadow-sm border-slate-200">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold text-slate-900">Start New Clinical Referral</h2>
          <Badge className="bg-sky-50 text-sky-700 border-sky-200 font-normal text-xs">
            End-to-End AI Orchestration
          </Badge>
        </div>

        <form onSubmit={processWithCarePathAI} className="mt-5 grid md:grid-cols-2 gap-4">
          <div className="md:col-span-2 space-y-1.5">
            <Label htmlFor="reason">Reason for Visit / Primary Concern</Label>
            <Input
              id="reason"
              required={!file}
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              placeholder="e.g. Recurrent retrosternal chest pain with exertion and elevated LDL"
              data-testid="ref-reason"
            />
          </div>

          <div className="md:col-span-2 space-y-1.5">
            <Label htmlFor="symptoms">Clinical Symptoms & Observations</Label>
            <Textarea
              id="symptoms"
              required={!file}
              value={form.symptoms}
              onChange={(e) => setForm({ ...form, symptoms: e.target.value })}
              placeholder="Describe symptoms, severity, associated findings, or relevant lab values..."
              data-testid="ref-symptoms"
              rows={3}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="duration">Duration of Symptoms</Label>
            <Input
              id="duration"
              value={form.duration}
              onChange={(e) => setForm({ ...form, duration: e.target.value })}
              placeholder="e.g. 3 weeks, intermittent"
              data-testid="ref-duration"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="urgency">Clinical Urgency</Label>
            <Select value={form.urgency} onValueChange={(v) => setForm({ ...form, urgency: v })}>
              <SelectTrigger id="urgency" data-testid="ref-urgency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="routine">Routine (Standard referral)</SelectItem>
                <SelectItem value="urgent">Urgent (Priority consultation within 7 days)</SelectItem>
                <SelectItem value="emergency">Emergent (High priority queue acceleration)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="zip_code">Patient Zip Code / Search Radius</Label>
            <Input
              id="zip_code"
              value={form.zip_code}
              onChange={(e) => setForm({ ...form, zip_code: e.target.value })}
              placeholder="90024"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="file_upload">Attach Medical Document / Lab Scan (Optional)</Label>
            <div
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-3 rounded-lg border border-dashed border-slate-300 px-3 py-2 cursor-pointer hover:bg-slate-50 transition-colors"
            >
              <Upload className="h-4 w-4 text-slate-500 shrink-0" />
              <div className="text-sm text-slate-600 truncate">
                {file ? file.name : "Select PDF or Image document"}
              </div>
              <input
                ref={fileRef}
                id="file_upload"
                type="file"
                accept=".pdf,image/*"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          {busy && (
            <div className="md:col-span-2 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-sm flex items-center gap-3 animate-pulse">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600 shrink-0" />
              <div>
                <div className="font-semibold">CarePath AI Pipeline Running</div>
                <div className="text-xs text-blue-700">{stepMsg}</div>
              </div>
            </div>
          )}

          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              type="submit"
              disabled={busy}
              className="h-11 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium flex-1 shadow-sm"
              data-testid="ref-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Processing AI Pipeline...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2 text-sky-200" /> Run CarePath AI Triage & Match
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={saveDraft}
              className="h-11 px-5 border-slate-300"
            >
              Save Draft
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
