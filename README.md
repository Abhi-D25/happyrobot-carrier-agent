# Inbound Carrier Sales Agent API

A FastAPI backend service for an AI-powered inbound carrier sales agent that automates load matching, carrier verification, and rate negotiation. Integrated with HappyRobot AI platform for conversational AI capabilities.

## Project Overview

This system provides a complete backend solution for managing inbound carrier calls, featuring:

- **Automated Carrier Verification** via FMCSA API integration
- **Intelligent Load Matching** with city/state-based search algorithms
- **Dynamic Rate Negotiation** with configurable policies
- **Real-time Analytics Dashboard** with comprehensive KPIs
- **HappyRobot AI Integration** for conversational flow management
- **Production-ready Architecture** with Docker and SQLite

## Features & Capabilities

### Core Functionality
- **MC Number Verification**: Real-time FMCSA carrier validation
- **Load Search & Matching**: Advanced filtering by equipment, origin, destination
- **Negotiation Engine**: Multi-round rate negotiation with acceptance policies
- **Call Tracking**: Complete conversation persistence and analytics
- **Dashboard Analytics**: Real-time KPIs and performance metrics

### HappyRobot Integration
- **Conversation Management**: State-based call flow handling
- **Web Call Triggers**: Seamless integration with HappyRobot platform
- **Data Extraction**: Automated conversation data capture
- **Sentiment Analysis**: Call outcome classification

### Production Features
- **API Authentication**: Secure API key-based access control
- **CORS Configuration**: Production-ready cross-origin settings
- **Database Persistence**: SQLite for assessment, PostgreSQL ready for production
- **Docker Support**: Complete containerization with docker-compose
- **Health Monitoring**: Comprehensive health checks and metrics

## Production Deployment Reproduction

### Prerequisites
- Docker & Docker Compose
- Fly.io CLI (for cloud deployment)
- Git

### Quick Start (Local Development)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd carrier-agent-production
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize and start:**
   ```bash
   python seed/seed_loads.py
   python run_server.py
   ```

4. **Verify local deployment:**
   ```bash
   curl http://localhost:8000/api/health
   open http://localhost:8000/dashboard
   ```

### Production Deployment to Fly.io

#### Step-by-Step Deployment

1. **Install Fly.io CLI:**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login to Fly.io:**
   ```bash
   fly auth login
   ```

3. **Clone and prepare repository:**
   ```bash
   git clone <repository-url>
   cd carrier-agent-production
   ```

4. **Initialize Fly.io app:**
   ```bash
   # Create new app with unique name
   fly launch --name carrier-agent-[your-name]
   
   # When prompted:
   # - Choose region closest to you
   # - Deploy now? Choose "No" (we need to set secrets first)
   ```

5. **Set environment variables:**
   ```bash
   fly secrets set API_KEY="assessment-api-key-2024"
   fly secrets set FMCSA_API_KEY="your-actual-fmcsa-api-key"
   fly secrets set ALLOWED_ORIGINS="https://your-app.fly.dev,https://app.happyrobot.ai"
   ```

6. **Deploy application:**
   ```bash
   fly deploy
   ```

7. **Initialize database:**
   ```bash
   fly ssh console
   python seed/seed_loads.py
   exit
   ```

8. **Verify deployment:**
   ```bash
   # Health check
   curl https://your-app.fly.dev/api/health
   
   # Test API endpoint
   curl -X POST https://your-app.fly.dev/api/happyrobot/start-call \
        -H "X-API-Key: assessment-api-key-2024" \
        -H "Content-Type: application/json" \
        -d '{"call_id": "test-call-123"}'
   ```

### Alternative Deployment Options

#### Docker Compose (Local/VPS)

1. **Set environment variables:**
   ```bash
   export API_KEY="your-secure-api-key"
   export FMCSA_API_KEY="your-fmcsa-api-key"
   export ALLOWED_ORIGINS="https://yourdomain.com,https://app.happyrobot.ai"
   ```

2. **Deploy with Docker Compose:**
   ```bash
   # Build and start services
   docker-compose up -d api
   
   # Initialize database
   docker-compose exec api python seed/seed_loads.py
   
   # Verify deployment
   curl http://localhost:8000/api/health
   ```

#### Using the Automated Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh

# The script will:
# - Set up environment variables
# - Build and deploy the application
# - Initialize the database
# - Verify deployment
```

## Environment Variables Reference

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `assessment-api-key-2024` |
| `FMCSA_API_KEY` | FMCSA API key for carrier verification | `your-fmcsa-api-key` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `https://yourdomain.com,https://app.happyrobot.ai` |

### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection string | `sqlite:///./carrier_agent.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

## API Documentation

