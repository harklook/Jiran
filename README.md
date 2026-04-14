# Jiran — AI-Assisted Inventory Optimization & Retailer Marketplace

Jiran is a centralized, web-based platform designed for small and mid-sized retailers to manage inventory more effectively, reduce stock imbalances, and make better operational decisions using analytics and AI-assisted forecasting. The platform brings together inventory tracking, demand insights, alerts, and a retailer-to-retailer marketplace in one system. It was developed as a university capstone project by Team OSCORP. 

## Product Overview

Many retailers operate with disconnected tools such as spreadsheets, POS systems, and manual records. Jiran addresses this by providing a single platform where retailers can:

- manage inventory across stores and locations,
- import or synchronize stock and sales data,
- monitor stock health and receive low-stock alerts,
- analyze sales and demand trends,
- identify slow-moving or dead stock, and
- redistribute excess inventory through a built-in marketplace.

The goal of Jiran is to improve inventory visibility, reduce overstocking and stockouts, and support data-driven stock movement between decentralized retailers.

## Key Features

- **Centralized inventory management** for adding, updating, importing, and monitoring stock.
- **AI-assisted analytics** for stock classification, demand forecasting, and recommendations.
- **Marketplace / stock exchange** for listing excess inventory and requesting stock from other retailers.
- **Low-stock and critical-stock alerts** to improve responsiveness.
- **POS and file import support** for integrating data from existing systems.
- **Retailer dashboard** for operational insights, inventory summaries, and analytics views.

## Target Users

Jiran is designed primarily for:

- small and medium-sized retailers,
- businesses operating across multiple locations,
- retailers using systems such as spreadsheets and POS platforms, and
- stores that need better visibility into stock movement and excess inventory.

## Tech Stack

- **Frontend:** React + Vite
- **Backend / ML Service:** Python + FastAPI
- **Database / Auth / Realtime:** Supabase (PostgreSQL + Authentication + Realtime)
- **Machine Learning:** Prophet, XGBoost, Gradient Boosting, Random Forest

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
- start the ML backend on **http://localhost:8001**, and
- start the frontend on **http://localhost:5173**.

Press `Ctrl+C` to stop both services.

## Prerequisites

| Tool | Minimum Version | Install |
|------|------------------|---------|
| Python | 3.9+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |

## Project Structure

```text
Jiran/
├── start.sh
├── README.md
├── frontend/                  # React + Vite frontend (port 5173)
│   ├── src/
│   ├── package.json
│   └── .env
└── ml_backend/                # FastAPI ML service (port 8001)
    ├── app.py
    ├── supabase_watcher.py
    ├── train.py
    ├── saved_models/
    ├── requirements.txt
    └── .env
```

## Core Workflows

Jiran supports the following business workflows:

1. **Authentication and onboarding** using secure retailer accounts.
2. **Inventory management** through manual updates, file imports, or POS synchronization.
3. **Stock monitoring** with low-stock, excess-stock, slow-moving, and dead-stock visibility.
4. **Demand forecasting** using historical sales and inventory data.
5. **Marketplace exchange** where retailers can list surplus stock and request needed inventory.
6. **Notifications and alerts** for stock issues and operational updates.

## ML API Reference

**Base URL:** `http://localhost:8001`  
**Interactive Docs:** `http://localhost:8001/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/predict-stock` | Predict stock status for products |
| POST | `/recommend` | Generate predictions and transfer/restock recommendations |
| GET | `/feature-importance` | Return top model features |

## Stock Labels

| Label | Meaning | Suggested Action |
|-------|---------|------------------|
| Low | Running low | Receive transfers or restock |
| Optimum | Healthy stock level | No action needed |
| Excess | Overstocked | Move stock to stores with lower availability |
| Slow | Slow-moving | Transfer to higher-demand stores |
| Dead | No recent sales | Clear or redistribute surplus stock |

## Data and Integration Notes

Jiran supports manual inventory imports and POS integration workflows. The platform is designed to work with structured sales and stock data, and the AI-assisted features rely on historical inventory and transaction records to generate useful predictions and recommendations.

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

### npm install fails (macOS)

```bash
xattr -cr frontend/
rm -rf frontend/node_modules
cd frontend && npm install
```

## Notes

- Jiran is an academic capstone project focused on inventory optimization, forecasting, and retailer collaboration.
- The current scope emphasizes inventory operations, AI-assisted recommendations, and stock exchange workflows rather than full ERP replacement.
