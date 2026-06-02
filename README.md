# Jiran — AI-Assisted Inventory Optimization & Retailer Marketplace

**Small Stores. Big Network.**

Jiran is a centralized, web-based inventory intelligence platform designed for small and mid-sized retailers to manage stock more effectively, reduce inventory imbalances, and make better operational decisions using analytics and AI-assisted forecasting.

The platform brings together inventory tracking, demand insights, stock health alerts, AI-assisted recommendations, and a retailer-to-retailer marketplace in one system. It was developed as a CSIT321 capstone startup-style project by Team OSCORP/Jiran at the University of Wollongong in Dubai.

---

## Product Overview

Many small and mid-sized retailers operate with disconnected tools such as spreadsheets, POS systems, manual records, and isolated store-level inventory processes. This creates a common problem: one store may have excess or dead stock sitting idle, while another nearby store may be running low on the same product.

Jiran addresses this problem by providing a shared platform where retailers can:

- manage inventory across stores and locations,
- import or synchronize stock and sales data,
- monitor stock health and receive low-stock alerts,
- analyze sales and demand trends,
- identify slow-moving, dead, low, excess, and optimum stock,
- receive AI-assisted stock recommendations, and
- redistribute excess inventory through a built-in retailer marketplace.

The goal of Jiran is to improve inventory visibility, reduce overstocking and stockouts, and support data-driven stock movement between decentralized retailers.

---

## Key Features

- **Centralized Inventory Management**  
  Add, update, import, and monitor stock across stores and product categories.

- **AI-Assisted Analytics**  
  Supports stock classification, demand forecasting, and recommendation-driven inventory optimization.

- **Retailer Marketplace / Stock Exchange**  
  Allows retailers to list excess inventory, request needed products, and rebalance supply across nearby stores.

- **Low-Stock and Critical-Stock Alerts**  
  Helps retailers respond earlier to low stock, out-of-stock risk, and inventory imbalance.

- **POS and File Import Support**  
  Supports structured inventory import workflows and POS integration concepts. Square POS was used for the prototype implementation.

- **Retailer Dashboard**  
  Provides operational insights, inventory summaries, analytics views, and stock health indicators.

- **Recommendation Engine**  
  Generates transfer/restock suggestions based on stock status, demand patterns, and inventory imbalance.

---

## Target Users

Jiran is designed primarily for:

- independent retailers,
- small and medium-sized retailers,
- businesses operating across multiple locations,
- retailers using spreadsheets, POS platforms, or manual inventory records,
- stores with excess, dead, slow-moving, low, or imbalanced stock, and
- retailers that need affordable inventory intelligence without adopting complex ERP systems.

---

## Tech Stack

- **Frontend:** React, Vite, JavaScript
- **Backend / ML Service:** Python, FastAPI
- **Database / Auth / Realtime:** Supabase, PostgreSQL, Supabase Authentication, Supabase Realtime
- **Machine Learning:** Prophet, XGBoost, Gradient Boosting, Random Forest
- **Integration:** Square POS integration for prototype workflows
- **Version Control:** GitHub

---

## AI / ML Components

Jiran uses AI-assisted analytics to support inventory decision-making.

The machine learning components include:

- demand forecasting using historical sales and inventory data,
- stock classification into operational categories,
- recommendation logic for stock transfer and restocking,
- feature importance analysis for model interpretability, and
- AI-assisted stock optimization workflows.

### Stock Classification Labels

| Label | Meaning | Suggested Action |
|---|---|---|
| Low | Running low | Receive transfers or restock |
| Optimum | Healthy stock level | No action needed |
| Excess | Overstocked | Move stock to stores with lower availability |
| Slow | Slow-moving | Transfer to higher-demand stores |
| Dead | No recent sales | Clear or redistribute surplus stock |

---

## Core Workflows

Jiran supports the following business workflows:

1. **Authentication and Onboarding**  
   Retailers access the platform through secure account-based authentication.

2. **Inventory Management**  
   Retailers can manage inventory through manual updates, file imports, or POS synchronization workflows.

3. **Stock Monitoring**  
   The system identifies low-stock, excess-stock, slow-moving, and dead-stock conditions.

4. **Demand Forecasting**  
   Historical sales and inventory data are used to support demand predictions.

