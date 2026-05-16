# 🛒 CartTalk — AI Voice Grocery Assistant

**CartTalk** is an intelligent, bilingual (English + Malayalam) voice-powered grocery ordering system. Customers simply **speak** their grocery list, and CartTalk's AI handles everything — understanding items, suggesting recipes, enforcing stock limits, and confirming delivery.

---

## 🎯 Project Objective

To build a voice-first grocery ordering platform that eliminates the friction of traditional e-commerce for local grocery stores. CartTalk enables:

- **Elderly and non-tech-savvy users** to order groceries by simply talking
- **Regional language support** (Malayalam) for inclusive accessibility
- **Store owners** to manage inventory, orders, and analytics through a real-time merchant dashboard

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice Ordering** | Real-time bilingual voice conversation via WebSocket streaming |
| 🌐 **Bilingual NLP** | Automatic English / Malayalam detection and response |
| 🧠 **Smart Context** | Multi-turn conversation memory with sliding-window summarization |
| 🍛 **Recipe Assistant** | Say "Make chicken curry" — AI identifies and adds all ingredients instantly |
| 🔊 **Neural TTS** | Microsoft Edge Neural voices (`ml-IN-SobhanaNeural`, `en-US-AriaNeural`) with gTTS fallback |
| 🛡️ **Server-Side Stock Guard** | Every cart update is validated against live DB stock (incl. safety buffer). Overselling is impossible |
| 🔄 **Smart Reorder** | AI suggests frequently bought and monthly essential items before checkout |
| 📦 **Persistent Cart** | Cart synced to DB per phone number across sessions |
| 🔍 **Live Product Search** | Real-time product filtering on the storefront |
| 📊 **Merchant Analytics** | Revenue, top products, low stock alerts, and 7-day order trend charts |
| 🗒️ **Voice Logs** | Every AI interaction is logged for merchant review |
| 📋 **Order History** | Customers can view full order history with item breakdown |
| 📱 **Phone-Based Auth** | Simple phone number login with automatic account creation |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Frontend (React 18 + Vite)             │
│                                                          │
│  App.jsx (Router)      ProductGrid.jsx (Live Search)     │
│  CallInterface.jsx     AdminDashboard.jsx                │
│  AdminLogin.jsx        OrderHistory.jsx                  │
│                                                          │
│  components/                                             │
│    AnalyticsDashboard  RecentOrders  TopProducts         │
│    LowStockProducts    VoiceLogs     Logo  Icons         │
└─────────────────────────┬────────────────────────────────┘
                          │  REST (HTTP) + WebSocket
┌─────────────────────────┴────────────────────────────────┐
│                  Backend (FastAPI + Python)               │
│                                                          │
│  main.py         →  Routes, WebSocket handler            │
│  services.py     →  Gemini AI, TTS, stock validation     │
│  db.py           →  SQLite schema, CRUD, stock guard     │
│  ws_manager.py   →  Admin real-time WebSocket broadcast  │
│                                                          │
│            ┌─────────────────────────┐                   │
│            │  Google Gemini 2.0 Flash │                  │
│            │  Edge-TTS / gTTS         │                  │
│            │  SQLite3 Database        │                  │
│            └─────────────────────────┘                   │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **AI / NLP** | Google Gemini 2.0 Flash |
| **Text-to-Speech** | Edge-TTS (Neural), gTTS (fallback) |
| **Speech-to-Text** | Web Speech API (`en-IN` — bilingual) |
| **Database** | SQLite 3 |
| **Real-time** | WebSocket (voice streaming + admin push) |
| **Audio** | Web Audio API, MediaRecorder, Voice Activity Detection |

---

## 📁 Project Structure

```
carttalk/
├── backend/
│   ├── main.py              # FastAPI app, all routes, WebSocket handler
│   ├── services.py          # Gemini AI service, TTS, NLP pipeline, stock validation
│   ├── db.py                # SQLite schema, CRUD, validate_cart_stock()
│   ├── ws_manager.py        # Admin WebSocket broadcast manager
│   ├── cartalk.db           # SQLite database (auto-generated on first run)
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # API keys (not committed)
│   ├── .env.example         # Environment variable template
│   └── static/images/       # Uploaded product images
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app router and customer login
│   │   ├── CallInterface.jsx        # Voice call UI, WebSocket, audio playback
│   │   ├── ProductGrid.jsx          # Storefront product grid with live search
│   │   ├── AdminDashboard.jsx       # Merchant dashboard (inventory + orders)
│   │   ├── AdminLogin.jsx           # Merchant authentication
│   │   ├── OrderHistory.jsx         # Customer order history view
│   │   └── components/
│   │       ├── AnalyticsDashboard.jsx  # Revenue + 7-day order chart
│   │       ├── RecentOrders.jsx        # Latest orders table
│   │       ├── TopProducts.jsx         # Best-selling products
│   │       ├── LowStockProducts.jsx    # Stock alert panel
│   │       ├── VoiceLogs.jsx           # AI interaction log viewer
│   │       ├── Logo.jsx                # Brand logo component
│   │       └── Icons.jsx               # SVG icon set
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Run

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key — [Get one free here](https://aistudio.google.com/apikey)

### 1. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Open .env and set your GEMINI_API_KEY

# Start the backend server
python main.py
```

