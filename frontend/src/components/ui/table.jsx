import * as React from "react";
export function Table({ className = "", ...props }) { return <div className="relative w-full overflow-auto"><table className={`w-full caption-bottom text-sm ${className}`} {...props} /></div>; }
export function TableHeader({ className = "", ...props }) { return <thead className={`[&_tr]:border-b ${className}`} {...props} />; }
export function TableBody({ className = "", ...props }) { return <tbody className={`[&_tr:last-child]:border-0 ${className}`} {...props} />; }
export function TableFooter({ className = "", ...props }) { return <tfoot className={`border-t bg-slate-100/50 font-medium [&>tr]:last:border-b-0 ${className}`} {...props} />; }
export function TableRow({ className = "", ...props }) { return <tr className={`border-b transition-colors hover:bg-slate-100/50 data-[state=selected]:bg-slate-100 ${className}`} {...props} />; }
export function TableHead({ className = "", ...props }) { return <th className={`h-10 px-4 text-left align-middle font-medium text-slate-500 [&:has([role=checkbox])]:pr-0 ${className}`} {...props} />; }
export function TableCell({ className = "", ...props }) { return <td className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`} {...props} />; }
