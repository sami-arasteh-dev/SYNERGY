# Smart Synergy Network (SYNERGY)

A local-first, AI-powered platform for mapping and analyzing B2B commercial synergies. Generates directed, weighted relationship graphs, strategic recommendations, and campaign sequences based on organizational data and business context.

## 📋 Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [File Structure](#file-structure)
- [Technical Notes](#technical-notes)
- [Development & Extensibility](#development--extensibility)

## ✨ Features
- **AI-Driven Network Analysis:** Generates directed, weighted graphs representing commercial relationships, referral flows, and cross-selling potential.
- **Multi-Format Data Import:** Supports CSV, JSON, and Excel (`.xlsx`/`.xls`) files via `pandas` and `csv`.
- **Interactive Visualization:** Renders graphs using Cytoscape.js with dynamic edge weighting and node role classification.
- **Structured Recommendations:** Outputs actionable partnership cards with commercial logic, implementation steps, risk assessment, and confidence scores.
- **Campaign Sequencing:** Suggests timed, multi-step commercial campaigns with conditional triggers.
- **Configurable LLM Backend:** Fully customizable API base URL, model, temperature, max tokens, and custom headers. Compatible with OpenAI and OpenAI-compatible providers.
- **Persistent Local Storage:** All data, analyses, and saved cards are stored in a local SQLite database (`synergy.db`).
- **JSON Export:** Download any analysis as a structured JSON file.

## 🏗️ Architecture
The application follows a monolithic client-server architecture:
- **Backend:** Flask-based REST API handling data persistence, file parsing, LLM orchestration, and response normalization.
- **Database:** SQLite (`synergy.db`) with tables for `settings`, `organizations`, `analyses`, and `saved_cards`.
- **Frontend:** Static HTML/CSS/JS served by Flask. UI is Persian/RTL by default but easily localizable. Graph rendering uses Cytoscape.js.
- **AI Integration:** External LLM calls via the `openai` Python SDK. Prompts are constructed dynamically from organizational data and user context.

## 📦 Prerequisites
- Python 3.8+
- `pip` package manager
- An OpenAI-compatible API key (or compatible provider)

## 🛠️ Installation
```bash
# Clone or extract the project
cd synergy-network

# Install dependencies
pip install flask openai pandas werkzeug

# Run the application
python app.py
```
The server will start at `http://127.0.0.1:8500`.

## ⚙️ Configuration
Access the **Settings** tab in the UI or modify the `settings` table directly.
- **API Base URL:** Default `https://api.gapgpt.app/v1`
- **API Key:** Stored in SQLite. Masked in UI for security.
- **Model:** Default `gpt-4o`
- **Temperature:** Default `0.2`
- **Max Tokens:** Default `6000`
- **Extra Headers:** JSON string for custom request headers.

> ⚠️ **Security Note:** The API key is stored in plaintext in SQLite. For production deployments, implement environment variables, secret managers, or database encryption.

## 🚀 Usage
1. **Add Organizations:** Navigate to the *Organizations & Data* tab. Manually add entities or import files.
2. **Select Axis & Context:** In the *Network Analysis* tab, choose the primary organization, select participating entities, and provide business context.
3. **Run Analysis:** Click the generate button. The backend constructs a prompt, calls the LLM, normalizes the response, and saves the result.
4. **Review & Export:** View the interactive graph, recommendation cards, and campaign sequences. Export the full analysis as JSON.

## 🔌 API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Serves the frontend UI. |
| `GET`  | `/api/settings` | Retrieve LLM configuration. |
| `POST` | `/api/settings` | Update LLM configuration. |
| `GET`  | `/api/organizations` | List all organizations. |
| `POST` | `/api/organizations` | Add a new organization. |
| `PUT`  | `/api/organizations/<id>` | Update an organization. |
| `DELETE` | `/api/organizations/<id>` | Delete an organization. |
| `POST` | `/api/import` | Upload & parse CSV/JSON/XLSX files. |
| `POST` | `/api/analyze` | Trigger network analysis. Returns JSON graph & recommendations. |
| `GET`  | `/api/analyses` | List saved analyses. |
| `GET`  | `/api/analyses/<id>` | Retrieve a specific analysis. |
| `POST` | `/api/cards` | Save a recommendation card. |
| `GET`  | `/api/cards` | List saved cards. |
| `GET`  | `/api/export/<id>` | Download analysis as JSON. |
| `GET`  | `/api/health` | Health check endpoint. |

## 📁 File Structure
```
.
├── app.py              # Flask backend, API routes, LLM integration, DB logic
├── index.html          # Frontend UI (Persian/RTL, Cytoscape.js integration)
├── synergy.db          # SQLite database (auto-created on first run)
├── uploads/            # Directory for imported files
└── static/             # CSS & JS assets (style.css, app.js)
```

## 🔍 Technical Notes
- **Response Normalization:** The `normalize_result()` function ensures LLM outputs conform to the expected schema, guarantees valid nodes/edges for selected organizations, caps edge weights to `0–100`, and fills missing recommendations with structured placeholders.
- **JSON Parsing:** Raw LLM responses are cleaned of markdown code blocks and extracted using bracket matching before parsing.
- **File Upload Limit:** Configured to `25 MB` via `MAX_CONTENT_LENGTH`.
- **Database Schema:** Auto-initialized on startup. Tables: `settings`, `organizations`, `analyses`, `saved_cards`.
- **Unused Imports:** `secrets` is imported but not utilized in the current implementation.

## 🧑‍💻 Development & Extensibility
- **Localization:** The frontend is hardcoded in Persian. Extract strings to a translation layer for multi-language support.
- **Authentication:** Currently unauthenticated. Add JWT/session middleware for production.
- **Containerization:** Wrap `app.py` in a `Dockerfile` with a Python base image for reproducible deployments.
- **LLM Prompt Engineering:** Modify `SYSTEM_PROMPT` in `app.py` to adjust analytical focus, output structure, or domain specificity.
- **Database Migration:** Use `alembic` or `sqlite-utils` if schema evolution is required.

## 📄 License
This project is provided as-is for local and internal use. No explicit license is included. Modify and distribute according to your organizational policies.

---
*Built for structured B2B commercial planning. Data remains local; intelligence is configurable.*