Backend runs at: `http://localhost:8000`  
Auto-generates `cartalk.db` and seeds sample products on first run.

### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Run development server
npm run dev

# Or build for production
npm run build
```

Frontend runs at: `http://localhost:5173`

---

## 📡 API Reference

### Customer Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Phone-based login (creates account if new) |
| `POST` | `/api/call/start` | Start a new voice call session |
| `WS` | `/api/call/{call_id}/stream` | Real-time voice WebSocket (text + binary audio) |
| `GET` | `/api/products` | List all products |
| `GET` | `/api/orders/user?phone={phone}` | Get a customer's order history |
| `POST` | `/api/cart/add` | Persist cart to database |

### Merchant / Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/products` | Add new product |
| `PUT` | `/api/products/{id}` | Update product (price, stock, image) |
| `DELETE` | `/api/products/{id}` | Delete product |
| `GET` | `/api/orders` | List all orders |
| `PUT` | `/api/orders/{id}/status` | Update order status |
| `DELETE` | `/api/orders/{id}` | Delete order |
| `GET` | `/api/admin/analytics` | Revenue, totals, 7-day trend |
| `GET` | `/api/admin/recent-orders` | Latest 10 orders |
| `GET` | `/api/admin/low-stock` | Products below safety stock level |
| `GET` | `/api/admin/top-products` | Best-selling products |
| `GET` | `/api/admin/voice-logs` | Recent AI voice interaction logs |
| `POST` | `/api/upload` | Upload product image |
| `WS` | `/api/admin/ws` | Real-time push notifications for dashboard |

---

## 🗄️ Database Schema

```sql
products    (id, name_en, name_ml, category, price, stock, image_url, safety_stock)
orders      (id, customer_phone, customer_name, customer_address, total,
             status, language, transcript, created_at)
order_items (id, order_id, product_id, quantity, price)
users       (phone, name, address, created_at)
cart_items  (id, phone, product_id, quantity)
voice_logs  (id, voice_input, ai_interpretation, action_performed, timestamp)
```

**Schema migration is automatic** — new columns are added on startup without data loss.

---

## 🛡️ Stock Validation System

CartTalk enforces a two-layer stock guard:

1. **Cart Layer** — Every time the AI updates the cart, `validate_cart_stock()` runs immediately. Quantities are clamped to `stock - safety_stock` (the same value shown to the AI). If a violation is found, the frontend receives a `stock_warning` WebSocket message and shows a dismissible red alert.

2. **Checkout Layer** — When `CONFIRM_ORDER` is issued, stock is re-validated one final time before the order is written. The SQL deduction uses `WHERE stock >= qty` to prevent race conditions between concurrent users.

---

## 🎙️ Voice Flow

```
User speaks
    │
    ▼
Web Speech API (en-IN) → transcript text
    │
    ▼
WebSocket → Backend (FastAPI)
    │
    ▼
GeminiService.process_text()
    ├── Build prompt (inventory + user history + conversation window)
    └── Gemini 2.0 Flash → structured response
            │
            ├── TRANSCRIPT   → shown on screen
            ├── DATA (cart)  → validated against DB stock
            ├── COMMAND      → UPDATE_CART | CONFIRM_ORDER | NONE
            ├── RESPONSE_TEXT → displayed in chat
            └── RESPONSE_AUDIO → sent to Edge-TTS → MP3 bytes → browser
```

---

## ⚙️ Environment Variables

```env
# backend/.env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

---

## 📝 Notes

- The database (`cartalk.db`) is auto-created and seeded with 7 sample products on first run.
- **Edge-TTS** is used by default for high-quality neural voices. If unavailable, **gTTS** is used as fallback automatically.
- The merchant admin default credentials are `admin / admin123`. **Change these before any public deployment.**
- All voice sessions are stored in-memory on the server. Restarting the server ends all active calls.

---

## 👨‍💻 Author

**Fahim** — Full-stack Development & AI Integration
