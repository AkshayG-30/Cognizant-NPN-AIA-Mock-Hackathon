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
import { Upload, FileText, X, Sparkles, Loader2, CheckCircle2, ArrowRight, FileCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { CareJourney } from "@/components/CareJourney";

export default function UploadReports() {
  const [reports, setReports] = useState([]);
  const [form, setForm] = useState({ name: "", kind: "Blood Test", notes: "", file_name: "" });
  const [location, setLocation] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [stepMsg, setStepMsg] = useState("");
  const fileRef = useRef(null);
  const nav = useNavigate();

  const load = () => api.get("/reports/mine").then((r) => setReports(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  function handleFileChange(e) {
    const f = e.target.files?.[0];
    if (f) {
      setSelectedFile(f);
      setForm((prev) => ({
        ...prev,
        file_name: f.name,
        name: prev.name || f.name.replace(/\.[^/.]+$/, ""),
      }));
    }
  }

  async function processDirectWithAI() {
    if (!selectedFile && !form.notes) {
      toast.error("Please select a medical document (PDF or Image) to analyze.");
      return;
    }

    setBusy(true);
    setStepMsg("Uploading & extracting document text with RapidOCR / PDF engine...");

    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append("file", selectedFile);
      }
      formData.append("clinical_text", form.notes || form.name || "Medical Report Ingestion");
      formData.append("urgency", "routine");
      if (location && location.trim()) {
        formData.append("zip_code", location.trim());
        formData.append("patient_address", location.trim());
      }
      formData.append("max_distance_km", "150");

      setStepMsg("Running Groq LLM clinical triage & diagnostic classification...");
      const res = await api.post("/carepath/process", formData);

      const data = res.data;
      if (data && data.success) {
        localStorage.setItem("cp_carepath_result", JSON.stringify(data));
        toast.success(`Classified as ${data.clinical_triage.specialty}! Triage complete.`);
        
        // Also save to reports list for reference
        try {
          await api.post("/reports", {
            name: form.name || selectedFile?.name || "Clinical Report",
            kind: form.kind,
            notes: form.notes || data.clinical_triage.summary,
            file_name: selectedFile?.name || "",
          });
        } catch (_) {}

        setStepMsg("Predicting wait times with LightGBM & finding best provider...");
        setTimeout(() => {
          nav("/patient/best-match");
        }, 500);
      } else {
        toast.error("Extraction failed. Please check document formatting.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Processing error. Verify backend server is running.");
    } finally {
      setBusy(false);
      setStepMsg("");
    }
  }

  async function submit(e) {
    e.preventDefault();
    try {
      await api.post("/reports", form);
      toast.success("Report added to your records");
      setForm({ name: "", kind: "Blood Test", notes: "", file_name: "" });
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch {
      toast.error("Could not add report");
    }
  }

  async function remove(id) {
    await api.delete(`/reports/${id}`);
    load();
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Upload Medical Reports & Documents</h1>
        <p className="text-slate-600 mt-1">Upload lab results, imaging scans, discharge summaries, or referral letters to run automated OCR and clinical AI analysis.</p>
      </div>

      <Card className="p-5">
        <CareJourney current={1} />
      </Card>

      <Card className="p-6 shadow-sm border-slate-200">
        <form onSubmit={submit} className="grid md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="rep_name">Report Name / Description</Label>
            <Input
              id="rep_name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Lipid Panel & Stress Test 2026"
              data-testid="report-name"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rep_kind">Document Category</Label>
            <Select value={form.kind} onValueChange={(v) => setForm({ ...form, kind: v })}>
              <SelectTrigger id="rep_kind" data-testid="report-kind">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["Blood Test", "Imaging", "Prescription", "Discharge Summary", "Clinical Referral", "Other"].map((k) => (
                  <SelectItem key={k} value={k}>{k}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="md:col-span-2 space-y-1.5">
            <Label htmlFor="patient_loc">Patient Address / City / Zip Code (Optional)</Label>
            <Input
              id="patient_loc"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Mumbai, India or 90024 or Los Angeles"
            />
          </div>

          <div className="md:col-span-2 space-y-1.5">
            <Label htmlFor="rep_file">Select Medical File (PDF, JPEG, PNG)</Label>
            <label
              htmlFor="rep_file"
              className="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 px-6 py-8 cursor-pointer hover:border-blue-400 hover:bg-blue-50/40 transition-colors"
            >
              {selectedFile ? (
                <div className="flex items-center gap-3 text-blue-700 font-medium">
                  <FileCheck className="h-7 w-7 text-blue-600" />
                  <div>
                    <div className="text-sm font-semibold">{selectedFile.name}</div>
                    <div className="text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(1)} KB · Ready for AI ingestion</div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="h-10 w-10 rounded-full bg-blue-50 grid place-items-center text-blue-600">
                    <Upload className="h-5 w-5" />
                  </div>
                  <div className="text-sm font-medium text-slate-700">
                    Click to browse or drag and drop your clinical document
                  </div>
                  <div className="text-xs text-slate-400">PDF, JPG, PNG up to 25MB (Supports multi-page OCR)</div>
                </>
              )}
              <input
                ref={fileRef}
                id="rep_file"
                type="file"
                accept=".pdf,image/*"
                className="hidden"
                onChange={handleFileChange}
                data-testid="report-file"
              />
            </label>
          </div>

          <div className="md:col-span-2 space-y-1.5">
            <Label htmlFor="rep_notes">Clinical Notes / Context (Optional)</Label>
            <Textarea
              id="rep_notes"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Add any specific clinical notes, patient history, or questions for the AI specialist triage..."
              data-testid="report-notes"
              rows={2}
            />
          </div>

          {busy && (
            <div className="md:col-span-2 p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-sm flex items-center gap-3 animate-pulse">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600 shrink-0" />
              <div>
                <div className="font-semibold">CarePath Pipeline In Progress</div>
                <div className="text-xs text-blue-700">{stepMsg}</div>
              </div>
            </div>
          )}

          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              type="button"
              onClick={processDirectWithAI}
              disabled={busy}
              className="h-11 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium flex-1 shadow-sm"
            >
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Analyzing Document...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2 text-sky-200" /> Ingest & Analyze with AI
                </>
              )}
            </Button>

            <Button
              type="submit"
              variant="outline"
              disabled={busy}
              className="h-11 px-6 border-slate-300"
              data-testid="report-submit"
            >
              Save to Portal Only
            </Button>
          </div>
        </form>
      </Card>

      <Card className="p-6">
        <h2 className="font-display text-lg font-semibold text-slate-900">Your Uploaded Medical Documents</h2>
        {reports.length === 0 ? (
          <div className="mt-3 text-sm text-slate-500">No medical reports uploaded yet.</div>
        ) : (
          <div className="mt-4 space-y-3">
            {reports.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/60 hover:bg-slate-100/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-blue-100 text-blue-700 grid place-items-center">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-900">{r.name}</div>
                    <div className="text-xs text-slate-500">{r.kind} · {r.file_name || "Text report"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs font-normal">Stored</Badge>
                  <Button variant="ghost" size="sm" onClick={() => remove(r.id)} className="h-8 w-8 p-0 text-slate-400 hover:text-red-600">
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
