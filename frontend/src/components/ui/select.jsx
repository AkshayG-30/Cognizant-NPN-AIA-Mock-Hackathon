import * as React from "react";
import { ChevronDown, Check } from "lucide-react";

export function Select({ value, onValueChange, children }) {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef(null);

  React.useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const trigger = React.Children.toArray(children).find(
    (c) => c?.type === SelectTrigger || c?.type?.name === "SelectTrigger"
  );
  const content = React.Children.toArray(children).find(
    (c) => c?.type === SelectContent || c?.type?.name === "SelectContent"
  );

  return (
    <div ref={containerRef} className="relative w-full">
      {trigger &&
        React.cloneElement(trigger, {
          open,
          onClick: () => setOpen((prev) => !prev),
          value,
          content,
        })}
      {open &&
        content &&
        React.cloneElement(content, {
          value,
          onSelect: (val) => {
            onValueChange && onValueChange(val);
            setOpen(false);
          },
        })}
    </div>
  );
}

export function SelectTrigger({ className = "", children, open, onClick, value, content }) {
  let displayValue = value;
  if (content && content.props && content.props.children) {
    const items = React.Children.toArray(content.props.children);
    const matchedItem = items.find((item) => item.props && item.props.value === value);
    if (matchedItem && matchedItem.props.children) {
      displayValue = matchedItem.props.children;
    }
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 ${className}`}
    >
      <span className="block truncate text-slate-900 font-medium capitalize">{displayValue || "Select..."}</span>
      <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
    </button>
  );
}

export function SelectValue({ placeholder, value }) {
  return <span className="block truncate">{value || placeholder}</span>;
}

export function SelectContent({ children, value, onSelect, className = "" }) {
  return (
    <div
      className={`absolute left-0 top-full mt-1.5 w-full rounded-md border border-slate-200 bg-white p-1 shadow-lg ring-1 ring-black/5 z-50 ${className}`}
    >
      {React.Children.map(children, (child) =>
        child ? React.cloneElement(child, { selectedValue: value, onSelect }) : null
      )}
    </div>
  );
}

export function SelectItem({ value, selectedValue, onSelect, children, className = "" }) {
  const isSelected = selectedValue === value;
  return (
    <div
      onClick={() => onSelect && onSelect(value)}
      className={`relative flex w-full cursor-pointer select-none items-center rounded-sm py-2 pl-3 pr-8 text-sm font-medium transition-colors hover:bg-slate-100 ${
        isSelected ? "bg-blue-50 text-blue-700" : "text-slate-700"
      } ${className}`}
    >
      <span className="truncate">{children}</span>
      {isSelected && (
        <span className="absolute right-2.5 flex h-3.5 w-3.5 items-center justify-center">
          <Check className="h-4 w-4 text-blue-600" />
        </span>
      )}
    </div>
  );
}
