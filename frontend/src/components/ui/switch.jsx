import * as React from "react";
export function Switch({ checked, onCheckedChange, className = "", ...props }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange && onCheckedChange(!checked)}
      className={`peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none ${checked ? "bg-blue-600" : "bg-slate-200"} ${className}`}
      {...props}
    >
      <span className={`pointer-events-none block h-4 w-4 rounded-full bg-white shadow-lg ring-0 transition-transform ${checked ? "translate-x-4" : "translate-x-0"}`} />
    </button>
  );
}
