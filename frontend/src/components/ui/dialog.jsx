import * as React from "react";
export function Dialog({ open, onOpenChange, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl border border-slate-100 animate-in fade-in-0 zoom-in-95">
        {children}
      </div>
    </div>
  );
}
export function DialogContent({ children, className = "" }) { return <div className={`space-y-4 ${className}`}>{children}</div>; }
export function DialogHeader({ children, className = "" }) { return <div className={`flex flex-col space-y-1.5 text-center sm:text-left ${className}`}>{children}</div>; }
export function DialogTitle({ children, className = "" }) { return <h2 className={`text-lg font-semibold leading-none tracking-tight text-slate-900 ${className}`}>{children}</h2>; }
export function DialogDescription({ children, className = "" }) { return <p className={`text-sm text-slate-500 ${className}`}>{children}</p>; }
export function DialogFooter({ children, className = "" }) { return <div className={`flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 ${className}`}>{children}</div>; }
