import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/lib/auth";

import { CarePathLogo } from "@/components/CarePathLogo";

import {

  LayoutDashboard, FileText, Upload, Sparkles, Search, MapPin, CalendarClock, History,

  MessageSquare, Bell, User, Settings, LifeBuoy, LogOut, Users, ClipboardList, Building2,

  BarChart3, Network, TimerReset, Award, Scroll, Home, HeartPulse, Menu, ChevronRight

} from "lucide-react";

import { useState } from "react";

import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

import { Input } from "@/components/ui/input";

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";

import { Badge } from "@/components/ui/badge";



const PATIENT_NAV = [

  { group: "Home", items: [{ to: "/patient", icon: LayoutDashboard, label: "Dashboard" }] },

  { group: "My Care", items: [

    { to: "/patient/referral", icon: FileText, label: "My Referral" },

    { to: "/patient/reports", icon: Upload, label: "Upload Reports" },

    { to: "/patient/ai-analysis", icon: Sparkles, label: "AI Analysis" },

  ]},

  { group: "Find Care", items: [

    { to: "/patient/specialists", icon: Search, label: "Find Specialists" },

    { to: "/patient/nearby", icon: MapPin, label: "Nearby Care" },

  ]},

  { group: "Appointments", items: [

    { to: "/patient/appointments", icon: CalendarClock, label: "Upcoming" },

    { to: "/patient/appointments/past", icon: History, label: "Past" },

  ]},

  { group: "Communication", items: [

    { to: "/patient/messages", icon: MessageSquare, label: "Messages" },

    { to: "/patient/notifications", icon: Bell, label: "Notifications" },

  ]},

  { group: "Account", items: [

    { to: "/patient/profile", icon: User, label: "Profile" },

    { to: "/patient/settings", icon: Settings, label: "Settings" },

  ]},

  { group: "Support", items: [{ to: "/patient/help", icon: LifeBuoy, label: "Help & Support" }] },

];



const DOCTOR_NAV = [

  { group: "Workspace", items: [

    { to: "/doctor", icon: LayoutDashboard, label: "Dashboard" },

    { to: "/doctor/referrals", icon: ClipboardList, label: "Referrals" },

    { to: "/doctor/patients", icon: Users, label: "Patients" },

  ]},

  { group: "Schedule", items: [

    { to: "/doctor/schedule", icon: CalendarClock, label: "My Schedule" },

    { to: "/doctor/appointments", icon: CalendarClock, label: "Appointments" },

  ]},

  { group: "Communication", items: [

    { to: "/doctor/messages", icon: MessageSquare, label: "Messages" },

    { to: "/doctor/notifications", icon: Bell, label: "Notifications" },

  ]},

  { group: "Account", items: [

    { to: "/doctor/profile", icon: User, label: "Profile" },

    { to: "/doctor/settings", icon: Settings, label: "Settings" },

  ]},

  { group: "Support", items: [{ to: "/doctor/help", icon: LifeBuoy, label: "Help & Support" }] },

];



const ADMIN_NAV = [

  { group: "Overview", items: [{ to: "/admin", icon: LayoutDashboard, label: "Dashboard" }] },

  { group: "Provider Network", items: [

    { to: "/admin/doctors", icon: Users, label: "Doctors" },

    { to: "/admin/hospitals", icon: Building2, label: "Hospitals" },

    { to: "/admin/schedules", icon: CalendarClock, label: "Schedules" },

  ]},

  { group: "Operations", items: [

    { to: "/admin/appointments", icon: CalendarClock, label: "Appointments" },

    { to: "/admin/referrals", icon: ClipboardList, label: "Referrals" },

  ]},

  { group: "Intelligence", items: [

    { to: "/admin/analytics/referrals", icon: BarChart3, label: "Referral Analytics" },

    { to: "/admin/analytics/network", icon: Network, label: "Network Access" },

    { to: "/admin/analytics/wait-time", icon: TimerReset, label: "Wait-Time Analytics" },

    { to: "/admin/analytics/quality", icon: Award, label: "Provider Quality" },

  ]},

  { group: "System", items: [

    { to: "/admin/audit", icon: Scroll, label: "Audit Logs" },

    { to: "/admin/notifications", icon: Bell, label: "Notifications" },

    { to: "/admin/settings", icon: Settings, label: "Settings" },

  ]},

  { group: "Support", items: [{ to: "/admin/help", icon: LifeBuoy, label: "Help & Support" }] },

];



