import React from "react";
import { Check } from "lucide-react";

export function CareJourney({ current = 0 }) {
  const steps = [
    { label: "Referral Request", desc: "Submitted" },
    { label: "Clinical Data", desc: "Upload Reports" },
    { label: "AI Triage", desc: "Specialty Match" },
    { label: "Provider Selection", desc: "Best Match" },
    { label: "Care Scheduled", desc: "Booked" }
  ];

  return (
    <div className="w-full py-2">
      <div className="grid grid-cols-5 gap-2 relative">
        {steps.map((step, idx) => {
          const isDone = idx < current;
          const isCurrent = idx === current;
          return (
            <div key={step.label} className="flex flex-col items-center text-center relative z-10">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center font-medium text-xs transition-colors ${
                  isDone
                    ? "bg-blue-600 text-white"
                    : isCurrent
                    ? "bg-blue-100 text-blue-700 ring-2 ring-blue-600 font-bold"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                {isDone ? <Check className="h-4 w-4" /> : idx + 1}
              </div>
              <div className="mt-2 text-xs font-semibold text-slate-800">{step.label}</div>
              <div className="text-[11px] text-slate-500">{step.desc}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
