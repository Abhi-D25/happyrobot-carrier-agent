# Inbound Carrier Sales Agent API

A production-ready FastAPI backend service for an AI-powered inbound carrier sales agent that automates load matching, carrier verification, and rate negotiation. Integrated with HappyRobot AI platform for conversational AI capabilities.

## 🚀 Project Overview

This system provides a complete backend solution for managing inbound carrier calls, featuring:

- **Automated Carrier Verification** via FMCSA API integration
- **Intelligent Load Matching** with city/state-based search algorithms
- **Dynamic Rate Negotiation** with configurable policies
- **Real-time Analytics Dashboard** with comprehensive KPIs
- **HappyRobot AI Integration** for conversational flow management
- **Production-ready Architecture** with Docker and SQLite

## ✨ Features & Capabilities

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

## 🚀 Production Deployment Instructions

### Quick Production Deployment

**Use our automated deployment script:**

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The script will automatically:
- Set up environment variables
- Build and deploy the application
- Initialize the database
- Start all services
- Verify deployment

### Manual Production Deployment

#### Prerequisites
- Docker & Docker Compose
- Git

#### Step-by-Step Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd carrier-agent-production
   ```

2. **Set up environment variables**
   ```bash
   export API_KEY="your-secure-production-api-key"
   export FMCSA_API_KEY="your-fmcsa-api-key"
   export ALLOWED_ORIGINS="https://yourdomain.com,https://app.happyrobot.ai"
   ```

3. **Deploy with Docker Compose**
   ```bash
   # Deploy API service
   docker-compose up -d api
   
   # Or deploy with Nginx reverse proxy
   docker-compose --profile production up -d
   ```

4. **Initialize database and seed data**
   ```bash
   # Seed the database with sample loads
   docker-compose exec api python seed/seed_loads.py
   ```

5. **Verify deployment**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Check API documentation
   open http://localhost:8000/docs
   
   # View dashboard
   open http://localhost:8000/dashboard
   ```

### Production Environment Configuration

Create a `.env` file with the following variables:

```bash
# API Configuration
API_KEY=your-secure-api-key-here
PORT=8000
DEBUG=False

# Database Configuration (SQLite for assessment)
DATABASE_URL=sqlite:///./carrier_agent.db

# FMCSA API Configuration
FMCSA_API_KEY=your-fmcsa-api-key-here
FMCSA_BASE_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://app.happyrobot.ai

# Security Configuration
SECRET_KEY=your-secret-key-for-jwt-tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30

# HappyRobot Integration
HAPPYROBOT_API_URL=https://api.happyrobot.ai
HAPPYROBOT_WEBHOOK_SECRET=your-webhook-secret

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 🏃‍♂️ Local Development Setup

### Prerequisites
- Python 3.8+
- Docker & Docker Compose (optional)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd carrier-agent-production
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database and seed data**
   ```bash
   python seed/seed_loads.py
   ```

6. **Start the development server**
   ```bash
   python run_server.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

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

#### Load Management
- `POST /api/loads/search` - Search available loads
- `GET /api/loads/{load_id}` - Get specific load details

#### Carrier Verification
- `POST /api/fmcsa/verify` - Verify carrier with FMCSA

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

## 🤖 HappyRobot Integration Guide

### Overview
This API is designed to work seamlessly with HappyRobot's conversational AI platform. The integration enables automated carrier sales conversations with intelligent load matching and negotiation.

### Web Call Trigger Feature

The **Web Call Trigger** feature allows HappyRobot to initiate API calls during conversations:

1. **Call Initialization**: HappyRobot calls `/api/happyrobot/start-call` when a carrier calls
2. **MC Verification**: System verifies carrier MC number via FMCSA API
3. **Load Search**: Searches for matching loads based on carrier preferences
4. **Negotiation**: Handles rate negotiation with configurable policies
5. **Data Persistence**: Saves complete conversation data for analytics

### Integration Setup