### Base URLs
- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-app.fly.dev`

### Interactive Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

### Core Endpoints

#### Health & Status
- `GET /api/health` - Health check (no auth required)
- `GET /` - API information and status

#### HappyRobot Integration
- `POST /api/happyrobot/start-call` - Initialize new conversation
- `POST /api/happyrobot/verify-mc` - Verify carrier MC number
- `POST /api/happyrobot/search-loads` - Search and present loads
- `POST /api/happyrobot/negotiate` - Handle rate negotiation
- `POST /api/happyrobot/end-call` - Complete call and persist data
- `GET /api/happyrobot/call-status/{call_id}` - Get conversation status

#### Analytics & Metrics
- `GET /api/metrics/summary` - Get KPI metrics
- `GET /api/dashboard-data` - Dashboard data endpoint
- `GET /dashboard` - Analytics dashboard UI

### Authentication

All endpoints except `/api/health` and `/` require API key authentication:

```bash
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/metrics/summary
```

## HappyRobot Integration Guide

### Web Call Trigger Setup

Configure HappyRobot tools to call your deployed API:

```json
{
  "name": "carrier_verification",
  "url": "https://your-app.fly.dev/api/happyrobot/verify-mc",
  "method": "POST",
  "headers": {
    "X-API-Key": "assessment-api-key-2024",
    "Content-Type": "application/json"
  }
}
```

### Conversation Flow

```
1. Call Start → /api/happyrobot/start-call
2. MC Collection → /api/happyrobot/verify-mc
3. Load Search → /api/happyrobot/search-loads
4. Negotiation → /api/happyrobot/negotiate (multiple rounds)
5. Call End → /api/happyrobot/end-call
```

## Assessment Information

### For Technical Reviewers

#### **API Key for Testing**
```bash
API_KEY=assessment-api-key-2024
```

#### **Quick Assessment Setup**
```bash
# Clone and test locally
git clone <repository-url>
cd carrier-agent-production
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed/seed_loads.py
python run_server.py

# Test HappyRobot endpoints
curl -X POST http://localhost:8000/api/happyrobot/start-call \
     -H "X-API-Key: assessment-api-key-2024" \
     -H "Content-Type: application/json" \
     -d '{"call_id": "test-call-123"}'
```

#### **Live Demo Links**
- **Production API**: `https://carrier-agent-production.fly.dev`
- **Health Check**: `https://carrier-agent-production.fly.dev/api/health`
- **Dashboard**: `https://carrier-agent-production.fly.dev/dashboard`
- **API Docs**: `https://carrier-agent-production.fly.dev/docs`

#### **Key Features Demonstrated**
- ✅ **Web Call Trigger Integration**: Complete HappyRobot platform integration
- ✅ **Production-Ready Code**: Clean, documented, error-handled codebase
- ✅ **Real-time Analytics**: Comprehensive dashboard with live metrics
- ✅ **Docker Support**: Full containerization with docker-compose
- ✅ **Security**: HTTPS and API key authentication
- ✅ **Cloud Deployment**: Production deployment on Fly.io

## Troubleshooting Guide

### Common Issues

#### 1. Deployment Access Issues
```bash
# Check app status
fly status

# View logs
fly logs

# Check secrets
fly secrets list
```

#### 2. API Key Authentication Issues
```bash
# Test API key locally
curl -H "X-API-Key: assessment-api-key-2024" http://localhost:8000/api/health

# Verify environment variables
echo $API_KEY
```

#### 3. Database Issues
```bash
# Re-seed database
fly ssh console
python seed/seed_loads.py
exit
```

#### 4. Docker Issues
```bash
# Rebuild containers
docker-compose build --no-cache

# Check container logs
docker-compose logs api

# Restart services
docker-compose restart api
```

### Health Checks

```bash
# Basic connectivity
curl https://your-app.fly.dev/

# Health endpoint
curl https://your-app.fly.dev/api/health

# Dashboard access
curl https://your-app.fly.dev/dashboard
```

## Security Features

1. **HTTPS**: Automatic HTTPS with valid certificates via Fly.io
2. **API Key Authentication**: All endpoints protected except health check
3. **CORS Configuration**: Restricted to trusted origins
4. **Input Validation**: Pydantic schema validation
5. **Error Handling**: No sensitive information exposure

## Project Structure

```
carrier-agent-production/
├── api/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── deps.py                   # Dependencies (auth, db)
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── routers/                  # API route handlers
│   └── services/                 # Business logic services
├── templates/                    # HTML templates
│   └── dashboard.html            # Analytics dashboard
├── seed/                         # Database seeding
├── infra/                        # Infrastructure files
├── docker-compose.yml            # Docker configuration
├── Dockerfile                    # Container definition
├── deploy.sh                     # Automated deployment script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Performance Monitoring

Access real-time metrics and KPIs:
- **Dashboard**: `/dashboard`
- **Call Analytics**: Detailed conversation tracking
- **Performance Metrics**: Response times and success rates
- **Business Intelligence**: Revenue tracking and carrier behavior
