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
