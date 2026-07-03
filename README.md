# Production Insurance Claims Processing Engine

A production-quality REST API engineered with Python 3.11+ and FastAPI designed to ingest, sanitize, process, and analyze relational insurance datasets. The system features a custom data parsing engine built using **Pandas** and enforces strict relational boundaries alongside financial business regulations.

---

## 📺 Project Demo & Walkthrough
See the complete system in action, including file ingestion, data quality filtering, and live analytical processing:
👉 **[Watch the System Demo Video on Google Drive](https://drive.google.com/file/d/12dIJ2r4VyCSv8YyNYQncoIqcuM4gv4ES/view?usp=sharing)**

---

## 🛠️ Technology Stack
* **Framework:** FastAPI (Asynchronous execution model & automated OpenAPI documentation)
* **Data Processing Layer:** Pandas (Vectorized cleaning, deduplication, and parsing)
* **ORM Engine:** SQLAlchemy 2.0 (Relational database schema modeling & raw SQL execution execution maps)
* **Database Platform:** SQLite (Zero-configuration file-based persistent backend storage)

---

## 📐 Design Decisions & Architecture
1. **Defensive Pre-Database ETL:** Instead of allowing dirty data to hit the database layer, the app implements a strict Pandas sanitation phase. It handles lowercasing headers, stripping whitespace, remapping irregular column naming patterns, and tracking primary key duplicates.
2. **Flexible Schema-to-File Handling:** Engineered to gracefully handle variations in column formatting (e.g., automatically matching `customer_id` rows down to unified relational primary keys).
3. **Data Integrity Checks:** Policies referencing orphaned or missing customer profiles are rejected. Financial values are programmatically checked against safety rules (e.g., rejecting negative losses or future incident timelines).
4. **Hybrid Query Engine:** Uses standard SQLAlchemy model relationships for routine CRUD lookups and dynamic parameters while leveraging highly optimized **raw SQL queries** for performance heavy geographical and consumer aggregate reporting.

---

## 📂 Core Directory Structure
```text
insurance_api/
│
├── app/
│   ├── models/            # SQLAlchemy Database Table Schemas (Customer, Policy, Claim)
│   ├── routers/           # Endpoint Layer Routes (Upload, Claims Query, Reporting)
│   ├── services/          # Pure Business Logic & Vectorized Pandas ETL Pipeline
│   ├── database.py        # SQLite Engine Inversion & Safe Session Lifecycle Helpers
│   └── main.py            # Main App Boot Factory & Infrastructure Probes
│
├── README.md
└── requirements.txt       # Declared Framework Dependencies