5. **Marketplace Exchange**  
   Retailers can list surplus stock and request needed inventory from other retailers.

6. **Recommendations and Alerts**  
   The platform provides alerts and recommendations for operational stock decisions.

---

## Project Structure

```text
Jiran/
├── start.sh
├── README.md
├── frontend/                  # React + Vite frontend (port 5173)
│   ├── src/
│   ├── package.json
│   └── .env.example
└── ml_backend/                # FastAPI ML service (port 8001)
    ├── app.py
    ├── supabase_watcher.py
    ├── train.py
    ├── saved_models/
    ├── requirements.txt
    └── .env.example
```

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---:|---|
| Python | 3.9+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |

---

## Environment Setup

This project uses local environment variables.

Real `.env` files are intentionally not committed to version control. Use `.env.example` files as templates.

### 1. Copy the example environment files

```bash
cp frontend/.env.example frontend/.env
cp ml_backend/.env.example ml_backend/.env
```

### 2. Fill in the required local values

Example frontend variables may include:

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_BASE_URL=http://localhost:8001
```

Example backend variables may include:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_if_required
```

> **Security Note:** Do not commit real API keys, credentials, access tokens, database URLs, or service role keys to GitHub.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/harklook/Jiran.git
cd Jiran
```

### 2. Start the project

```bash
./start.sh
```

The startup script will:

- install Python and Node dependencies on first run,
- start the ML backend on `http://localhost:8001`, and
- start the frontend on `http://localhost:5173`.

Press `Ctrl+C` to stop both services.

---

## ML API Reference

**Base URL:** `http://localhost:8001`  
**Interactive Docs:** `http://localhost:8001/docs`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/predict-stock` | Predict stock status for products |
| POST | `/recommend` | Generate predictions and transfer/restock recommendations |
| GET | `/feature-importance` | Return top model features |

---

## Data and Integration Notes

Jiran supports manual inventory imports and POS integration workflows. The platform is designed to work with structured sales and stock data, and the AI-assisted features rely on historical inventory and transaction records to generate useful predictions and recommendations.

Square POS was used for the prototype implementation. Additional POS and e-commerce integrations were considered as part of the broader system design.

---

## Security Considerations

Jiran includes several security-related design considerations:

- Supabase Authentication for user login and account access,
- role-based access control considerations,
- protected application routes,
- environment variable and secret management,
- API validation considerations,
- retailer data privacy and access control,
- multi-tenant data protection considerations, and
- secure handling of POS/API integration credentials.

Environment variables and API keys should be stored locally in `.env` files and should not be committed to version control.

---

## My Role

Originated the concept for Jiran and co-developed it with my capstone team from idea to working prototype.

Contributed across:

- product planning,
- feature planning,
- user flows,
- system design,
- frontend development,
- backend integration,
- database workflows,
- API/POS integration,
- inventory workflows,
- marketplace features,
- analytics functionality,
- recommendation logic,
- testing and debugging,
- technical documentation,
- presentation, and
- security-related system considerations.

---

## Troubleshooting

### ML models missing

```bash
cd ml_backend && python3 train.py
```

### Port already in use

```bash
lsof -ti:8001 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### npm install fails on macOS

```bash
xattr -cr frontend/
rm -rf frontend/node_modules
cd frontend && npm install
```

---

## Project Status and Limitations

Jiran is an academic capstone prototype focused on inventory optimization, forecasting, and retailer collaboration.

The current scope emphasizes:

- inventory operations,
- AI-assisted recommendations,
- stock classification,
- stock exchange workflows,
- dashboard-based insights, and
- prototype-level POS/data integration.

Current limitations include:

- prototype-level POS integration,
- no full payment gateway in the MVP,
- no mobile app in the MVP,
- some workflows simplified for academic demonstration,
- regional focus on UAE/GCC retail use cases, and
- prototype/demo data used in some scenarios.

Jiran is not a full ERP replacement. It is designed to demonstrate how lightweight inventory intelligence and retailer-to-retailer stock redistribution can support small and mid-sized retailers.

---

## Capstone Context

Developed as a CSIT321 capstone startup-style project by Team OSCORP/Jiran at the University of Wollongong in Dubai.

The project was built to demonstrate real-world business potential through a working prototype, technical documentation, testing, and product presentation.
