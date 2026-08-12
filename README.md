# CarePath AI — Intelligent Clinical Referral & Appointment Orchestration Platform

CarePath AI is an enterprise healthcare decision-support platform that transforms patient clinical reports into structured medical intelligence, classifies required medical specialties, calculates queue-aware wait times using LightGBM machine learning models, recommends optimal specialists, and manages database-backed user authentication and referral workflows.

---

## 🌟 Key Features

- **Clinical Extraction Pipeline**: Parses medical reports (PDF/Images/Text) using OCR (Tesseract / EasyOCR / PyPDF2 / pdfplumber) and extracts clinical entities (ICD-10 codes, diagnoses, vitals, lab values, urgency indicators).
- **Specialty Classification & AI Triage**: Maps complex patient symptoms and clinical entities to target medical specialties with confidence scores and urgency levels (`ROUTINE`, `URGENT`, `EMERGENCY`).
- **Queue-Aware LightGBM Wait-Time Model**: Predicts specialist wait times using queue-theory features and trained LightGBM models.
- **Provider Recommendation Engine**: Ranks nearby healthcare providers based on distance, specialty match, accepted insurance, quality metrics, and estimated wait times.
- **Database-Backed Authentication (`PostgreSQL`)**: Secure user registration and login with `bcrypt` password hashing, RFC/Gmail validation, and role-based JWT access tokens (`patient`, `doctor`, `admin`).
- **Modern Responsive UX**: Reconstructed Vite + React dashboard with Tailwind CSS styling, interactive Leaflet provider maps, referral progress trackers, and direct booking.

---

## 🏗 System Architecture

```
[ Patient / Doctor UI ]
          │
          ▼  (REST API / JWT Auth)
[ FastAPI Backend Engine ]
   ├── Auth Service (Bcrypt + JWT)
   ├── Extraction Engine (OCR + Clinical NLP)
   ├── Classification Engine (Rule-based + Groq AI)
   ├── LightGBM Wait-Time Inference
   └── Provider Optimization Engine
          │
          ▼  (Async SQLAlchemy)
[ PostgreSQL Database ] ◄── (Users, Patients, Providers, Referrals, Appointments)
```

---

## 🛠 Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, Leaflet Maps, Axios, Sonner Toast
- **Backend**: Python 3.12, FastAPI, AsyncSQLAlchemy, Pydantic v2, PyJWT, Bcrypt
- **Machine Learning**: LightGBM, Scikit-learn, NumPy, Pandas
- **OCR & Extraction**: PyPDF2, pdfplumber, Tesseract OCR, EasyOCR, Pillow
- **Database**: PostgreSQL / SQLite (Development Fallback)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional, SQLite fallback available)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

Backend API Docs available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend application available at: `http://localhost:5173`

---

## 🔐 Default Demo Accounts

For testing, pre-seeded demo accounts are automatically initialized:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Patient** | `patient@carepath.ai` | `Patient@2026` |
| **Doctor** | `sarah.williams@carepath.ai` | `Doctor@2026` |
| **Admin** | `soniyaezhumalaisoniya@gmail.com` | `CarePath@2026` |

---

## 📄 License
CarePath AI · Clinical Decision Support System © 2026. All rights reserved.
