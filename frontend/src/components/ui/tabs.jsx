import * as React from "react";
export function Tabs({ defaultValue, value, onValueChange, className = "", children, ...props }) {
  const [active, setActive] = React.useState(value || defaultValue);
  const current = value !== undefined ? value : active;
  const handleChange = (v) => { setActive(v); if (onValueChange) onValueChange(v); };
  return (
    <div className={className} {...props}>
      {React.Children.map(children, child => {
        if (!child) return null;
        return React.cloneElement(child, { activeValue: current, onSelect: handleChange });
      })}
    </div>
  );
}

export function TabsList({ activeValue, onSelect, className = "", children, ...props }) {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500 ${className}`} {...props}>
      {React.Children.map(children, child => {
        if (!child) return null;
        return React.cloneElement(child, { activeValue, onSelect });
      })}
    </div>
  );
}

export function TabsTrigger({ value, activeValue, onSelect, className = "", children, ...props }) {
  const isActive = activeValue === value;
  return (
    <button
      type="button"
      onClick={() => onSelect && onSelect(value)}
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 ${isActive ? "bg-white text-slate-950 shadow-sm font-semibold" : "hover:text-slate-900"} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, activeValue, className = "", children, ...props }) {
  if (activeValue !== value) return null;
  return <div className={`mt-2 ${className}`} {...props}>{children}</div>;
}
