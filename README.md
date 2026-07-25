# 🛡️ KSP CrimeAI — Command Center

**An AI-Powered Crime Investigation & Analytics Platform for Karnataka State Police**

Built on **Zoho Catalyst** for the Karnataka State Police Hackathon, organized by **Hack2Skill**.
<img width="851" height="237" alt="Screenshot 2026-07-25 094436" src="https://github.com/user-attachments/assets/0b933846-bd56-4a85-a035-2c4e7af88861" />


---

## 📖 About the Project

KSP CrimeAI is a role-based command center that helps police officers investigate, predict, and manage crime more efficiently. It combines a conversational AI assistant, predictive crime analytics, criminal network mapping, and case management in one dashboard — built end-to-end on Zoho Catalyst.

---

## ✨ Features
<img width="1406" height="638" alt="image" src="https://github.com/user-attachments/assets/9a170366-ea7c-4cd4-8cfd-e4efe33baa78" />

- **Role-based officer access** — Sub-Inspector, Inspector, Senior Inspector, Analyst, Policymaker, each with permitted data access
- **AI Chatbot** — multi-agent system (Query, Prediction, RAG, Summary agents) answering officer queries in English and Kannada
- **Predictive crime analytics** — ML-based risk prediction, hotspot forecasting, repeat-offender likelihood
- **Interactive crime maps** — district and city-level crime density visualization
- **Criminal network graph** — visualizes offender connections and gang links
- **Case summary & timeline** — AI-generated case overviews combining FIR, victim, and investigation data
- **Conversation export** — chatbot conversations exportable as PDF
- **Multilingual support** — English, Kannada, Hindi, Urdu
- **Audit logging** — every query logged for compliance

---

<img width="1200" height="675" alt="image" src="https://github.com/user-attachments/assets/5a41f410-a854-4d11-bb92-299186e27842" />


## 🏗️ Tech Stack 
<img width="1500" height="718" alt="image" src="https://github.com/user-attachments/assets/fa7d0c2e-7247-4523-b532-5ffdc04665a9" />

**Frontend**
- Angular
- Chart.js (analytics visualizations)
- Leaflet.js (crime maps)
- D3.js (criminal network graph)
- Deployed on Zoho Catalyst Web Client Hosting

**Backend**
- Python (Flask) on Zoho Catalyst Functions
- Zoho Catalyst Data Store (ZCQL) for structured crime data
- Zoho Catalyst QuickML for prediction models and RAG-based knowledge search
- OAuth-based token management for secure API access

---

## 🚀 Getting Started

### Prerequisites
- Node.js & npm
- Angular CLI
- Zoho Catalyst CLI
- Python 3.12

### Frontend Setup
```bash
cd client
npm install
ng serve
```

### Backend Setup
```bash
cd functions/ksp_crime_agent_function
pip install -r requirements.txt
```

### Deploy to Zoho Catalyst
```bash
catalyst deploy
```

### SNAPSHOTS OF THE PROTOTYPE 
---  

<img width="1362" height="642" alt="image" src="https://github.com/user-attachments/assets/0d083173-441a-47f7-93a2-8b35be872800" />

<img width="1167" height="631" alt="Screenshot 2026-07-24 165242" src="https://github.com/user-attachments/assets/fd6b7149-c01c-460f-8fbd-95f6e1822e8d" />

<img width="1364" height="635" alt="Screenshot 2026-07-24 165041" src="https://github.com/user-attachments/assets/584bd12b-1955-4919-ae35-51d039741b82" />

<img width="1365" height="631" alt="Screenshot 2026-07-25 095550" src="https://github.com/user-attachments/assets/4009b709-3fee-4eb7-a801-512f30c77afb" />



## 🔗 Live URLs

- **Frontend:** https://ksp-crime-agent-60072886153.development.catalystserverless.in/app/login
- **Backend:** https://ksp-crime-agent-60072886153.development.catalystserverless.in/server/ksp_crime_agent_function

---

## 👥 Team — One of Us Is Lying

| Role | Name |
|------|------|
| Team Leader | Mudasir Pasha |
| Member | Voni Purujit |
| Member | Aditya M P |

*Karnataka State Police Hackathon — Organized by Hack2Skill*
