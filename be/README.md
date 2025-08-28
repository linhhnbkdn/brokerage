# BrokerPro Backend API

A modern Django REST API backend for a comprehensive brokerage platform supporting stock, bond, and cryptocurrency trading with real-time market data integration.

## 🏗️ Technical Architecture

### Core Technologies
- **Framework**: Django 5.2.5 with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Real-time**: Django Channels with WebSockets + ASGI (Daphne)
- **Authentication**: JWT-based authentication with refresh tokens
- **API Documentation**: drf-spectacular (OpenAPI 3.0/Swagger)
- **Package Management**: UV (modern Python package manager)
- **Code Quality**: Ruff (linting + formatting), MyPy (type checking)

### Key Features
- 🔐 **JWT Authentication Flow** with secure token refresh and blacklisting
- 📈 **Real-time Market Data Streaming** via WebSockets
- 🤖 **Exchange Simulator** for generating realistic dummy market data
- 💰 **Banking Integration** with encrypted account management
- 📊 **Portfolio Tracking** and performance analytics
- 🔄 **Order Management System** with market/limit order support
- 🌐 **CORS Enabled** for cross-origin frontend integration
- 📝 **Comprehensive API Documentation** with interactive Swagger UI

### Apps Structure
```
be/
├── authentication/     # JWT auth, user management
├── banking/           # Account linking, deposits/withdrawals  
├── portfolio/         # Holdings, performance tracking
├── exchange/          # Trading, market data, WebSocket consumers
├── be/               # Main Django project settings
└── manage.py         # Django management commands
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- UV package manager (or pip/pipenv)

### Development Setup

1. **Clone and navigate to backend**:
```bash
cd be/
```

2. **Install dependencies**:
```bash
make install
# or: uv sync
```

3. **Setup database**:
```bash
make migrate
# or: uv run python manage.py migrate
```

4. **Create superuser** (optional):
```bash
make createsuperuser
# or: uv run python manage.py createsuperuser
```

5. **Start development server**:
```bash
make runserver
# or: uv run daphne -p 8000 be.asgi:application
```

The API will be available at:
- **Main API**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **WebSocket Endpoint**: ws://localhost:8000/ws/market-data/

## 📡 Real-time Market Data

### Exchange Simulator
Generate realistic market data for development/testing:

```bash
# Run simulator for 60 seconds
make run-simulator DURATION=60

# Run simulator indefinitely (Ctrl+C to stop)
uv run python manage.py run_exchange_simulator

# Custom update interval (default: 2 seconds)
uv run python manage.py run_exchange_simulator --interval=1
```

**Supported Instruments**:
- **Stocks**: AAPL, GOOGL, MSFT, TSLA, AMZN, META, NFLX
- **ETFs**: SPY, QQQ, VTI, VOO, IWM  
- **Crypto**: BTC-USD, ETH-USD, ADA-USD, DOT-USD, SOL-USD

### WebSocket Integration
Connect to real-time market data:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-data/');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));

// Subscribe to symbols
ws.send(JSON.stringify({
  type: 'subscribe', 
  symbols: ['AAPL', 'BTC-USD']
}));
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login/` - User authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Token refresh
- `POST /api/auth/logout/` - Secure logout

### Market Data
- `GET /api/exchange/api/v1/market-data/supported_symbols/` - Available symbols
- `GET /api/exchange/api/v1/market-data/current_prices/?symbols=AAPL,BTC-USD` - Current prices
- `GET /api/exchange/api/v1/market-data/{id}/` - Historical data
- `GET /api/exchange/api/v1/market-data/statistics/?symbol=AAPL` - Market statistics

### Trading
- `POST /api/exchange/api/v1/orders/` - Place order
- `GET /api/exchange/api/v1/orders/` - Order history
- `GET /api/exchange/api/v1/orders/{id}/` - Order details

### Banking
- `GET /api/banking/accounts/` - Linked accounts
- `POST /api/banking/accounts/` - Link new account
- `POST /api/banking/transactions/` - Deposit/withdrawal

### Portfolio
- `GET /api/portfolio/holdings/` - Current holdings
- `GET /api/portfolio/performance/` - Performance metrics

## 🔧 Development Commands

### Using Makefile (Recommended)
```bash
make help                 # Show all commands
make install             # Install dependencies  
make runserver           # Start Django server
make test                # Run tests with coverage
make lint                # Run ruff linting
make format              # Format code
make check               # Run all quality checks
make migrate             # Apply migrations
make makemigrations      # Create migrations
make run-simulator       # Start market simulator
```

### Direct UV Commands
```bash
uv run python manage.py runserver
uv run python manage.py test
uv run python manage.py shell
uv run python manage.py makemigrations
uv run python manage.py migrate
```

## 🐳 Docker Support

### Development Container
```bash
make docker-build
make docker-run
```

### Production Deployment
```bash
docker build -t brokerpro-api .
docker run -p 8000:8000 -e DEBUG=False brokerpro-api
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/brokerpro

# Security
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,localhost

# Redis (for production WebSockets)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Banking Encryption
BANKING_ENCRYPTION_KEY=base64-encoded-key
```

### Django Settings
Key configurations in `be/settings.py`:
- **CORS**: Frontend origins allowed
- **JWT Settings**: Token lifetimes and security
- **Exchange Settings**: Market data simulation parameters
- **Channel Layers**: WebSocket backend configuration

## 🧪 Testing

### Run Test Suite
```bash
make test                # Full test suite with coverage
make test-fast          # Tests without coverage report
```

### Coverage Requirements
- Minimum coverage threshold: **80%**
- Tests include: API endpoints, WebSocket consumers, business logic
- Factories provided for easy test data generation

## 🔒 Security Features

- **JWT Authentication** with secure token refresh
- **CORS Protection** with configurable origins
- **Banking Data Encryption** for sensitive information
- **SQL Injection Protection** via Django ORM
- **XSS Protection** via Django middleware
- **CSRF Protection** for state-changing operations

## 🚀 Production Deployment

### Database Migration
```bash
uv run python manage.py collectstatic --noinput
uv run python manage.py migrate --noinput
```

### ASGI Server (for WebSockets)
```bash
daphne -b 0.0.0.0 -p 8000 be.asgi:application
```

### Reverse Proxy (Nginx)
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📈 Performance Considerations

- **Database Indexing**: Optimized queries for market data
- **Connection Pooling**: Efficient database connections
- **Caching Strategy**: Redis for session and market data caching  
- **WebSocket Scaling**: Channel layers for multi-server deployment
- **Query Optimization**: Select_related and prefetch_related usage

## 🔍 Monitoring & Logging

### Health Checks
- `GET /api/exchange/api/v1/status/` - System status
- Database connectivity verification
- WebSocket service status

### Logging Configuration
- Structured logging for production debugging
- Market data operation tracking
- WebSocket connection monitoring
- Error aggregation support

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Run `make check` before committing
3. Maintain test coverage above 80%
4. Use type hints for all new code
5. Update API documentation for new endpoints

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

Built with ❤️ using Django and modern Python tooling.