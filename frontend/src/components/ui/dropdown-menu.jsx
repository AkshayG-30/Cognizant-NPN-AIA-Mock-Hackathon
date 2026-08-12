import * as React from "react";
export function DropdownMenu({ children }) {
  const [open, setOpen] = React.useState(false);
  return <div className="relative inline-block text-left">{React.Children.map(children, c => c ? React.cloneElement(c, { open, setOpen }) : null)}</div>;
}
export function DropdownMenuTrigger({ children, setOpen, asChild }) {
  return <div onClick={() => setOpen && setOpen(o => !o)} className="cursor-pointer">{children}</div>;
}
export function DropdownMenuContent({ children, open, setOpen, align = "right", className = "" }) {
  if (!open) return null;
  return (
    <div onClick={() => setOpen && setOpen(false)} className={`absolute ${align === "right" ? "right-0" : "left-0"} mt-2 w-56 rounded-md bg-white p-1 shadow-lg ring-1 ring-black/5 z-50 ${className}`}>
      {children}
    </div>
  );
}
export function DropdownMenuItem({ children, onClick, className = "" }) {
  return <div onClick={onClick} className={`flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm hover:bg-slate-100 ${className}`}>{children}</div>;
}
export function DropdownMenuLabel({ children, className = "" }) {
  return <div className={`px-2 py-1.5 text-xs font-semibold text-slate-500 ${className}`}>{children}</div>;
}
export function DropdownMenuSeparator({ className = "" }) {
  return <div className={`-mx-1 my-1 h-px bg-slate-100 ${className}`} />;
}