1. **Configure HappyRobot Tools**
   ```json
   {
     "name": "carrier_verification",
     "url": "https://yourdomain.com/api/happyrobot/verify-mc",
     "method": "POST",
     "headers": {
       "X-API-Key": "your-api-key",
       "Content-Type": "application/json"
     }
   }
   ```

2. **Set up Web Call Triggers**
   - Configure HappyRobot to call API endpoints during conversation flow
   - Use conversation state management for context preservation
   - Implement error handling for API failures

3. **API Key Sharing for Reviewers**
   ```bash
   # For assessment/testing purposes
   API_KEY=assessment-api-key-2024
   ```

### Conversation Flow

```
1. Call Start → /api/happyrobot/start-call
2. MC Collection → /api/happyrobot/verify-mc
3. Load Search → /api/happyrobot/search-loads
4. Negotiation → /api/happyrobot/negotiate (multiple rounds)
5. Call End → /api/happyrobot/end-call
```

## 📋 Assessment-Specific Information

### For Technical Reviewers

This codebase has been prepared for technical assessment submission with the following key features:

#### **Web Call Trigger Implementation**
- Complete HappyRobot integration with web call trigger functionality
- State-based conversation management for seamless call flow
- Real-time API endpoints for carrier verification, load search, and negotiation

#### **API Key for Testing**
```bash
# Use this API key for assessment testing
API_KEY=assessment-api-key-2024
```

#### **Quick Assessment Setup**
1. **Clone and run locally:**
   ```bash
   git clone <repository-url>
   cd carrier-agent-production
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python seed/seed_loads.py
   python run_server.py
   ```

2. **Test HappyRobot endpoints:**
   ```bash
   # Start a call
   curl -X POST http://localhost:8000/api/happyrobot/start-call \
        -H "X-API-Key: assessment-api-key-2024" \
        -H "Content-Type: application/json" \
        -d '{"call_id": "test-call-123"}'
   
   # Verify MC number
   curl -X POST http://localhost:8000/api/happyrobot/verify-mc \
        -H "X-API-Key: assessment-api-key-2024" \
        -H "Content-Type: application/json" \
        -d '{"call_id": "test-call-123", "mc_number": "123456"}'
   ```

3. **View analytics dashboard:**
   - Open `http://localhost:8000/dashboard` in browser
   - Real-time KPIs and call analytics

#### **Key Assessment Features Demonstrated**
- ✅ **Web Call Trigger Integration**: Complete HappyRobot platform integration
- ✅ **Production-Ready Code**: Clean, documented, error-handled codebase
- ✅ **Real-time Analytics**: Comprehensive dashboard with live metrics
- ✅ **API Documentation**: Interactive Swagger UI at `/docs`
- ✅ **Docker Support**: Full containerization with docker-compose
- ✅ **Database Integration**: SQLite with PostgreSQL production support
- ✅ **Security**: API key authentication and CORS configuration

#### **Deployment Verification Steps**
1. **Health Check**: `curl http://localhost:8000/api/health`
2. **API Documentation**: Visit `http://localhost:8000/docs`
3. **Dashboard**: Visit `http://localhost:8000/dashboard`
4. **HappyRobot Integration**: Test endpoints with provided API key

#### **Business Logic Highlights**
- **Intelligent Load Matching**: City/state-based search with fallback options
- **Dynamic Negotiation**: Multi-round rate negotiation with configurable policies
- **Carrier Verification**: Real-time FMCSA API integration
- **Conversation State Management**: Persistent conversation tracking
- **Analytics & Reporting**: Comprehensive KPI tracking and business intelligence

## 🔧 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_KEY` | API authentication key | - | Yes |
| `PORT` | Server port | 8000 | No |
| `DEBUG` | Debug mode | False | No |
| `DATABASE_URL` | Database connection string | sqlite:///./carrier_agent.db | No |
| `FMCSA_API_KEY` | FMCSA API key for carrier verification | - | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | - | Yes |
| `LOG_LEVEL` | Logging level | INFO | No |

