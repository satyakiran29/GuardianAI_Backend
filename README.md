# 🛡️ GuardianAI Backend — Emergency Safety & Incident Command Platform

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.14+-a30000?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Realtime-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**GuardianAI** (also known as *SheGuard*) is a mission-critical backend engine and real-time emergency incident command platform designed for women safety, personal protection, and rapid guardian dispatch. 

It provides secure RESTful APIs for mobile and IoT clients, live location telemetry tracking, multi-channel SOS triggers, automated OTP verification, Supabase real-time cloud synchronization, and a centralized web-based Command & Control Dashboard.

---

## 🌟 Key Features

### 🚨 1. Real-Time Emergency SOS & Incident Dispatch
- **Multi-Modal SOS Triggers**: Handles trigger signals from hardware SOS buttons, shake gestures, voice keywords, safety timer expirations, critical low-battery alerts (15%), safe mode broadcasts, and trip route divergences.
- **Live Location Telemetry**: Continuous GPS ping ingestion with address reverse-geocoding, battery status monitoring, and siren tracking.
- **Incident Lifecycle Management**: Immediate alert broadcast (`active`), responder dispatch (`dispatched`), and resolution tracking with incident notes (`resolved`).

### 🔐 2. Authentication & Verification Gateway
- **Dynamic OTP Dispatch & Verification**: Time-expiring (10 min) 6-digit numeric OTP generation and verification for registration and logins.
- **Multi-Role User Hierarchy**:
  - `superadmin`: Full platform control, user privilege modification, telemetry audits, and data exports.
  - `guardian`: Trusted responders, emergency contact dispatchers, and resolution officers.
  - `user`: Protected citizens and app users with active emergency telemetry broadcast.
- **Master Passcodes**: Built-in test passcodes (`123456` OTP, `admin123` / `guardian123` passwords) for seamless testing and demonstration.

### 🌐 3. Supabase Real-Time Cloud Integration
- Real-time synchronization of users, emergency SOS events, emergency contacts, and OTP logs to Supabase PostgreSQL.
- Enables instant websocket event broadcasting across mobile applications and operations dashboards.

### 🖥️ 4. Mission Command Center (Web Dashboard)
- **Live Incident Radar**: Real-time visual tracking of active emergency events and battery levels.
- **Incident Dispatch & Action Center**: One-click responder assignment, siren controls, and alert resolution.
- **User Management & Role Switching**: Instant privilege elevation and user status controls.
- **Data Export**: Comprehensive CSV export for reporting, audit logging, and incident compliance.
- **Live OTP Telemetry Monitor**: Visual tracking of incoming authentication codes and validity states.

### 📞 5. Emergency Helplines & Contacts Directory
- Integrated directory of national emergency helplines (112, 1091 Women Helpline, 1930 Cyber Crime, 100 Police, 108 Ambulance, 18005990019 KIRAN Mental Health).
- User-specific primary and secondary emergency contact management.

---

## 🏗️ System Architecture & Flowcharts

### 1. High-Level System Architecture Flow

```mermaid
flowchart TB
    subgraph CLIENTS["📱 Client Tier"]
        MA["Mobile Application (iOS / Android)"]
        IOT["Wearable / IoT Safety Devices"]
        WEB_CLIENT["Web Portal Client"]
    end

    subgraph API_GATEWAY["🛡️ GuardianAI Backend (Django REST Framework)"]
        direction TB
        MW["Security, CORS & WhiteNoise Middleware"]
        ROUTER["URL Dispatcher & Router"]
        
        subgraph CORE_APPS["Application Modules"]
            AUTH["🔐 Auth & OTP Gateway<br/>(Send / Verify / Passcode Bypass)"]
            SOS_ENGINE["🚨 SOS & Telemetry Engine<br/>(Triggers / GPS Pings / Geo-Reverse)"]
            MGMT["👥 User & Contact Directory<br/>(Profiles / Roles / Helplines)"]
            DASH_ENGINE["🖥️ Mission Control Web Views<br/>(Triage / Dispatch / Role Switch / CSV)"]
        end

        DB_ORM["Django ORM Layer"]
    end

    subgraph PERSISTENCE["💾 Data & Real-Time Sync Tier"]
        SQLITE[("Local SQLite Database<br/>(db.sqlite3)")]
        SUPABASE[("⚡ Supabase PostgreSQL<br/>(Cloud Storage)")]
        REALTIME["📡 Supabase Realtime<br/>(WebSocket Publication)"]
    end

    subgraph RESPONDERS["🚨 First Responders & Operations Tier"]
        DASHBOARD["🖥️ Live Command Center Dashboard<br/>(Incident Radar & Action Panel)"]
        POLICE["🚓 Police / 112 Emergency Dispatch"]
        GUARDIANS["👨‍👩‍👧 Family & Trusted Guardians"]
    end

    %% Client to Backend
    MA -->|HTTPS / REST API| MW
    IOT -->|Hardware SOS / Telemetry| MW
    WEB_CLIENT -->|Session Auth / HTTP| MW
    MW --> ROUTER
    ROUTER --> AUTH
    ROUTER --> SOS_ENGINE
    ROUTER --> MGMT
    ROUTER --> DASH_ENGINE

    %% Backend to Database & Supabase
    AUTH & SOS_ENGINE & MGMT & DASH_ENGINE --> DB_ORM
    DB_ORM --> SQLITE
    SOS_ENGINE -.->|Cloud Upsert & Sync| SUPABASE
    MGMT -.->|User Profiles Sync| SUPABASE
    SUPABASE --> REALTIME

    %% Realtime to Operations
    REALTIME ==>|Live Push Alert| DASHBOARD
    DASH_ENGINE --> DASHBOARD
    DASHBOARD -->|Dispatch Action| POLICE
    DASHBOARD -->|Notification Alert| GUARDIANS
```

