import { Card } from "@/components/ui/card";

import { Textarea } from "@/components/ui/textarea";

import { Button } from "@/components/ui/button";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import { toast } from "sonner";

import { useAuth } from "@/lib/auth";

import { Send } from "lucide-react";



export default function Messages() {

  const { user } = useAuth();

  const [items, setItems] = useState([]);

  const [body, setBody] = useState("");

  const [to, setTo] = useState("");

  const load = () => api.get("/messages").then((r) => setItems(r.data)).catch(() => {});

  useEffect(() => { load(); }, []);



  async function send() {

    if (!body.trim() || !to) return;

    try {

      await api.post("/messages", { to_user_id: to, body });

      setBody(""); load();

      toast.success("Message sent");

    } catch { toast.error("Could not send"); }

  }



  return (

    <div className="space-y-6 max-w-3xl">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Messages</h1>

        <p className="text-slate-600 mt-1">Secure conversations with your care team.</p>

      </div>

      <Card className="p-4">

        <div className="text-xs text-slate-500 mb-2">Send a note (paste a user ID)</div>

        <div className="flex gap-2">

          <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="Recipient user id" className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm" data-testid="msg-to" />

        </div>

        <Textarea className="mt-2" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write a message" data-testid="msg-body" />

        <Button className="mt-2" onClick={send} data-testid="msg-send"><Send className="h-4 w-4 mr-2" />Send</Button>

      </Card>

      <div className="space-y-2">

        {items.length === 0 && <div className="text-sm text-slate-500">Nothing here yet.</div>}

        {items.map((m) => (

          <Card key={m.id} className={`p-4 ${m.from_user_id === user.id ? "bg-blue-50/50 border-blue-100" : ""}`}>

            <div className="text-xs text-slate-500">{m.from_name} · {new Date(m.created_at).toLocaleString()}</div>

            <div className="mt-1">{m.body}</div>

          </Card>

        ))}

      </div>

    </div>

  );

}





