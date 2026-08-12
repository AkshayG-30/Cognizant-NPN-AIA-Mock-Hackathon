import { Card } from "@/components/ui/card";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { Bell } from "lucide-react";

import { Button } from "@/components/ui/button";



export default function Notifications() {

  const [items, setItems] = useState([]);

  const load = () => api.get("/notifications").then((r) => setItems(r.data)).catch(() => {});

  useEffect(() => { load(); }, []);

  async function mark(id) { await api.post(`/notifications/${id}/read`); load(); }

  return (

    <div className="space-y-6 max-w-3xl">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Notifications</h1>

        <p className="text-slate-600 mt-1">Stay up to date on your care.</p>

      </div>

      {items.length === 0 && <Card className="p-8 text-slate-500">Nothing here yet.</Card>}

      <div className="space-y-2">

        {items.map((n) => (

          <Card key={n.id} className={`p-4 flex items-start justify-between gap-4 ${n.read ? "" : "border-blue-200 bg-blue-50/40"}`}>

            <div className="flex items-start gap-3">

              <div className="h-9 w-9 rounded-lg bg-blue-100 text-blue-700 grid place-items-center"><Bell className="h-4 w-4" /></div>

              <div>

                <div className="font-medium">{n.title}</div>

                <div className="text-sm text-slate-600">{n.body}</div>

                <div className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>

              </div>

            </div>

            {!n.read && <Button variant="ghost" size="sm" onClick={() => mark(n.id)}>Mark read</Button>}

          </Card>

        ))}

      </div>

    </div>

  );

}





