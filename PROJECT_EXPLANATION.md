# CartTalk - Project Overview & Walkthrough

## 📖 Project Concept
**CartTalk** is an intelligent, bilingual voice assistant designed for grocery ordering. It simulates a natural conversation with a shopkeeper, allowing customers to check stock, ask for prices, and place orders using their voice in either **English** or **Malayalam**.

## 🛠️ Technology Stack

### Backend (The Brain)
- **Language**: Python 3.11
- **Framework**: **FastAPI** (High-performance web API framework)
- **AI Model**: **Google Gemini 2.0 Flash** (via `google-genai` SDK)
  - We use the *experimental* Flash model (`gemini-2.0-flash-exp`) for its multimodal capabilities (processing audio directly).
- **Database**: **SQLite** (Simple, file-based database)
  - Stores Products, Orders, and Order Items.
- **Audio Processing**: 
  - **gTTS (Google Text-to-Speech)**: Converts the AI's text response into speech (MP3).
  - **RegeX**: Used to clean the text (removing `**` bold markers) before speaking.
- **WebSocket**: Enables real-time, bidirectional communication between the browser and server.

### Frontend (The Face)
- **Framework**: **React** (powered by Vite for speed).
- **Styling**: Vanilla CSS (Custom modern design).
- **Audio**: 
  - **MediaRecorder API**: Captures user microphone input.
  - **Web Audio API**: Plays back the MP3 response from the server.
  - **WebSocket API**: Streams audio data to the backend.

---

## 🔄 How It Works (The Logical Flow)

1.  **Audio Capture**: The user clicks "Start Speaking". The React frontend records audio chunks.
2.  **Streaming**: These audio chunks are sent instantly over a WebSocket connection to the FastAPI backend.
3.  **AI Processing (`services.py`)**:
    - The backend accumulates the audio and sends it to **Gemini**.
    - We inject a **System Prompt** that includes the entire Database Inventory (Prices/Stock).
    - We maintain a **Conversation History** list. We manually extract the User's "Transcript" from Gemini's reasoning and append it to history so the AI remembers context (e.g., "I want 2kg of *that*").
4.  **Response Generation**:
    - Gemini returns a text response (e.g., "Okay, added 2kg rice. Anything else?").
    - We "clean" this text (remove markdown symbols).
    - We detect the language (English or Malayalam characters).
    - **gTTS** converts the clean text into an Audio Byte Stream.
5.  **Playback**: The audio bytes are sent back down the WebSocket. The Frontend receives them and plays the audio blob.

---

## ⚡ Recent Key Implementations & Fixes

During development, we solved several critical challenges:

1.  **Context Memory**: Initial versions "forgot" previous requests. We implemented a custom History tracking system that feeds previous turns back into Gemini.
2.  **Barge-In (Interruption)**: We added logic in the Frontend to `pause()` and clear the current audio player immediately when the user starts speaking again. This makes the conversation feel natural.
3.  **Language Switching**: We enforced strict prompts ("If input is Malayalam, output Malayalam") and added code checks to set the correct accent/language for the Text-to-Speech engine.
4.  **Audio Cleaning**: We stripped markdown characters (like `**Rice**`) so the voice doesn't say "Asterisk Asterisk Rice".

---

## 🚀 Roadmap for Improvements

If you want to take this project further, here is what to explain/implement:

### 1. Lower Latency (Speed)
*   **Current**: We wait for the full text response, generate full audio, then send.
*   **Improvement**: Use **Streaming TTS**. As soon as Gemini generates the first sentence, generate audio for *just that sentence* and stream it. Or, use Gemini 2.0's native "Audio Output" modality when it becomes stable to avoid the gTTS step entirely.

### 2. Robust Cart System
*   **Current**: The cart is essentially "remembered" by the AI in the conversation context.
*   **Improvement**: Implement the `/api/cart/add` endpoint properly. When the AI decides to add an item, it should output a structured JSON command (Function Calling) to actually update a `cart` table in the database.

### 3. Voice Animation
*   **Current**: Simple "AI is speaking..." text.
*   **Improvement**: Add a visualizer (waveforms) that reacts to the audio amplitude.

### 4. Deployment
*   **Current**: Localhost.
*   **Improvement**: Deploy Backend to **Render** or **Google Cloud Run**. Deploy Frontend to **Vercel**. Using SQLite in serverless is tricky; migrating to **PostgreSQL** (e.g., Supabase) would be better for production.

---

## ❓ FAQ for Explanation

**Q: Why use WebSocket instead of HTTP?**
A: HTTP has overhead for every request. WebSocket keeps a single open pipe, which is much faster for streaming audio data back and forth.

**Q: How does it know the inventory?**
A: We fetch the product list from SQLite and "inject" it into the AI's instructions as text. This is called **RAG (Retrieval-Augmented Generation)** in its simplest form.

**Q: Can it handle out-of-stock items?**
A: Yes, because the inventory context includes `Stock: 50`. The System Prompt commands the AI to check this number before accepting an order.
