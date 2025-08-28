# BrokerPro - Modern Brokerage Platform

A full-stack modern brokerage application supporting stocks, bonds, and cryptocurrency trading with real-time market data integration, comprehensive portfolio management, and secure banking operations.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│                 │    │                 │    │                 │
│  React Router   │◄──►│  Django + DRF   │◄──►│    SQLite       │
│  TypeScript     │    │  WebSockets     │    │   (Development) │
│  TailwindCSS    │    │  JWT Auth       │    │                 │
│  WebSocket      │    │  Market Sim     │    │   PostgreSQL    │
│                 │    │                 │    │  (Production)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      :5173                   :8000                 :5432
```

### Core Technologies

**Frontend:**
- React 18 + React Router v7 (SSR)
- TypeScript + TailwindCSS v4
- WebSocket real-time integration
- JWT authentication

**Backend:**
- Django 5.2.5 + Django REST Framework
- Django Channels (WebSocket support)
- JWT authentication with refresh tokens
- Exchange market data simulator
- Comprehensive API documentation

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL (production) / SQLite (dev)
- Redis (production WebSocket scaling)
- Nginx reverse proxy

## 🚀 Quick Start with Docker

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd brokerage

# Start the entire application
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

**Access Points:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/api/docs/
- 🔌 **WebSocket**: ws://localhost:8000/ws/market-data/

### Manual Development (Alternative)

```bash
# Run backend manually
cd be && make runserver

# Run frontend manually  
cd fe && npm run dev
```

## 📦 Project Structure

```
brokerage/
├── docker-compose.yml          # Multi-service orchestration
├── docker-compose.dev.yml      # Development overrides
├── .env.example                # Environment template
├── README.md                   # This file
│
├── be/                         # Django Backend
│   ├── authentication/        # JWT auth system
│   ├── banking/               # Bank account management
│   ├── portfolio/             # Holdings & performance
│   ├── exchange/              # Trading & market data
│   ├── Dockerfile             # Backend container
│   ├── requirements.txt       # Python dependencies
│   ├── Makefile              # Development commands
│   └── README.md             # Backend documentation
│
├── fe/                        # React Frontend
│   ├── app/
│   │   ├── components/       # UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # API clients & utilities
│   │   └── routes/          # Page components
│   ├── Dockerfile           # Frontend container
│   ├── package.json         # Node dependencies
│   └── README.md           # Frontend documentation
│
└── nginx/                    # Reverse Proxy
    └── nginx.conf           # Production configuration
```

## 🔌 Real-time Features

### Market Data Simulation
The backend includes a realistic market data simulator:

```bash
# Start the exchange simulator
docker-compose exec backend python manage.py run_exchange_simulator

# Or run for specific duration
docker-compose exec backend python manage.py run_exchange_simulator --duration=300
```

**Supported Instruments:**
- **Stocks**: AAPL, GOOGL, MSFT, TSLA, AMZN, META, NFLX
- **ETFs**: SPY, QQQ, VTI, VOO, IWM
- **Crypto**: BTC-USD, ETH-USD, ADA-USD, DOT-USD, SOL-USD

### WebSocket Integration
Real-time market data streaming:

```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/market-data/');

// Authenticate with JWT
ws.send(JSON.stringify({
  type: 'auth',
  token: localStorage.getItem('access_token')
}));

// Subscribe to real-time data
ws.send(JSON.stringify({
  type: 'subscribe',
  symbols: ['AAPL', 'BTC-USD', 'ETH-USD']
}));
```

## 🎯 Key Features

### 🔐 Authentication & Security
- JWT-based authentication with refresh tokens
- Secure password hashing and validation
- CORS protection for cross-origin requests
- Encrypted banking information storage

### 📈 Trading Platform
- **Real-time Market Data**: Live price feeds and updates
- **Order Management**: Market and limit order support
- **Portfolio Tracking**: Holdings, P&L, and performance metrics
- **Market Alerts**: Real-time notifications and news

### 💰 Banking Integration
- Secure bank account linking
- Deposit and withdrawal operations
- Transaction history and status tracking
- Account verification workflow

### 📊 User Interface
- Modern responsive design with dark mode
- Glass morphism design patterns
- Interactive charts and data visualization
- Mobile-optimized trading interface

## 🐳 Docker Commands

### Basic Docker Operations

```bash
# Build and start services
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart backend

# Access backend container shell
docker-compose exec backend bash

# Access frontend container shell
docker-compose exec frontend sh
```

## 🔧 Development Workflow

### Backend Development

```bash
cd be/

# Setup development environment
make install
make migrate
make createsuperuser

# Run development server
make runserver

# Code quality
make test
make lint
make format
```

### Frontend Development

```bash
cd fe/

# Setup development environment
npm install

# Run development server
npm run dev

# Code quality
npm run typecheck
npm run build
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access Django shell
docker-compose exec backend python manage.py shell

# Run exchange simulator
docker-compose exec backend python manage.py run_exchange_simulator
```

## 📊 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Key Endpoints

```bash
# Authentication
POST /api/auth/login/              # User login
POST /api/auth/register/           # User registration
POST /api/auth/refresh/            # Token refresh

# Market Data
GET  /api/exchange/api/v1/market-data/supported_symbols/
GET  /api/exchange/api/v1/market-data/current_prices/?symbols=AAPL,BTC-USD

# Trading
POST /api/exchange/api/v1/orders/  # Place order
GET  /api/exchange/api/v1/orders/  # Order history

# Banking
GET  /api/banking/accounts/        # Linked accounts
POST /api/banking/transactions/    # Deposit/withdrawal

# Portfolio
GET  /api/portfolio/holdings/      # Current holdings
GET  /api/portfolio/performance/   # Performance metrics
```

## 🧪 Testing

### Backend Testing
```bash
# Run all tests with coverage
docker-compose exec backend make test

# Run specific test
docker-compose exec backend python manage.py test exchange.tests.test_market_data
```

### Frontend Testing
```bash
# Run frontend tests
docker-compose exec frontend npm run test

# E2E testing
docker-compose exec frontend npm run test:e2e
```

### Integration Testing
```bash
# Full system test
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 🔍 Troubleshooting

### Common Issues

**Backend not starting:**
```bash
# Check logs
docker-compose logs backend

# Rebuild container
docker-compose build --no-cache backend
```

**Frontend build errors:**
```bash
# Clear npm cache
docker-compose exec frontend npm cache clean --force

# Rebuild container
docker-compose build --no-cache frontend
```

**Database connection errors:**
```bash
# Make sure migrations are run
docker-compose exec backend python manage.py migrate

# Check database status
docker-compose logs backend
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Setup development environment with Docker
4. Make changes and add tests
5. Run code quality checks
6. Submit pull request

### Code Standards
- **Backend**: Follow PEP 8, use type hints, maintain 80%+ test coverage
- **Frontend**: TypeScript strict mode, responsive design, component testing
- **Documentation**: Update README files for new features

## 📚 Additional Resources

### Architecture Documentation
- [JWT Authentication Flow](be/design/jwt-authentication-flow.mmd)
- [Exchange Integration System](be/design/exchange-integration-system.mmd)
- [API Documentation](http://localhost:8000/api/docs/)

### Technology Stack Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [React Router v7](https://reactrouter.com/)
- [TailwindCSS](https://tailwindcss.com/)
- [Django Channels](https://channels.readthedocs.io/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

🚀 **Built with modern technologies for scalable, real-time trading platforms**

For detailed information about each component, see the README files in the `be/` and `fe/` directories.
