# Legal Document Summarization

## Overview
An AI-driven web app simplifying Indian Supreme Court judgment analysis with summarization, question-answering, and multilingual translation. Built with ReactJS, Flask, and MongoDB Atlas, it serves lawyers, students, and non-lawyers, reducing case preparation time and enhancing accessibility.

## Problem Solved
- **Summarization**: Condenses 100-page judgments into 1–2 pages (~100s, ~80% accuracy).
- **Q&A**: Answers case-specific queries (e.g., "What’s the rationale?") in ~15s (~75% relevance).
- **Multi-Format**: Supports PDF, DOCX, TXT up to 16MB.
- **Accessibility**: Translates summaries (e.g., Hindi, ~90% accuracy) for India’s diverse users.
- **Inclusivity**: Optimized for low-bandwidth (2 Mbps) and low-end devices (320px).

Reduces judicial backlog and empowers non-experts.

## Case Studies

### Case Study 1: Lawyer Case Preparation
**Scenario**: A lawyer analyzes a 60-page judgment.  
**Solution**: The system summarizes in ~100s and answers statute queries in ~15s.  
**Impact**: Cuts prep time by ~80%.

### Case Study 2: Student Moot Court
**Scenario**: Student researches multiple cases.  
**Solution**: Uploads files, gets summaries, queries precedents, exports TXT.  
**Impact**: Speeds research by ~70%.

### Case Study 3: Rural Non-Lawyer
**Scenario**: Citizen seeks ruling clarity.  
**Solution**: Hindi-translated summary on a budget phone.  
**Impact**: Boosts legal literacy.

## Technology Stack
- **Frontend**: ReactJS (v18) – Responsive UI, drag-and-drop, low-bandwidth optimized.
- **Backend**: Flask (v2.3) – Lightweight APIs for file handling and AI integration.
- **AI/ML**: T5-small & RAG with FAISS (v1.7) – Summarization and Q&A.
- **Data Processing**: PyPDF2 (v3.0), python-docx – Text extraction.
- **Database**: MongoDB Atlas (v7.0) – Scalable storage.
- **Translation**: MyMemory, LibreTranslate APIs – Multilingual support.
- **Infrastructure**: Docker (v24.0), Vercel, Render, Fly.io – Scalable deployment.
- **Development**: VS Code (v1.85), Git (v2.43) – Collaboration.

## Why This Stack?
- **ReactJS**: Dynamic, mobile-friendly UI for rural users.
- **Flask**: Lightweight, cost-effective API development.
- **T5-small & RAG**: CPU-efficient, affordable AI processing.
- **FAISS**: Fast, lightweight vector search vs. Pinecone.
- **MongoDB Atlas**: Flexible for unstructured legal data.
- **Translation APIs**: Low-cost multilingual support.
- **Docker & Cloud**: Portable, scalable deployment.

## Approach to Edge Cases
- **Jargon**: T5-small with legal database, regex for ~80% term accuracy.
- **Large Files**: Dynamic chunking, parallel processing (~100s for 10,000 words).
- **Vague Queries**: RAG with FAISS, plans for multi-turn dialogue.
- **File Issues**: PyPDF2, python-docx with OCR for malformed files.
- **Translation Errors**: API fallback, caching for reliability.
- **Low Bandwidth**: Compressed UI for 2 Mbps connections.

## Tradeoffs Made
- **CPU vs. GPU**: Used CPUs (AWS t3.medium) for cost, ~100s vs. ~70s with GPUs.
- **External APIs vs. Local Model**: MyMemory, LibreTranslate for simplicity, ~5s latency.
- **T5-small vs. Larger Models**: Fits Fly.io’s 1GB RAM, ~5–10% accuracy trade-off.
- **Language Support**: Focused on key Indian languages, plans for more (e.g., Gujarati).
- **Feature Scope**: Focused on core features—document upload, AI summarization, RAG-based Q&A, multilingual translation, TXT export, user notes, and legal blog—to deliver a functional system within deadlines. Advanced features like citation extraction and document comparison were deferred for future releases to ensure robust core functionality. Planned enhancements include local translation, improved accuracy, and collaboration tools.
