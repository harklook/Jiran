#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Oscorp Capstone — One-command startup
#  Starts ML backend (port 8001) + React frontend (port 5173)
# ─────────────────────────────────────────────────────────────

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
ML="$ROOT/ml_backend"
FE="$ROOT/frontend"

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[oscorp]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${BOLD}  Oscorp Capstone — Starting up${NC}"
echo "  ──────────────────────────────"
echo ""

# ── macOS: clear quarantine flags ────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
  log "Clearing macOS quarantine flags..."
  xattr -cr "$FE"  2>/dev/null || true
  xattr -cr "$ML"  2>/dev/null || true
  ok "Quarantine cleared"
fi

# ── Check .env for frontend ───────────────────────────────────
if [ ! -f "$FE/.env" ]; then
  if [ -f "$FE/.env.example" ]; then
    warn "frontend/.env not found — copying from .env.example"
    cp "$FE/.env.example" "$FE/.env"
    warn "Edit frontend/.env with your Supabase keys before using the app."
  else
    warn "frontend/.env not found. Create it before starting."
  fi
fi

# ── Resolve pip / python ─────────────────────────────────────
PIP=$(command -v pip3 || command -v pip || echo "")
PYTHON=$(command -v python3 || command -v python || echo "")
[ -z "$PIP" ]    && err "pip not found. Install Python from https://python.org"
[ -z "$PYTHON" ] && err "python not found. Install Python from https://python.org"

# ── Python deps ───────────────────────────────────────────────
log "Checking Python dependencies..."
if ! $PIP show fastapi &>/dev/null; then
  log "Installing Python dependencies..."
  $PIP install -r "$ML/requirements.txt" || err "pip install failed"
fi
ok "Python dependencies ready"

# ── Node deps ─────────────────────────────────────────────────
log "Checking Node dependencies..."
if [ ! -f "$FE/node_modules/.bin/vite" ]; then
  log "Running npm install..."
  (cd "$FE" && xattr -cr . 2>/dev/null; npm install) || err "npm install failed"
fi
ok "Node dependencies ready"

# ── Check ML models ───────────────────────────────────────────
if [ ! -f "$ML/saved_models/ensemble.pkl" ]; then
  warn "ML models not found. Running train.py first..."
  (cd "$ML" && $PYTHON train.py) || err "Training failed"
  ok "Models trained"
fi

echo ""
echo -e "${BOLD}  Starting services...${NC}"
echo ""

# ── Free ports if already in use ─────────────────────────────
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

# ── Start ML backend ──────────────────────────────────────────
log "Starting ML backend on http://localhost:8001 ..."
(cd "$ML" && uvicorn app:app --port 8001) &
ML_PID=$!

# Give the ML server a moment to load models before frontend hits it
sleep 4

# ── Start frontend ────────────────────────────────────────────
log "Starting React frontend on http://localhost:5173 ..."
(cd "$FE" && npm run dev) &
FE_PID=$!

echo ""
echo -e "${GREEN}${BOLD}  Both services are running!${NC}"
echo "  ──────────────────────────────────────────"
echo -e "  Frontend  →  ${CYAN}http://localhost:5173${NC}"
echo -e "  ML API    →  ${CYAN}http://localhost:8001${NC}"
echo -e "  API Docs  →  ${CYAN}http://localhost:8001/docs${NC}"
echo "  ──────────────────────────────────────────"
echo "  Press Ctrl+C to stop everything"
echo ""

# ── Graceful shutdown on Ctrl+C ───────────────────────────────
cleanup() {
  echo ""
  log "Stopping all services..."
  kill $ML_PID $FE_PID 2>/dev/null
  wait $ML_PID $FE_PID 2>/dev/null
  ok "All stopped. Goodbye."
  exit 0
}
trap cleanup SIGINT SIGTERM

wait $ML_PID $FE_PID
