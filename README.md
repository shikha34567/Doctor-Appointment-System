# Hospital Resource & Patient Flow Optimization System

An enterprise-grade, end-to-end healthcare operations management, patient flow optimization, and clinical resource decision-support platform. Built with a **FastAPI** backend, **Streamlit** multi-role interactive frontend, **SQLAlchemy** ORM, and an advanced **Machine Learning** pipeline (XGBoost, Random Forest, Gradient Boosting).

---

## 🌟 Executive Overview & Key Capabilities

The system upgrades the traditional doctor appointment portal into a hospital-wide operational platform:

* **55-Doctor Clinical Registry**: Preserves and operationalizes the comprehensive 55-physician registry spanning 11 clinical departments (Cardiology, General Medicine, Neurology, Orthopedics, Pediatrics, Dermatology, ENT, Ophthalmology, Gastroenterology, Gynecology & Obstetrics, Psychiatry).
* **Multi-Role RBAC Architecture**:
  * **Patient Portal**: Physician search by specialty, doctor profile cards, interactive booking with double-booking prevention, confirmation slips, and cancellation.
  * **Physician Clinical Portal**: Isolated schedule tracking, patient consultation notes, and status management (`Scheduled`, `Completed`, `Cancelled`). Mapped directly to unique doctor IDs.
  * **Hospital Operations Manager**: Executive operational analytics, bed occupancy tracking, daily patient inflow forecasting, emergency waiting-time analytics, what-if scenario simulator, and Power BI report exports.
* **Predictive Machine Learning Pipelines**:
  * **Inpatient Admission Forecasting**: Compares 14-day rolling averages, 7-day moving averages, Random Forest, Gradient Boosting, and XGBoost using chronological splits (preventing future data leakage). Generates 7-day and 30-day forecasts with 95% uncertainty intervals.
  * **Emergency Waiting-Time Estimation**: Predicts triage queue waiting times based on emergency priority (P1 to P5), arrival hour congestion, department workload, and clinical staffing. Provides feature importance explainability.
* **Bed Capacity & Occupancy Tracking**: Tracks concurrent active patient stays calculated from valid admission/discharge intervals across Emergency, ICU, General Wards, and Surgical units.
* **Interactive What-If Scenario Simulator**: Simulates Low (-20%), Normal (Baseline), and High (+35% surge / epidemic) demand scenarios using Little's Law steady-state calculations to project bed shortages and staffing deficits.
* **Power BI & Business Intelligence Integration**: Exports normalized, ready-to-ingest CSV datasets for Power BI Desktop and includes documented report creation instructions.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Streamlit, Plotly Express & Graph Objects, Custom CSS (HealthCare Blue & Teal Theme) |
| **Backend REST API** | FastAPI, Pydantic v2, Starlette, Uvicorn, Python-Multipart |
| **Security & Auth** | Argon2 / scrypt password hashing, PyJWT Bearer Tokens, Role-Based Access Control |
| **Database** | SQLite (local development with WAL & foreign keys enabled), PostgreSQL-compatible configuration, SQLAlchemy 2.0 ORM |
| **Data Science & ML** | Pandas, NumPy, Scikit-learn, XGBoost, Statsmodels, Joblib |
| **Testing & CI** | Pytest, HTTPX TestClient |

---

## 🔐 Provisioned Test Accounts

The database is pre-seeded with all 55 physicians, test patients, and the Operations Manager:

| Role | Email | Password | Scope / Mapped ID |
| :--- | :--- | :--- | :--- |
| **Hospital Operations Manager** | `admin.operations@healthcare.demo` | `Admin#Operations2026!` | Hospital-wide operational metrics, forecasting, bed management, reports |
| **Physician (Cardiology)** | `dr.johnsmith@healthcare.demo` | `Doctor#doc-0012026!` | Mapped to `doc-001`. Manages only Dr. John Smith's appointments |
| **Physician (General Medicine)** | `dr.davidwilson@healthcare.demo` | `Doctor#doc-0062026!` | Mapped to `doc-006`. Manages only Dr. David Wilson's appointments |
| **Patient** | `ananya.raman@healthcare.demo` | `Patient#Secure2026!` | Personal patient profile, booking flow, appointment slips |
| **Patient** | `karthik.verma@healthcare.demo` | `Patient#Secure2026!` | Personal patient profile, booking flow |

*Note: All 55 physicians can log in using their email and the standard format `Doctor#<doctor_id>2026!` (e.g., `Doctor#doc-0252026!`).*

---

## 📁 Project Directory Structure

