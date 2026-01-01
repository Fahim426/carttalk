# CartTalk - Voice-Enabled Grocery Assistant
## Comprehensive Technical Documentation

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Technology Stack](#architecture--technology-stack)
3. [System Components](#system-components)
4. [Key Features & Implementation](#key-features--implementation)
5. [Technical Decisions & Rationale](#technical-decisions--rationale)
6. [Security Considerations](#security-considerations)
7. [Scalability & Performance](#scalability--performance)
8. [Deployment & Configuration](#deployment--configuration)
9. [Future Enhancements](#future-enhancements)
10. [Project Strengths & Areas for Improvement](#project-strengths--areas-for-improvement)

---

## Project Overview

CartTalk is an innovative voice-enabled grocery shopping assistant that allows customers to place orders through natural conversation in both English and Malayalam. The system uses AI to process voice input, manage inventory, and handle order processing through an intelligent conversational interface.

### Core Functionality
- Real-time voice processing with AI-powered responses
- Bilingual support (English and Malayalam)
- Inventory management with real-time stock tracking
- Order processing and status management
- Administrative dashboard for inventory and order management

---

## Architecture & Technology Stack

### Backend Technologies
- **Python 3.11**: Primary backend language chosen for its rich ecosystem of AI/ML libraries and excellent support for web frameworks
- **FastAPI**: High-performance web framework that provides:
  - Automatic API documentation
  - Type validation
  - WebSocket support for real-time communication
  - Asynchronous request handling
- **SQLite**: Lightweight, file-based database that requires no separate server process, ideal for development and small-scale deployments
- **Google Gemini 2.0 Flash API**: AI model for processing audio and generating intelligent responses
- **gTTS (Google Text-to-Speech)**: Converts AI responses to audio for natural voice interaction
- **WebSockets**: Enables real-time bidirectional communication for low-latency audio streaming
- **Python-dotenv**: Environment variable management for secure API key storage

### Frontend Technologies
- **React 18**: Component-based UI framework for building responsive user interfaces
- **Vite**: Fast build tool and development server
- **Web Audio API**: Handles audio processing and playback
- **MediaRecorder API**: Captures microphone input for voice commands
- **WebSocket API**: Real-time communication with backend for audio streaming

---

## System Components

### Backend Architecture
The backend follows a service-oriented architecture with clear separation of concerns:

- **main.py**: Entry point and API router handling WebSocket connections, REST endpoints, and CORS configuration
- **services.py**: Core business logic including:
  - GeminiService: Handles AI processing, conversation history management, and text-to-speech conversion
  - InventoryService: Manages product context for AI
  - OrderService: Handles order processing
- **db.py**: Database operations including schema management, data seeding, and migrations

### Frontend Architecture
- **App.jsx**: Main application component with routing between home, admin, and call interface views
- **CallInterface.jsx**: Core voice interaction component with:
  - Voice Activity Detection (VAD)
  - Real-time audio streaming
  - WebSocket communication
  - Conversation display
- **AdminDashboard.jsx**: Administrative interface for managing orders and inventory
- **ProductGrid.jsx**: Displays available products from the backend

---

## Key Features & Implementation Details

### Voice Processing Pipeline
1. **Audio Capture**: Frontend uses MediaRecorder API to capture user speech
2. **Voice Activity Detection**: Real-time detection of speech vs. silence to optimize transmission
3. **WebSocket Streaming**: Audio chunks are sent immediately over WebSocket connection
4. **AI Processing**: Gemini processes audio input with full inventory context
5. **Response Generation**: AI generates text response in user's language
6. **Text-to-Speech**: gTTS converts response to audio
7. **Audio Playback**: Audio is streamed back and played on frontend

### Language Detection & Support
- Automatic detection of English/Malayalam input
- AI responds in the same language as input
- Product database includes both English and Malayalam names
- gTTS configured for appropriate language output

### Conversation Context Management
- Conversation history maintained per call ID
- Context includes full inventory information for accurate responses
- History is managed to prevent excessive memory usage (last 20 turns)
- Transcript extraction for maintaining coherent conversation flow

### Inventory Management
- Real-time inventory tracking with stock deduction on order placement
- Product information includes ID, names (English/Malayalam), category, price, stock, and image URL
- Automatic stock updates when orders are placed
- Admin interface for adding/updating products

### Order Processing
- Order creation with customer details, cart items, and transcript
- Order status tracking (completed, delivered)
- Order history maintained in database
- Integration with inventory for stock management

---

## Technical Decisions & Rationale

### Choice of Gemini 2.0 Flash
- **Rationale**: Chosen for its experimental multimodal capabilities allowing direct audio processing
- **Benefits**: Direct audio-to-text processing without intermediate conversion
- **Trade-offs**: Experimental model may have stability concerns for production

### WebSocket Architecture
- **Rationale**: Traditional HTTP would introduce unacceptable latency for real-time audio streaming
- **Benefits**: Persistent connection reduces overhead, enables true real-time communication
- **Trade-offs**: More complex connection management, potential scaling challenges

### SQLite Database
- **Rationale**: Simple, file-based solution requiring no separate database server
- **Benefits**: Easy deployment, zero configuration, suitable for prototype
- **Trade-offs**: Limited concurrent access, potential bottlenecks in production

### Voice Activity Detection
- **Rationale**: Prevents transmission of silence, reducing bandwidth and processing overhead
- **Implementation**: Uses Web Audio API to analyze volume levels and detect speech
- **Benefits**: Optimized data transmission, improved user experience

### Client-Side Audio Processing
- **Rationale**: Browser-native APIs provide efficient audio capture and playback
- **Benefits**: No additional client software required, good browser support
- **Trade-offs**: Browser-dependent features may vary across platforms

---

## Security Considerations

- API keys stored in environment variables (.env file)
- CORS configured to allow necessary origins
- Input validation through FastAPI type hints
- No authentication required for basic functionality (though admin features exist)

---

## Scalability & Performance

### Current Limitations
- SQLite database may not handle high concurrency
- Conversation history stored in memory (not persistent across restarts)
- No load balancing or horizontal scaling

### Potential Improvements
- Migration to PostgreSQL for production deployments
- Redis for conversation state management
- Microphone access optimization for mobile devices
- Caching for frequently accessed data

---

## Deployment & Configuration

### Backend Setup
- Python virtual environment with FastAPI dependencies
- Gemini API key configuration via .env file
- Automatic database initialization and seeding

### Frontend Setup
- Vite-based development server
- React component architecture
- WebSocket connection management

---

## Future Enhancements

Based on the roadmap mentioned in the documentation:

1. **Lower Latency**: Implement streaming TTS for faster response times
2. **Robust Cart System**: Proper cart management with structured data exchange
3. **Voice Animation**: Visual audio feedback for better user experience
4. **Production Deployment**: Server-grade database and hosting solutions
5. **Enhanced VAD**: More sophisticated voice detection algorithms
6. **Multi-language Support**: Extend beyond English/Malayalam

---

## Project Strengths & Areas for Improvement

### Project Strengths
- Innovative approach to voice-based shopping
- Bilingual support for regional language users
- Real-time processing with low latency
- Clean separation of concerns in architecture
- Comprehensive admin interface
- Well-documented codebase with clear explanations

### Potential Areas for Improvement
- Session persistence across server restarts
- Enhanced error handling and user feedback
- Mobile optimization for touch interfaces
- Advanced analytics for conversation insights
- Integration with payment systems
- Improved accessibility features

---

This project demonstrates a sophisticated integration of modern web technologies with AI capabilities to create an innovative voice-based shopping experience that addresses real-world needs for multilingual commerce applications.