---

### 2. Emergency SOS Incident Lifecycle & Resolution Flowchart

```mermaid
flowchart TD
    START(["🚨 Emergency Trigger Event"])
    
    subgraph TRIGGERS["Trigger Sources"]
        T1["SOS Button Press"]
        T2["Device Shake Detection"]
        T3["Voice Keyword Activation"]
        T4["Safety Timer Expiration"]
        T5["Battery Critical (&lt; 15%)"]
        T6["Route Divergence / Geofence"]
    end

    TRIGGERS --> START

    START --> POST_ALERT["POST /api/sos/trigger/"]
    
    subgraph BACKEND_PROCESSING["Backend Processing Pipeline"]
        VALIDATE["Validate & Associate User Profile"]
        LOG_DB["Create EmergencyAlert in Database (Status: Active)"]
        UPDATE_LOC["Update GPS Telemetry (Lat, Lng, Address)"]
        SYNC_CLOUD["Sync to Supabase Realtime Table: emergency_alerts"]
    end

    POST_ALERT --> VALIDATE
    VALIDATE --> LOG_DB
    LOG_DB --> UPDATE_LOC
    UPDATE_LOC --> SYNC_CLOUD

    SYNC_CLOUD --> BROADCAST{{"📡 Real-Time Incident Broadcast"}}

    subgraph ACTION_COMMAND["Mission Command & Dispatch"]
        RADAR["Web Dashboard Live Radar Alarm Triggers"]
        NOTIF["Emergency Contacts Alerted"]
        DISPATCH_DECISION{"Responder Action"}
    end

    BROADCAST --> RADAR
    BROADCAST --> NOTIF
    RADAR --> DISPATCH_DECISION

    DISPATCH_DECISION -->|Dispatch Guardian/Police| DISPATCHED["Status: Dispatched<br/>POST /dashboard/alerts/&lt;id&gt;/dispatch/"]
    DISPATCHED --> ASSIST["Responder Reaches Citizen & Secures Area"]
    ASSIST --> RESOLVE["POST /api/sos/resolve/<br/>Status: Resolved"]
    DISPATCH_DECISION -->|False Alarm / Direct Safe| RESOLVE

    RESOLVE --> ARCHIVE[("Incident Logged, Timestamped & Archived")]
    ARCHIVE --> END(["✅ Situation Safe & Closed"])
```

---

## 📂 Project Structure

```
GuardianAI_Backend/
├── manage.py                   # Django project CLI entrypoint
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment process configuration (Gunicorn)
├── build.sh                    # Automated build, migration & seed script
├── runtime.txt                 # Python runtime version definition
├── db.sqlite3                  # Local SQLite database
├── supabase_schema.sql         # Supabase PostgreSQL schema & realtime policies
├── guardian_backend/           # Core Django project configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # App settings, CORS, Whitenoise, Supabase keys
│   ├── urls.py                 # Root URL router
│   └── wsgi.py
├── guardian_api/               # RESTful API application
│   ├── models.py               # UserProfile, EmergencyAlert, OtpRecord, TripLog, EmergencyContact
│   ├── serializers.py          # DRF Serializers
│   ├── views.py                # API endpoints (Auth, SOS, Telemetry, Contacts)
│   ├── urls.py                 # API route definitions (`/api/...`)
│   ├── supabase_client.py      # Supabase cloud sync integration
│   └── management/commands/
│       └── seed_demo_data.py   # Seeder for demo accounts, guardians, and telemetry
└── dashboard/                  # Operations Web Dashboard application
    ├── urls.py                 # Dashboard view routes (`/`, `/users`, `/alerts`, `/otp`)
    ├── views.py                # Dashboard views, session auth & CSV export
    ├── static/                 # Static assets, CSS, JS, branding
    └── templates/dashboard/    # Responsive HTML templates
        ├── base.html           # Base layout with sidebar navigation
        ├── index.html          # Mission control & live statistics
        ├── alerts.html         # Active SOS triage and responder dispatch
        ├── users.html          # User directory & privilege management
        ├── otp.html            # Real-time OTP monitoring terminal
        └── login.html          # Command center authentication
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (Recommended: Python 3.11 or 3.12)
- **pip** and **virtualenv**
- (Optional) **Supabase Account** for cloud database & realtime sync

---

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/satyakiran29/GuardianAI_Backend.git
cd GuardianAI_Backend

# Create and activate virtual environment
# On Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory (or configure your hosting environment):

```env
# Django Settings
DJANGO_SECRET_KEY=your-secure-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Supabase PostgreSQL (Permanent Cloud Storage)
# Get from: Supabase Project Settings -> Database -> Connection string (URI)
DATABASE_URL=postgresql://postgres.jwntzspmzapxablkmqhp:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

