import * as React from "react";
export function Sheet({ children }) {
  const [open, setOpen] = React.useState(false);
  return <div className="relative">{React.Children.map(children, c => c ? React.cloneElement(c, { open, setOpen }) : null)}</div>;
}
export function SheetTrigger({ children, setOpen, asChild }) {
  return <div onClick={() => setOpen && setOpen(o => !o)} className="cursor-pointer">{children}</div>;
}
export function SheetContent({ children, open, setOpen, side = "left", className = "" }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      <div onClick={() => setOpen && setOpen(false)} className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
      <div className={`relative z-50 w-72 bg-white p-6 shadow-2xl h-full ${className}`}>
        {children}
      </div>
    </div>
  );
}
