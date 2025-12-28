# CartTalk - Voice Grocery Assistant

## Setup & Run

### Backend
1. Navigate to `backend` directory:
   ```bash
   cd backend
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```
3. Create `.env` file from example and add your Gemini API key:
   ```bash
   copy .env.example .env
   # Edit .env
   ```
4. Run the server:
   ```bash
   python main.py
   ```
   Server running at http://localhost:8000

### Frontend
1. Navigate to `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   App running at http://localhost:5173 (or similar)

## Features
- Real-time voice ordering (English + Malayalam)
- Inventory management
- Order tracking

## Tech Stack
- Backend: Python 3.11, FastAPI, SQLite, Google Gemini Live API
- Frontend: React (Vite)