# Supabase REST/Realtime Integration
SUPABASE_URL=https://jwntzspmzapxablkmqhp.supabase.co
SUPABASE_KEY=your-supabase-service-or-anon-key

# Optional: Set to 'true' if you want to seed initial demo accounts on build
SEED_DEMO_DATA=false
```

### 4. Database Setup & Demo Data Seeding

```bash
# Apply database migrations
python manage.py migrate

# Seed pre-configured SuperAdmins, Responders, Users, and Sample SOS Alerts
python manage.py seed_demo_data
```

### 5. Run Local Development Server

```bash
python manage.py runserver
```

Once started, access:
- **Operations Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **REST API Endpoints**: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🔑 Default Demo Credentials

You can log into the web dashboard or authenticate via API using these pre-seeded accounts:

| Role | Email / Phone | Password | Master OTP |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `satya@guardianai.app` / `+919999000001` | `admin123` | `123456` |
| **Super Admin** | `superadmin@guardianai.app` / `+919999000099` | `admin123` | `123456` |
| **Guardian / Responder** | `mom@guardianai.app` / `+15552345678` | `guardian123` | `123456` |
| **Protected User** | `ananya@guardianai.app` / `+919876543210` | `guardian123` | `123456` |

---

## 📡 REST API Reference

All API routes are prefixed with `/api/`.

### 🔐 Authentication & Verification
| Method | Endpoint | Description | Sample Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/send-otp/` | Dispatch a 6-digit OTP to phone/email | `{"target": "+919876543210", "purpose": "login"}` |
| `POST` | `/api/auth/verify-otp/` | Verify OTP code (or bypass with `123456`) | `{"target": "+919876543210", "otp_code": "123456"}` |
| `POST` | `/api/auth/register/` | Register or update user profile | `{"name": "Ananya", "phone": "+919876543210", "role": "user"}` |
| `POST` | `/api/auth/login/` | Authenticate via Password or OTP | `{"identifier": "+919876543210", "password": "guardian123"}` |

### 🚨 Emergency SOS & Telemetry
| Method | Endpoint | Description | Sample Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/sos/trigger/` | Broadcast emergency SOS incident | `{"phone": "+919876543210", "latitude": 17.3850, "longitude": 78.4867, "trigger_source": "button", "siren_active": true}` |
| `POST` | `/api/sos/resolve/` | Resolve active SOS incident | `{"alert_id": 1, "notes": "Safe at home", "responder_id": 1}` |
| `POST` | `/api/location/ping/` | Ingest live telemetry & battery level | `{"phone": "+919876543210", "latitude": 17.4435, "longitude": 78.3772, "battery_level": 82}` |

### 👥 Users, Contacts & Helplines
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/users/` | Retrieve all registered users (supports `?role=guardian` filter) |
| `GET` | `/api/contacts/` | Retrieve emergency contacts (`?user_id=1` or `?phone=+91...`) |
| `POST` | `/api/contacts/` | Add emergency contact for a user |
| `GET` | `/api/helplines/` | Get list of emergency helpline numbers (112, 1091, 100, 108, etc.) |
| `GET` | `/api/dashboard/stats/`| Aggregated platform statistics & recent alerts |

---

## ⚡ Supabase Setup (Optional Cloud Sync)

To enable live cloud sync and Realtime WebSocket subscriptions:

1. Create a project on [Supabase](https://supabase.com/).
2. Open the **SQL Editor** in the Supabase Dashboard.
3. Paste and execute the contents of [`supabase_schema.sql`](file:///h:/Github/GuardianAI_Backend/supabase_schema.sql).
4. Copy your project **URL** and **anon/service key** to your `.env` file (`SUPABASE_URL` and `SUPABASE_KEY`).

---

## 🚢 Deployment

### Production Deployment (Heroku / Render / Railway)

This repository includes pre-configured deployment files:
- **`Procfile`**: Runs Gunicorn WSGI server: `web: gunicorn guardian_backend.wsgi:application --log-file -`
- **`build.sh`**: Runs dependency installation, asset collection (`collectstatic`), migrations, and seed data.
- **`runtime.txt`**: Specifies Python runtime `python-3.11.8`.

#### Example Deployment on Render / Railway:
1. Connect your GitHub repository.
2. Set Build Command: `./build.sh` or `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Set Start Command: `gunicorn guardian_backend.wsgi:application`
4. Set Environment Variables: `DJANGO_SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com,yourdomain.com`.

---

## 🛡️ Security & Privacy Notice
- This platform handles sensitive location and emergency telemetry. Ensure `DEBUG=False` and set restrictive `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` before production deployment.
- Passwords should be hashed in production using standard Django authentication backends.
- Set appropriate Row Level Security (RLS) policies in Supabase for user data protection.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!
Feel free to open a pull request or submit an issue to help make communities safer.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