```text
doctor-appointment/
├── app.py                      # Main Streamlit multi-role application
├── api/
│   ├── main.py                 # FastAPI application & lifespan management
│   ├── dependencies.py         # JWT auth, user context, RBAC security guards
│   ├── routes/
│   │   ├── auth.py             # Login, patient registration, /me, logout
│   │   ├── doctors.py          # 55 doctors directory & department details
│   │   ├── appointments.py     # Booking with duplicate prevention, queues, cancellation
│   │   ├── operations.py       # Executive overview, bed occupancy, staffing, simulation
│   │   └── reports.py          # Data export endpoints for Power BI / CSV
│   └── schemas/                # Pydantic request & response models
├── dashboard/
│   ├── styles.py               # Custom CSS (HealthCare blue/teal design system)
│   ├── api_client.py           # REST client connecting Streamlit to FastAPI
│   └── views/                  # 10 dedicated page views
│       ├── landing_login.py    # Page 1: Landing and secure login / signup
│       ├── patient_portal.py   # Page 2: Patient care and booking
│       ├── physician_portal.py # Page 3: Physician schedule and queues
│       ├── executive_overview.py # Page 4: Operations executive overview
│       ├── admission_forecasting.py # Page 5: Admission forecasting engine
│       ├── waiting_time_view.py # Page 6: Emergency waiting times & estimator
│       ├── bed_occupancy_view.py # Page 7: Bed occupancy & ward analytics
│       ├── staffing_view.py    # Page 8: Staff & resource capacity planning
│       ├── what_if_view.py     # Page 9: Interactive What-If Simulator
│       └── reports_view.py     # Page 10: Data insights & Power BI exports
├── database/
│   ├── db.py                   # SQLAlchemy engine and session management
│   ├── models.py               # Declarative ORM relational models
│   └── init_db.py              # Database initialization & 55-doctor seeder
├── src/
│   ├── synthetic_data.py       # Reproducible synthetic hospital operational data generator
│   ├── data_validation.py      # Schema, integrity, and data quality scorecard
│   ├── preprocessing.py        # Leakage-safe feature engineering & daily aggregations
│   ├── eda.py                  # Exploratory Data Analysis & Plotly figures
│   ├── forecasting.py          # Chronological admission forecasting pipeline
│   ├── waiting_time.py         # Emergency waiting-time regression & real-time estimator
│   ├── bed_occupancy.py        # Concurrent interval-based bed occupancy tracking
│   ├── resource_planning.py    # Staffing calculations & Little's Law simulator
│   └── explainability.py       # Explainable AI feature importance extractor
├── scripts/
│   ├── create_admin.py         # Provision Operations Manager CLI
│   ├── create_physician.py     # Provision Physician CLI
│   ├── create_patient.py       # Provision Patient CLI
│   ├── train_models.py         # End-to-end model training execution script
│   └── generate_reports.py     # Generates Power BI CSV extracts & reports
├── data/
│   ├── processed/              # Cleaned and engineered datasets
│   ├── synthetic/              # Generated synthetic operational records
│   └── doctors_registry.json   # 55 verified doctor profiles
├── models/                     # Saved model artifacts (.joblib and .json)
├── reports/                    # Exported Power BI CSVs and markdown reports
├── tests/                      # Pytest automated test suite (15 test cases)
├── .streamlit/
│   └── config.toml             # Streamlit theme & server configuration
├── .env.example                # Sample environment variables
├── requirements.txt            # Tested Python dependencies
└── README.md                   # System documentation
```

---

## 🚀 Local Installation & Execution (Windows / VS Code)

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.14.6)
* Git

### 2. Environment Configuration
Create your local `.env` file from the example:
```bash
copy .env.example .env
```

### 3. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 4. Initialize Database & Seed Doctors
```bash
py database/init_db.py
```

### 5. Train Machine Learning Models & Generate Reports
```bash
py scripts/train_models.py
py scripts/generate_reports.py
```

### 6. Run Automated Tests
```bash
py -m pytest -v
```

---

## 🖥️ Running the Application

The system operates as a decoupled architecture: run the **FastAPI Backend** and the **Streamlit Frontend** in separate terminal windows.

### Terminal 1: Start FastAPI REST Backend
```bash
py -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
* **Alternative API Docs (ReDoc)**: `http://127.0.0.1:8000/redoc`

### Terminal 2: Start Streamlit Frontend
```bash
py -m streamlit run app.py
```
* **Frontend Web Application**: `http://localhost:8501`

---

## 📊 Power BI Desktop Integration

1. Launch **Microsoft Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Select any of the pre-exported datasets located in the `reports/` folder:
   * `powerbi_admissions_trends.csv`: Daily admissions history, weekday flags, lag indicators.
   * `powerbi_bed_occupancy_history.csv`: Midday bed occupancy percentage and occupied bed counts.
   * `powerbi_department_capacity.csv`: Department-wise total beds, ICU capacity, and current utilization.
   * `powerbi_scenario_simulation_comparison.csv`: Comparative Little's Law benchmarks across Low, Normal, and High demand.
4. Click **Load** to ingest the tables into your Power BI data model.

---

## 🛡️ Responsible Use & Limitations Notice

* **Operational Decision-Support**: This software is designed for hospital operational workflow management, bed capacity planning, and staffing logistics. It is **not** an autonomous diagnostic, medical treatment, or clinical triage system.
* **Demonstration Lineage**: Data used for development and demonstration consists of verified doctor profiles combined with a reproducible synthetic operational dataset (`is_synthetic = True`).
* **Non-Guaranteed Estimates**: Emergency waiting-time predictions and admission forecasts are statistical estimates and should remain subject to hospital administrative and medical director review.
