# Happy Robot Inbound Carrier Sales Agent

An AI-powered inbound carrier sales agent designed to automate load matching, carrier verification, and rate negotiation for freight brokerages. This project integrates with the HappyRobot AI platform for conversational capabilities and uses a FastAPI backend for core logic.

## ✨ Key Features

*   **Automated MC Verification:** Real-time validation of carrier MC numbers via FMCSA API.
*   **Intelligent Load Matching:** Efficiently finds and presents relevant loads, intelligently mapping requests to nearest major hubs.
*   **Dynamic Rate Negotiation:** Engages in multi-round price negotiations to secure optimal rates.
*   **Real-time Analytics Dashboard:** Provides comprehensive KPIs and insights into agent performance and call outcomes.
*   **HappyRobot AI Integration:** Seamless conversational flow management and data extraction.

## 🚀 Quick Start (Local Development)

To get the project running locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Abhi-D25/happyrobot-carrier-agent
    cd happyrobot-carrier-agent
    ```
2.  **Setup Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env # Configure your environment variables here
    ```
3.  **Initialize Database & Run:**
    ```bash
    python seed/seed_loads.py
    python run_server.py
    ```
    Access the API at `http://localhost:8000` and the dashboard at `http://localhost:8000/dashboard`.

## 🌐 Production Deployment

The application is deployed on Fly.io.

*   **Production API Endpoint:** https://carrier-agent-production.fly.dev
*   **Analytics Dashboard:** https://carrier-agent-production.fly.dev/dashboard

Continuous deployment is managed via GitHub Actions, which automatically deploys changes from the `main` branch to Fly.io.

## 📚 API Documentation

Detailed API documentation is available via Swagger UI:

*   **Swagger UI:** https://carrier-agent-production.fly.dev/docs

This project demonstrates a robust, customer-centric solution for automating inbound carrier sales, built with scalability and efficiency in mind.