# Oscorp Capstone — Jiran Inventory Intelligence

AI-powered inventory management system with stock status prediction, transfer recommendations across multiple store locations.

> **University capstone project** — credentials are included, no setup required.

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/M4MD-M7SN/capstone_oscorp.git
cd capstone_oscorp
```

### 2. Start everything

```bash
./start.sh
```

That's it. The script handles everything automatically:
- Clears macOS quarantine flags (Mac only)
- Installs Python and Node dependencies on first run
- Starts the ML backend on **http://localhost:8001**
- Starts the React frontend on **http://localhost:5173**

Press `Ctrl+C` to stop both services.

---

## Prerequisites

| Tool | Min Version | Install |
|------|-------------|---------|
| Python | 3.9+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |

---

## Project Structure

```
oscorp_capstone/
├── start.sh              ← Run this to start everything
├── README.md
│
├── frontend/             ← React + Vite app (port 5173)
│   ├── src/
│   ├── .env              ← Supabase credentials (included)
│   └── package.json
│
└── ml_backend/           ← Python FastAPI ML service (port 8001)
    ├── app.py            ← API server
    ├── supabase_watcher.py
    ├── train.py          ← Run only if models need retraining
    ├── saved_models/     ← Pre-trained model artifacts (included)
    ├── .env              ← Supabase credentials (included)
    └── requirements.txt
```

---

## ML API Reference

Base URL: `http://localhost:8001`
Interactive docs: `http://localhost:8001/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/predict-stock` | Predict stock status for products |
| `POST` | `/recommend` | Predictions + transfer & restock recommendations |
| `GET` | `/feature-importance` | Top model features |

### Stock Labels

| Label | Meaning | Action |
|-------|---------|--------|
| `Low` | Running low | Receive transfers or restock |
| `Optimum` | Healthy stock level | No action needed |
| `Excess` | Overstocked | Donate stock to Low stores |
| `Slow` | Slow-moving | Transfer to higher-demand stores |
| `Dead` | No recent sales | Clear out surplus stock |

---

## Supabase Watcher

The ML backend polls Supabase every 10 seconds for prediction jobs. To trigger a full recommendation run, run this in the Supabase SQL editor:

```sql
INSERT INTO ml_triggers (status, trigger_type)
VALUES ('pending', 'recommend');
```

Results are saved to `ml_backend/ml_outputs/`.

### Required Supabase Tables

If the tables don't exist yet, create them in the Supabase SQL editor:

```sql
CREATE TABLE public.ml_triggers (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status         text NOT NULL DEFAULT 'pending',
  trigger_type   text NOT NULL DEFAULT 'recommend',
  filter_store   text,
  filter_product text,
  created_at     timestamptz DEFAULT now(),
  completed_at   timestamptz,
  error_msg      text,
  result_file    text
);

CREATE TABLE public.ml_inventory (
  store_id              text,
  product_id            text,
  product_name          text,
  category              text,
  stock_qty             float8,
  retail_price          float8,
  recent_qty            float8,
  recent_txns           float8,
  recent_avg            float8,
  recent_std            float8,
  historical_qty        float8,
  historical_txns       float8,
  historical_avg        float8,
  total_sold            float8,
  num_sales             float8,
  days_since_last_sale  float8,
  store_total_txns      float8
);
```

---

## Troubleshooting

**`Operation not permitted` on Mac**
```bash
xattr -cr frontend/
xattr -cr ml_backend/
```

**ML models missing**
```bash
cd ml_backend && python3 train.py
```

**Port already in use**
```bash
lsof -ti:8001 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**npm install fails**
```bash
xattr -cr frontend/
rm -rf frontend/node_modules
cd frontend && npm install
```