## 🐛 Troubleshooting Guide

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database connectivity
python -c "from api.db import SessionLocal; print('DB OK' if SessionLocal() else 'DB Error')"

# Verify environment variables
echo $DATABASE_URL
```

#### 2. API Key Authentication Issues
```bash
# Test API key
curl -H "X-API-Key: your-key" http://localhost:8000/api/health

# Check API key in environment
echo $API_KEY
```

#### 3. FMCSA API Issues
```bash
# Test FMCSA connectivity
curl -H "Authorization: Bearer $FMCSA_API_KEY" \
     "https://mobile.fmcsa.dot.gov/qc/services/carriers/name/123456"
```

#### 4. Docker Deployment Issues
```bash
# Check container logs
docker-compose logs api

# Restart services
docker-compose restart api

# Rebuild containers
docker-compose build --no-cache
```

#### 5. CORS Issues
- Verify `ALLOWED_ORIGINS` includes your frontend domain
- Check browser developer tools for CORS errors
- Ensure HTTPS is used in production

### Logs and Monitoring

#### Application Logs
```bash
# Docker logs
docker-compose logs -f api

# System logs (if using systemd)
journalctl -u carrier-agent -f
```

#### Health Checks
```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed status
curl http://localhost:8000/
```

#### Database Health
```bash
# Check database connection
python -c "from api.db import SessionLocal; print('DB OK' if SessionLocal() else 'DB Error')"
```

### Performance Optimization

1. **Database Indexing**: Ensure proper indexes on frequently queried columns
2. **Connection Pooling**: Configure database connection pooling
3. **Load Balancing**: Use Nginx for load balancing in production

## 📁 Project Structure

```
carrier-agent-production/
├── api/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── deps.py                   # Dependencies (auth, db)
│   ├── db.py                     # Database configuration
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── routers/                  # API route handlers
│   │   ├── health.py
│   │   ├── loads.py
│   │   ├── fmcsa.py
│   │   ├── negotiation.py
│   │   ├── calls.py
│   │   ├── metrics.py
│   │   ├── happyrobot.py         # HappyRobot integration
│   │   └── dashboard.py          # Dashboard endpoints
│   └── services/                 # Business logic services
│       ├── conversation_manager.py
│       ├── call_persistence.py
│       ├── fmcsa_client.py
│       ├── loads_search.py
│       ├── metrics_service.py
│       └── negotiation_policy.py
├── templates/                    # HTML templates
│   └── dashboard.html            # Analytics dashboard
├── seed/                         # Database seeding
│   ├── loads_seed.json
│   └── seed_loads.py
├── infra/                        # Infrastructure files
│   ├── nginx.conf
│   └── init-db.sql
├── docker-compose.yml            # Docker configuration
├── Dockerfile                    # Container definition
├── deploy.sh                     # Production deployment script
├── requirements.txt              # Python dependencies
├── run_server.py                 # Development server
└── README.md                     # This file
```

## 🔒 Security Considerations

1. **API Key Management**: Use strong, unique API keys in production
2. **HTTPS**: Always use HTTPS in production environments
3. **Database Security**: Use strong passwords and restrict database access
4. **CORS Configuration**: Limit allowed origins to trusted domains
5. **Input Validation**: All inputs are validated using Pydantic schemas
6. **Error Handling**: Sensitive information is not exposed in error messages

## 📈 Monitoring and Analytics

The system includes comprehensive monitoring capabilities:

- **Real-time Dashboard**: Live KPIs and performance metrics
- **Call Analytics**: Detailed conversation tracking and outcomes
- **Performance Metrics**: Response times, success rates, error rates
- **Business Intelligence**: Revenue tracking, carrier behavior analysis

Access the dashboard at `/dashboard` for real-time insights.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

---

**For technical support or questions about this assessment, please contact the development team.**