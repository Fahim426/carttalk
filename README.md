# 🛒 CartTalk — AI Voice Grocery Assistant

**CartTalk** is an intelligent, bilingual (English + Malayalam) voice-powered grocery ordering system. Customers simply **speak** their grocery list, and CartTalk's AI assistant handles everything — from understanding items to suggesting recipes and confirming delivery.

---

## 🎯 Project Objective

To build a voice-first grocery ordering platform that eliminates the friction of traditional e-commerce for local grocery stores. CartTalk enables:
- **Elderly and non-tech-savvy users** to order groceries by simply talking
- **Regional language support** (Malayalam) for inclusive accessibility
- **Store owners** to manage inventory and orders through a merchant dashboard

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice Ordering** | Real-time voice conversation with AI assistant via WebSocket |
| 🌐 **Bilingual NLP** | Automatic English/Malayalam detection and response |
| 🧠 **Smart Context** | Multi-turn memory with auto-summarization for long sessions |
| 🍛 **Recipe Assistant** | Ask "How to make Chicken Curry?" — AI suggests recipe + adds ingredients to cart |
| 🔊 **Neural TTS** | Microsoft Edge neural voices (with gTTS fallback) |
| 🔍 **Live Search** | Real-time product filtering as you type |
| 📦 **Order Management** | Full order lifecycle with transcript history |
| 🏪 **Merchant Dashboard** | Inventory CRUD, order tracking, stock management |
| 🛡️ **Stock Safety** | Safety stock limits prevent overselling |
| 🔄 **Smart Reorder** | AI remembers frequent purchases for personalized suggestions |
| 📱 **Phone Auth** | Simple phone-based login with persistent cart |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ App.jsx  │  │ProductGrid│  │ CallInterface    │   │
│  │ (Router) │  │ (Search)  │  │ (Voice + WebSocket)│  │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐   │
│  │AdminDashboard│  │OrderHist │  │ AdminLogin   │   │
│  └──────────────┘  └──────────┘  └──────────────┘   │
└────────────────────────┬────────────────────────────┘
                         │ HTTP + WebSocket
┌────────────────────────┴────────────────────────────┐
│                 Backend (FastAPI + Python)           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ main.py  │  │ services.py  │  │   db.py      │   │
│  │ (Routes) │  │ (Gemini AI)  │  │  (SQLite)    │   │
│  └──────────┘  └──────────────┘  └──────────────┘   │
│                        │                             │
│              Google Gemini 2.5 Flash                 │
│              Edge-TTS / gTTS                         │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI/NLP** | Google Gemini 2.5 Flash (voice + text) |
| **TTS** | Edge-TTS (neural), gTTS (fallback) |
| **Database** | SQLite3 |
| **Real-time** | WebSocket (audio streaming) |
| **Audio** | Web Audio API, MediaRecorder, VAD |

---

## 📁 Project Structure

```
carttalk/
├── backend/
│   ├── main.py           # FastAPI app, routes, WebSocket handler
│   ├── services.py       # Gemini AI service, TTS, NLP pipeline
│   ├── db.py             # SQLite schema, CRUD operations
│   ├── cartalk.db        # SQLite database (auto-generated)
│   ├── requirements.txt  # Python dependencies
│   ├── .env              # API keys (not committed)
│   ├── .env.example      # Environment template
│   └── static/images/    # Uploaded product images
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app with routing
│   │   ├── CallInterface.jsx   # Voice call UI + WebSocket
│   │   ├── ProductGrid.jsx     # Product catalog with live search
│   │   ├── AdminDashboard.jsx  # Merchant inventory + orders
│   │   ├── AdminLogin.jsx      # Merchant authentication
│   │   ├── OrderHistory.jsx    # Customer order history
│   │   └── *.css               # Component styles
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
- Google Gemini API Key ([Get one here](https://aistudio.google.com/apikey))

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run server
python main.py
```
Server runs at: `http://localhost:8000`

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Or run dev server
npm run dev
```
App runs at: `http://localhost:5173`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Phone-based customer login |
| `POST` | `/api/call/start` | Start a new voice call session |
| `WS` | `/api/call/{id}/stream` | Real-time audio WebSocket |
| `GET` | `/api/products` | List all products |
| `POST` | `/api/products` | Add new product |
| `PUT` | `/api/products/{id}` | Update product |
| `DELETE` | `/api/products/{id}` | Delete product |
| `GET` | `/api/orders` | List all orders (merchant) |
| `GET` | `/api/orders/user?phone=X` | Get user's orders |
| `PUT` | `/api/orders/{id}/status` | Update order status |
| `DELETE` | `/api/orders/{id}` | Delete order |
| `POST` | `/api/upload` | Upload product image |

---

## 🗄️ Database Schema

```sql
products     (id, name_en, name_ml, category, price, stock, image_url, safety_stock)
orders       (id, customer_phone, customer_name, customer_address, total, status, language, transcript, created_at)
order_items  (id, order_id, product_id, quantity, price)
users        (phone, name, address, created_at)
cart_items   (id, phone, product_id, quantity)
```

---

## 👥 Team

- **Fahim** — Full-stack Development & AI Integration