function getNav(role) {

  if (role === "admin") return ADMIN_NAV;

  if (role === "doctor") return DOCTOR_NAV;

  return PATIENT_NAV;

}



function SidebarBody({ role, onNavigate }) {

  const nav = getNav(role);

  return (

    <div className="flex flex-col h-full bg-white border-r border-slate-200">

      <div className="px-5 py-5 border-b border-slate-200">

        <CarePathLogo variant="compact" />

      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">

        {nav.map((g) => (

          <div key={g.group}>

            <div className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{g.group}</div>

            <div className="space-y-0.5">

              {g.items.map((it) => (

                <NavLink

                  key={it.to}

                  to={it.to}

                  end

                  onClick={onNavigate}

                  data-testid={`nav-${it.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}

                  className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${

                    isActive ? "nav-active" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"

                  }`}

                >

                  <it.icon className="h-4 w-4" />

                  <span>{it.label}</span>

                </NavLink>

              ))}

            </div>

          </div>

        ))}

      </nav>

    </div>

  );

}



function Breadcrumbs() {

  const { pathname } = useLocation();

  const parts = pathname.split("/").filter(Boolean);

  const labels = {

    patient: "Dashboard", doctor: "Dashboard", admin: "Dashboard",

    referral: "My Referral", reports: "Upload Reports", "ai-analysis": "AI Analysis",

    specialists: "Find Specialists", nearby: "Nearby Care", appointments: "Appointments",

    past: "Past", messages: "Messages", notifications: "Notifications",

    profile: "Profile", settings: "Settings", help: "Help & Support",

    referrals: "Referrals", patients: "Patients", schedule: "My Schedule",

    doctors: "Doctors", hospitals: "Hospitals", schedules: "Schedules",

    analytics: "Analytics", network: "Network Access", "wait-time": "Wait-Time Analytics",

    quality: "Provider Quality", audit: "Audit Logs", "best-match": "Find Your Best CarePath",

  };

  const crumbs = [];

  crumbs.push({ label: "Dashboard", to: `/${parts[0]}` });

  for (let i = 1; i < parts.length; i++) {

    const label = labels[parts[i]] || parts[i].replace(/-/g, " ");

    crumbs.push({ label: label.charAt(0).toUpperCase() + label.slice(1), to: "/" + parts.slice(0, i + 1).join("/") });

  }

  return (

    <div className="flex items-center gap-1.5 text-sm" data-testid="breadcrumbs">

      {crumbs.map((c, i) => (

        <div key={c.to} className="flex items-center gap-1.5">

          {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}

          <span className={i === crumbs.length - 1 ? "text-slate-900 font-medium" : "text-slate-500"}>{c.label}</span>

        </div>

      ))}

    </div>

  );

}



