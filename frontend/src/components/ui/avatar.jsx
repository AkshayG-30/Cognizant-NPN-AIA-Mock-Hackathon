import * as React from "react";
export function Avatar({ className = "", children, ...props }) {
  return <div className={`relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`} {...props}>{children}</div>;
}
export function AvatarImage({ src, alt = "", className = "" }) {
  if (!src) return null;
  return <img src={src} alt={alt} className={`aspect-square h-full w-full object-cover ${className}`} />;
}
export function AvatarFallback({ children, className = "" }) {
  return <div className={`flex h-full w-full items-center justify-center rounded-full bg-slate-100 text-slate-600 font-medium text-sm ${className}`}>{children}</div>;
}
