import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider, useAuth } from "@/lib/auth";

import { Toaster } from "@/components/ui/sonner";

import Login from "@/pages/Login";

import Register from "@/pages/Register";

import { RequireAuth } from "@/components/RequireAuth";

import PatientDashboard from "@/pages/patient/Dashboard";

import MyReferral from "@/pages/patient/MyReferral";

import UploadReports from "@/pages/patient/UploadReports";

import AIAnalysis from "@/pages/patient/AIAnalysis";

import FindSpecialists from "@/pages/patient/FindSpecialists";

import DoctorProfile from "@/pages/patient/DoctorProfile";

import BestMatch from "@/pages/patient/BestMatch";

import NearbyCare from "@/pages/patient/NearbyCare";

import Appointments from "@/pages/shared/Appointments";

import Notifications from "@/pages/shared/Notifications";

import Messages from "@/pages/shared/Messages";

import { ProfilePage, SettingsPage, HelpPage } from "@/pages/shared/Account";

import DoctorDashboard from "@/pages/doctor/Dashboard";

import { DoctorReferrals, DoctorPatients, DoctorSchedule } from "@/pages/doctor/DoctorPages";

import AdminDashboard from "@/pages/admin/Dashboard";

import { AdminDoctors, AdminHospitals, AdminReferrals, AdminAppointments, AdminAuditLogs, AdminSchedules } from "@/pages/admin/AdminPages";

import { ReferralAnalytics, WaitTimeAnalytics, NetworkAccess, ProviderQuality } from "@/pages/admin/Analytics";

import "@/App.css";



function RootRedirect() {

  const { user, loading } = useAuth();

  if (loading) return <div className="min-h-screen grid place-items-center text-slate-500">Loading CarePath AI…</div>;

  return <Navigate to={user ? `/${user.role}` : "/login"} replace />;

}



export default function App() {

  return (

    <BrowserRouter>

      <AuthProvider>

        <div className="App">

          <Toaster position="top-right" richColors />

          <Routes>

            <Route path="/" element={<RootRedirect />} />

            <Route path="/login" element={<Login />} />

            <Route path="/register" element={<Register />} />



            {/* Patient */}

            <Route path="/patient" element={<RequireAuth role="patient"><PatientDashboard /></RequireAuth>} />

            <Route path="/patient/referral" element={<RequireAuth role="patient"><MyReferral /></RequireAuth>} />

            <Route path="/patient/reports" element={<RequireAuth role="patient"><UploadReports /></RequireAuth>} />

            <Route path="/patient/ai-analysis" element={<RequireAuth role="patient"><AIAnalysis /></RequireAuth>} />

            <Route path="/patient/specialists" element={<RequireAuth role="patient"><FindSpecialists /></RequireAuth>} />

            <Route path="/patient/specialists/:id" element={<RequireAuth role="patient"><DoctorProfile /></RequireAuth>} />

            <Route path="/patient/best-match" element={<RequireAuth role="patient"><BestMatch /></RequireAuth>} />

            <Route path="/patient/nearby" element={<RequireAuth role="patient"><NearbyCare /></RequireAuth>} />

            <Route path="/patient/appointments" element={<RequireAuth role="patient"><Appointments scope="upcoming" /></RequireAuth>} />

            <Route path="/patient/appointments/past" element={<RequireAuth role="patient"><Appointments scope="past" /></RequireAuth>} />

            <Route path="/patient/messages" element={<RequireAuth role="patient"><Messages /></RequireAuth>} />

            <Route path="/patient/notifications" element={<RequireAuth role="patient"><Notifications /></RequireAuth>} />

            <Route path="/patient/profile" element={<RequireAuth role="patient"><ProfilePage /></RequireAuth>} />

            <Route path="/patient/settings" element={<RequireAuth role="patient"><SettingsPage /></RequireAuth>} />

            <Route path="/patient/help" element={<RequireAuth role="patient"><HelpPage /></RequireAuth>} />



            {/* Doctor */}

            <Route path="/doctor" element={<RequireAuth role="doctor"><DoctorDashboard /></RequireAuth>} />

            <Route path="/doctor/referrals" element={<RequireAuth role="doctor"><DoctorReferrals /></RequireAuth>} />

            <Route path="/doctor/patients" element={<RequireAuth role="doctor"><DoctorPatients /></RequireAuth>} />

            <Route path="/doctor/schedule" element={<RequireAuth role="doctor"><DoctorSchedule /></RequireAuth>} />

            <Route path="/doctor/appointments" element={<RequireAuth role="doctor"><Appointments scope="upcoming" /></RequireAuth>} />

            <Route path="/doctor/messages" element={<RequireAuth role="doctor"><Messages /></RequireAuth>} />

            <Route path="/doctor/notifications" element={<RequireAuth role="doctor"><Notifications /></RequireAuth>} />

            <Route path="/doctor/profile" element={<RequireAuth role="doctor"><ProfilePage /></RequireAuth>} />

            <Route path="/doctor/settings" element={<RequireAuth role="doctor"><SettingsPage /></RequireAuth>} />

            <Route path="/doctor/help" element={<RequireAuth role="doctor"><HelpPage /></RequireAuth>} />



            {/* Admin */}

            <Route path="/admin" element={<RequireAuth role="admin"><AdminDashboard /></RequireAuth>} />

            <Route path="/admin/doctors" element={<RequireAuth role="admin"><AdminDoctors /></RequireAuth>} />

            <Route path="/admin/hospitals" element={<RequireAuth role="admin"><AdminHospitals /></RequireAuth>} />

            <Route path="/admin/schedules" element={<RequireAuth role="admin"><AdminSchedules /></RequireAuth>} />

            <Route path="/admin/referrals" element={<RequireAuth role="admin"><AdminReferrals /></RequireAuth>} />

            <Route path="/admin/appointments" element={<RequireAuth role="admin"><AdminAppointments /></RequireAuth>} />

            <Route path="/admin/analytics/referrals" element={<RequireAuth role="admin"><ReferralAnalytics /></RequireAuth>} />

            <Route path="/admin/analytics/wait-time" element={<RequireAuth role="admin"><WaitTimeAnalytics /></RequireAuth>} />

            <Route path="/admin/analytics/network" element={<RequireAuth role="admin"><NetworkAccess /></RequireAuth>} />

            <Route path="/admin/analytics/quality" element={<RequireAuth role="admin"><ProviderQuality /></RequireAuth>} />

            <Route path="/admin/audit" element={<RequireAuth role="admin"><AdminAuditLogs /></RequireAuth>} />

            <Route path="/admin/notifications" element={<RequireAuth role="admin"><Notifications /></RequireAuth>} />

            <Route path="/admin/settings" element={<RequireAuth role="admin"><SettingsPage /></RequireAuth>} />

            <Route path="/admin/help" element={<RequireAuth role="admin"><HelpPage /></RequireAuth>} />



            <Route path="*" element={<Navigate to="/" replace />} />

          </Routes>

        </div>

      </AuthProvider>

    </BrowserRouter>

  );

}