function TopHeader({ onMenuClick }) {

  const { user, logout } = useAuth();

  const nav = useNavigate();

  return (

    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30">

      <div className="flex items-center gap-3 min-w-0">

        <button className="lg:hidden p-2 rounded-md hover:bg-slate-100" onClick={onMenuClick} aria-label="Open menu" data-testid="mobile-menu-btn">

          <Menu className="h-5 w-5" />

        </button>

        <div className="hidden md:block min-w-0">

          <Breadcrumbs />

        </div>

      </div>

      <div className="flex items-center gap-2 sm:gap-3">

        <div className="hidden md:flex items-center relative">

          <Search className="h-4 w-4 absolute left-3 text-slate-400" />

          <Input placeholder="Search…" className="pl-9 w-64 bg-slate-50 border-slate-200" data-testid="global-search" />

        </div>

        <button onClick={() => nav(`/${user?.role}/notifications`)} className="relative p-2 rounded-full hover:bg-slate-100" aria-label="Notifications" data-testid="notif-btn">

          <Bell className="h-5 w-5 text-slate-600" />

          <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-blue-600 rounded-full" />

        </button>

        <DropdownMenu>

          <DropdownMenuTrigger asChild>

            <button className="flex items-center gap-2 rounded-full p-1 hover:bg-slate-100" data-testid="profile-menu">

              <Avatar className="h-8 w-8">

                <AvatarFallback className="bg-blue-600 text-white text-sm">{(user?.name || "U").slice(0,1).toUpperCase()}</AvatarFallback>

              </Avatar>

              <div className="hidden sm:block text-left leading-tight pr-2">

                <div className="text-sm font-medium">{user?.name}</div>

                <div className="text-xs text-slate-500 capitalize">{user?.role}</div>

              </div>

            </button>

          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" className="w-56">

            <DropdownMenuLabel>My account</DropdownMenuLabel>

            <DropdownMenuSeparator />

            <DropdownMenuItem onClick={() => nav(`/${user?.role}/profile`)} data-testid="menu-profile"><User className="h-4 w-4 mr-2" />View Profile</DropdownMenuItem>

            <DropdownMenuItem onClick={() => nav(`/${user?.role}/settings`)}><Settings className="h-4 w-4 mr-2" />Settings</DropdownMenuItem>

            <DropdownMenuItem onClick={() => nav(`/${user?.role}/help`)}><LifeBuoy className="h-4 w-4 mr-2" />Help & Support</DropdownMenuItem>

            <DropdownMenuSeparator />

            <DropdownMenuItem onClick={logout} className="text-red-600" data-testid="menu-logout"><LogOut className="h-4 w-4 mr-2" />Logout</DropdownMenuItem>

          </DropdownMenuContent>

        </DropdownMenu>

      </div>

    </header>

  );

}



function MobileBottomNav({ role }) {

  const items = role === "patient" ? [

    { to: "/patient", icon: Home, label: "Home" },

    { to: "/patient/referral", icon: HeartPulse, label: "Care" },

    { to: "/patient/appointments", icon: CalendarClock, label: "Appts" },

    { to: "/patient/messages", icon: MessageSquare, label: "Messages" },

    { to: "/patient/profile", icon: User, label: "Profile" },

  ] : role === "doctor" ? [

    { to: "/doctor", icon: Home, label: "Home" },

    { to: "/doctor/referrals", icon: ClipboardList, label: "Referrals" },

    { to: "/doctor/appointments", icon: CalendarClock, label: "Appts" },

    { to: "/doctor/messages", icon: MessageSquare, label: "Messages" },

    { to: "/doctor/profile", icon: User, label: "Profile" },

  ] : [

    { to: "/admin", icon: Home, label: "Home" },

    { to: "/admin/doctors", icon: Users, label: "Doctors" },

    { to: "/admin/appointments", icon: CalendarClock, label: "Appts" },

    { to: "/admin/analytics/referrals", icon: BarChart3, label: "Insights" },

    { to: "/admin/settings", icon: Settings, label: "Settings" },

  ];

  return (

    <div className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-slate-200">

      <div className="grid grid-cols-5">

        {items.map((it) => (

          <NavLink key={it.to} to={it.to} end

            className={({ isActive }) => `flex flex-col items-center justify-center py-2 text-[11px] ${isActive ? "text-blue-700" : "text-slate-500"}`}

            data-testid={`mobile-nav-${it.label.toLowerCase()}`}

          >

            <it.icon className="h-5 w-5 mb-0.5" />

            {it.label}

          </NavLink>

        ))}

      </div>

    </div>

  );

}



export function AppLayout({ children }) {

  const { user } = useAuth();

  const [open, setOpen] = useState(false);

  if (!user) return null;

  return (

    <div className="min-h-screen bg-slate-50">

      <div className="hidden lg:block fixed inset-y-0 left-0 w-64 z-20">

        <SidebarBody role={user.role} />

      </div>

      <Sheet open={open} onOpenChange={setOpen}>

        <SheetContent side="left" className="p-0 w-72 bg-white">

          <SidebarBody role={user.role} onNavigate={() => setOpen(false)} />

        </SheetContent>

      </Sheet>

      <div className="lg:pl-64">

        <TopHeader onMenuClick={() => setOpen(true)} />

        <main className="p-4 sm:p-6 pb-24 lg:pb-8 max-w-[1400px]">

          <div className="md:hidden mb-3"><Breadcrumbs /></div>

          {children}

        </main>

      </div>

      <MobileBottomNav role={user.role} />

    </div>

  );

}



export { SheetTrigger };





