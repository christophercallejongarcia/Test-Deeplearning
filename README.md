# Course Materials Assistant 🎓

A comprehensive RAG (Retrieval-Augmented Generation) chatbot for course materials featuring advanced theming, testing infrastructure, and quality tools.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange.svg)](https://www.anthropic.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tested with pytest](https://img.shields.io/badge/tested%20with-pytest-blue.svg)](https://docs.pytest.org/)

## ✨ Features

### 🤖 AI-Powered RAG System
- **Semantic Search**: ChromaDB-powered vector search
- **Context-Aware Responses**: Session-based conversation memory
- **Tool-Based Querying**: Intelligent search decision making
- **Course Material Support**: PDF, DOCX, and TXT document processing

### 🎨 Advanced Theming System
- **Multiple Themes**: Light, Dark, Auto, and High Contrast modes
- **System Integration**: Respects OS theme preferences
- **Accessibility First**: WCAG 2.1 compliant with screen reader support
- **Responsive Design**: Mobile-first approach with touch-friendly controls

### 🧪 Comprehensive Testing
- **Unit Tests**: Backend component testing with 90%+ coverage
- **Integration Tests**: API endpoint validation
- **E2E Tests**: Playwright-powered browser testing
- **Visual Regression**: Automated UI consistency checks

### 🔧 Quality Assurance
- **Code Formatting**: Black + isort integration
- **Linting**: flake8 with custom rules
- **Type Safety**: mypy static analysis
- **Pre-commit Hooks**: Automated quality gates
- **Security Scanning**: Vulnerability detection

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **UV package manager** ([installation guide](https://docs.astral.sh/uv/))
- **Anthropic API key**

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd starting-ragchatbot-codebase
make setup
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Start the application**:
```bash
make run
```

Visit http://localhost:8000 to access the application! 🎉

