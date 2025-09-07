# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- Install dependencies: `uv sync`
- Activate virtual environment: `uv shell` (optional, commands run via `uv run`)

### Running the Application
- **Quick start**: `chmod +x run.sh && ./run.sh`
- **Manual start**: `cd backend && uv run uvicorn app:app --reload --port 8000`
- **Access points**:
  - Web interface: http://localhost:8000
  - API docs: http://localhost:8000/docs

### Environment Configuration
- Copy `.env` file with `ANTHROPIC_API_KEY=your_key_here`
- Uses Python 3.13+ and requires uv package manager

## Architecture Overview

This is a full-stack RAG (Retrieval-Augmented Generation) system for course material Q&A with the following key components:

### Backend Architecture (`/backend/`)

**Core RAG Pipeline:**
- `rag_system.py` - Main orchestrator that coordinates all components
- `vector_store.py` - ChromaDB integration for semantic search and persistence
- `ai_generator.py` - Anthropic Claude API integration with tool-calling capabilities
- `document_processor.py` - Handles PDF/DOCX/TXT parsing and chunking
- `session_manager.py` - Manages conversation history across sessions

**Search & Tools:**
- `search_tools.py` - Implements tool-based search with CourseSearchTool
- Uses function calling pattern where AI decides when to search vs. use knowledge

**Data Models:**
- `models.py` - Course, Lesson, CourseChunk data structures
- `config.py` - Configuration management

**FastAPI Application:**
- `app.py` - FastAPI server with CORS, static file serving, startup document loading
- Serves both API endpoints (`/api/query`, `/api/courses`) and frontend static files

### Frontend (`/frontend/`)
- Vanilla HTML/CSS/JavaScript single-page application
- `index.html` - Main interface with chat UI
- `script.js` - Handles API communication and chat interactions
- `style.css` - Complete styling including responsive design

### Key Design Patterns

**Tool-Based RAG**: The system uses Anthropic's function calling to let Claude decide when to search course materials vs. answer from general knowledge. This prevents unnecessary searches for general questions.

**Session Management**: Conversation context is maintained across queries using session IDs, allowing for follow-up questions.

**Document Processing Pipeline**: 
1. Documents loaded from `/docs/` folder on startup
2. Processed into semantic chunks with metadata
3. Stored in ChromaDB with both content and course metadata
4. Retrievable via semantic similarity search

**Dual Collection Strategy**: 
- Course metadata collection for high-level course information
- Content chunks collection for detailed lesson content
- Both collections used by search tool for comprehensive results

### Database & Storage
- **ChromaDB**: Vector database stored in `backend/chroma_db/`
- **Embeddings**: sentence-transformers model for semantic search
- **Persistence**: ChromaDB handles automatic persistence of vector data

### Document Support
- Supports PDF, DOCX, and TXT files in `/docs/` folder
- Automatic processing on startup with duplicate detection
- Configurable chunking (default: 1000 chars, 200 overlap)

## Development Notes

- The system automatically loads documents from `/docs/` on startup
- Uses uv for dependency management (replaces pip/pipenv)
- Frontend and backend are served from single FastAPI instance
- No build step required - pure Python backend, vanilla JS frontend
- ChromaDB data persists between runs in `backend/chroma_db/`