#!/bin/bash

# Production Deployment Script for Carrier Agent API
# This script automates the deployment process for the FastAPI application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to set up environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        
        # Create .env file with default values
        cat > .env << EOF
# API Configuration
API_KEY=assessment-api-key-2024
PORT=8000
DEBUG=False

# Database Configuration
DATABASE_URL=sqlite:///./carrier_agent.db

# FMCSA API Configuration
FMCSA_API_KEY=your-fmcsa-api-key-here
FMCSA_BASE_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://app.happyrobot.ai

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
        
        print_warning "Please edit .env file with your actual configuration values."
        print_warning "Especially update FMCSA_API_KEY with your real API key."
    fi
    
    # Load environment variables
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
        print_success "Environment variables loaded from .env file"
    fi
    
    # Set default values if not provided
    export API_KEY=${API_KEY:-"assessment-api-key-2024"}
    export FMCSA_API_KEY=${FMCSA_API_KEY:-"your-fmcsa-api-key-here"}
    export ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-"http://localhost:3000,https://app.happyrobot.ai"}
    export PORT=${PORT:-8000}
    export DEBUG=${DEBUG:-"False"}
}

# Function to build and deploy
deploy_application() {
    print_status "Building and deploying application..."
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose down --remove-orphans || true
    
    # Build the application
    print_status "Building Docker image..."
    docker-compose build --no-cache
    
    # Start the application
    print_status "Starting application services..."
    docker-compose up -d api
    
    # Wait for the application to start
    print_status "Waiting for application to start..."
    sleep 10
    
    # Check if the application is running
    if docker-compose ps api | grep -q "Up"; then
        print_success "Application started successfully"
    else
        print_error "Failed to start application"
        docker-compose logs api
        exit 1
    fi
}

# Function to initialize database
initialize_database() {
    print_status "Initializing database..."
    
    # Wait a bit more for the database to be ready
    sleep 5
    
    # Run database seeding
    print_status "Seeding database with sample data..."
    if docker-compose exec -T api python seed/seed_loads.py; then
        print_success "Database seeded successfully"
    else
        print_warning "Database seeding failed, but continuing..."
    fi
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check health endpoint
    print_status "Checking health endpoint..."
    if curl -f -s http://localhost:${PORT}/api/health >/dev/null; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi
    
    # Check API documentation
    print_status "Checking API documentation..."
    if curl -f -s http://localhost:${PORT}/docs >/dev/null; then
        print_success "API documentation accessible"
    else
        print_warning "API documentation not accessible"
    fi
    
    # Check dashboard
    print_status "Checking dashboard..."
    if curl -f -s http://localhost:${PORT}/dashboard >/dev/null; then
        print_success "Dashboard accessible"
    else
        print_warning "Dashboard not accessible"
    fi
}

# Function to show deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo ""
    echo "🚀 Application Information:"
    echo "   • API URL: http://localhost:${PORT}"
    echo "   • Health Check: http://localhost:${PORT}/api/health"
    echo "   • API Documentation: http://localhost:${PORT}/docs"
    echo "   • Dashboard: http://localhost:${PORT}/dashboard"
    echo ""
    echo "🔑 API Key for testing: ${API_KEY}"
    echo ""
    echo "📋 Quick Test Commands:"
    echo "   # Health check"
    echo "   curl http://localhost:${PORT}/api/health"
    echo ""
    echo "   # Start a test call"
    echo "   curl -X POST http://localhost:${PORT}/api/happyrobot/start-call \\"
    echo "        -H \"X-API-Key: ${API_KEY}\" \\"
    echo "        -H \"Content-Type: application/json\" \\"
    echo "        -d '{\"call_id\": \"test-call-123\"}'"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f api"
    echo ""
    echo "🛑 Stop application:"
    echo "   docker-compose down"
}

# Function to show help
show_help() {
    echo "Carrier Agent API Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -p, --port     Set the port (default: 8000)"
    echo "  -e, --env      Environment file path (default: .env)"
    echo "  --with-nginx   Deploy with Nginx reverse proxy"
    echo "  --stop         Stop the application"
    echo "  --logs         Show application logs"
    echo "  --status       Show application status"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy with default settings"
    echo "  $0 --with-nginx       # Deploy with Nginx"
    echo "  $0 --stop             # Stop the application"
    echo "  $0 --logs             # Show logs"
}

# Function to stop application
stop_application() {
    print_status "Stopping application..."
    docker-compose down
    print_success "Application stopped"
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker-compose logs -f api
}

# Function to show status
show_status() {
    print_status "Application status:"
    docker-compose ps
    echo ""
    print_status "Health check:"
    if curl -f -s http://localhost:${PORT}/api/health >/dev/null; then
        print_success "Application is healthy"
    else
        print_error "Application is not responding"
    fi
}

# Main function
main() {
    local WITH_NGINX=false
    local STOP_APP=false
    local SHOW_LOGS=false
    local SHOW_STATUS=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--port)
                export PORT="$2"
                shift 2
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            --with-nginx)
                WITH_NGINX=true
                shift
                ;;
            --stop)
                STOP_APP=true
                shift
                ;;
            --logs)
                SHOW_LOGS=true
                shift
                ;;
            --status)
                SHOW_STATUS=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle special commands
    if [ "$STOP_APP" = true ]; then
        stop_application
        exit 0
    fi
    
    if [ "$SHOW_LOGS" = true ]; then
        show_logs
        exit 0
    fi
    
    if [ "$SHOW_STATUS" = true ]; then
        show_status
        exit 0
    fi
    
    # Main deployment process
    echo "🚀 Starting Carrier Agent API Deployment"
    echo "========================================"
    
    # Check prerequisites
    check_docker
    
    # Setup environment
    setup_environment
    
    # Deploy application
    deploy_application
    
    # Initialize database
    initialize_database
    
    # Verify deployment
    if verify_deployment; then
        show_deployment_info
    else
        print_error "Deployment verification failed"
        print_status "Showing logs for debugging:"
        docker-compose logs api
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
