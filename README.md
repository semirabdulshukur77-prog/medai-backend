# 🏥 MedAI Backend - Multi-Agent Medical Consultation API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

MedAI Backend is a FastAPI-based REST API that powers the intelligent medical consultation system. It features a multi-agent AI architecture that provides medical analysis, diagnosis, recommendations, translation, and voice processing.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- GROQ API Key (get from [console.groq.com](https://console.groq.com/keys))

### Installation
```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ API key

# Run the server
python run.py