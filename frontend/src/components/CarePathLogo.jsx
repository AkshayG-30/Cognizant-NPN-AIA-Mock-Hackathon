import React from "react";



export function CarePathLogo({ variant = "full", className = "" }) {

  const white = variant === "white";

  const primary = white ? "#FFFFFF" : "#2563EB";

  const accent = white ? "#BAE6FD" : "#0EA5E9";

  const text = white ? "#FFFFFF" : "#0F172A";

  const sub = white ? "#CBD5E1" : "#64748B";



  const Mark = (

    <svg viewBox="0 0 64 64" width="40" height="40" aria-hidden="true">

      <path

        d="M50 18 C 42 8, 22 8, 14 22 C 8 32, 12 46, 22 52 C 32 58, 44 54, 50 46"

        fill="none"

        stroke={primary}

        strokeWidth="4"

        strokeLinecap="round"

      />

      <circle cx="14" cy="22" r="4" fill={primary} />

      <circle cx="26" cy="14" r="3.5" fill={accent} />

      <circle cx="42" cy="42" r="3.5" fill={accent} />

      <circle cx="50" cy="46" r="4" fill={primary} />

      <path d="M14 22 L 26 14 M 26 14 L 42 42 M 42 42 L 50 46"

        stroke={accent} strokeWidth="1.4" strokeDasharray="2 3" fill="none" opacity="0.55" />

    </svg>

  );



  if (variant === "icon") return <div className={className}>{Mark}</div>;

  if (variant === "compact") {

    return (

      <div className={`flex items-center gap-2 ${className}`}>

        {Mark}

        <span className="font-display text-lg font-semibold" style={{ color: text }}>CarePath<span style={{ color: primary }}> AI</span></span>

      </div>

    );

  }

  return (

    <div className={`flex items-center gap-3 ${className}`}>

      {Mark}

      <div className="leading-tight">

        <div className="font-display text-xl font-semibold" style={{ color: text }}>

          CarePath<span style={{ color: primary }}> AI</span>

        </div>

        <div className="text-[11px]" style={{ color: sub }}>Right Care. Right Path.</div>

      </div>

    </div>

  );

}
