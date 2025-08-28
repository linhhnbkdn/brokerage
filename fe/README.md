# BrokerPro Frontend

A modern React application built with React Router v7, providing a comprehensive brokerage platform interface with real-time market data, trading capabilities, and portfolio management.

## 🏗️ Technical Architecture

### Core Technologies
- **Framework**: React 18 with React Router v7 (SSR enabled)
- **Language**: TypeScript (strict mode) with path aliases
- **Styling**: TailwindCSS v4 with Vite plugin
- **Build Tool**: Vite with React Router plugin
- **Real-time**: WebSocket integration for market data
- **Authentication**: JWT-based authentication with secure token management
- **State Management**: React hooks with custom hooks for complex state

### Key Features
- 🔐 **Secure Authentication** with JWT tokens and refresh flow
- 📈 **Real-time Trading Dashboard** with WebSocket market data
- 💰 **Banking Integration** for deposits and withdrawals
- 📊 **Portfolio Management** with performance tracking
- 🌙 **Dark Mode Support** with system preference detection
- 📱 **Responsive Design** optimized for all device sizes
- ⚡ **Server-Side Rendering** for improved performance and SEO
- 🔄 **Hot Module Replacement** for rapid development

### Application Structure
```
fe/
├── app/
│   ├── components/        # Reusable UI components
│   ├── hooks/            # Custom React hooks
│   │   ├── useAuth.ts    # Authentication management
│   │   └── useExchange.ts # WebSocket market data
│   ├── lib/              # Utilities and API clients
│   │   ├── api-client.ts # REST API integration
│   │   └── websocket-client.ts # WebSocket client
│   ├── routes/           # File-based routing pages
│   │   ├── _index.tsx    # Landing page
│   │   ├── login.tsx     # Authentication
│   │   ├── dashboard.tsx # Portfolio overview
│   │   ├── trading.tsx   # Real-time trading
│   │   └── banking.tsx   # Account management
│   └── root.tsx          # App shell and layout
└── react-router.config.ts # Router configuration
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager

### Development Setup

1. **Navigate to frontend**:
```bash
cd fe/
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start development server**:
```bash
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Hot Reload**: Enabled for instant development feedback

### Available Scripts

```bash
npm run dev          # Start development server with HMR
npm run build        # Create production build
npm run start        # Start production server
npm run typecheck    # Run TypeScript type checking
npm run preview      # Preview production build locally
```

## 📱 Application Pages

### 🏠 Landing Page (`/`)
- Modern hero section with feature highlights
- Call-to-action for user registration
- Responsive design with mobile optimization

### 🔐 Authentication (`/login`, `/register`)
- Secure JWT authentication flow
- Form validation and error handling
- Automatic redirect after successful login

### 📊 Dashboard (`/dashboard`)
- Portfolio performance overview
- Holdings summary with real-time values
- Quick access to trading and banking features
- Interactive charts and metrics

### 📈 Trading (`/trading`)
- **Real-time Market Data**: Live price feeds via WebSocket
- **Symbol Subscription**: Subscribe to multiple instruments
- **Order Placement**: Market and limit orders
- **Order History**: Track all trading activity
- **Market Alerts**: Real-time notifications

### 💳 Banking (`/banking`)
- Linked bank account management
- Secure deposit and withdrawal operations
- Transaction history and status tracking
- Account verification flow

## 🔌 Real-time Integration

### WebSocket Connection
The trading dashboard establishes a WebSocket connection for real-time data:

```typescript
// Automatic connection management
const { state, connect, subscribe, placeOrder } = useExchange();

// Subscribe to market data
useEffect(() => {
  if (state.isAuthenticated) {
    subscribe(['AAPL', 'BTC-USD', 'ETH-USD']);
  }
}, [state.isAuthenticated]);
```

### Supported Features
- **Live Price Updates**: Real-time price streaming
- **Market Subscriptions**: Subscribe/unsubscribe to symbols
- **Order Execution**: Real-time order status updates
- **Market Alerts**: Breaking news and price alerts
- **Connection Management**: Automatic reconnection and error handling

## 🎨 Design System

### Color Palette
- **Primary**: Blue gradient (#3B82F6 to #8B5CF6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Neutral**: Slate grays for text and backgrounds

### Typography
- **Headings**: Inter font family with semibold weights
- **Body**: System font stack with optimal readability
- **Code**: Monospace for technical content

### Layout Patterns
- **Glass Morphism**: Frosted glass effects with backdrop blur
- **Card Design**: Elevated containers with subtle shadows
- **Responsive Grid**: Flexible layouts for all screen sizes
- **Navigation**: Persistent header with user context

## 🔧 Development Tools

### TypeScript Configuration
```json
{
  "compilerOptions": {
    "strict": true,
    "paths": {
      "~/*": ["./app/*"]
    }
  }
}
```

### Path Aliases
- `~/components/*` → `./app/components/*`
- `~/hooks/*` → `./app/hooks/*`
- `~/lib/*` → `./app/lib/*`

### Code Quality
- **TypeScript**: Strict mode enabled for type safety
- **ESLint**: Code linting with React and TypeScript rules
- **Prettier**: Automatic code formatting

## 🐳 Docker Support

### Development Container
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

### Production Build
```bash
# Build the application
npm run build

# Create production Docker image
docker build -t brokerpro-frontend .
docker run -p 3000:3000 brokerpro-frontend
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/market-data/

# Application Settings
VITE_APP_NAME=BrokerPro
VITE_APP_VERSION=1.0.0
```

### React Router Configuration
```typescript
// react-router.config.ts
export default {
  ssr: true,
  basename: "/",
  future: {
    unstable_optimizeDeps: true
  }
} satisfies Config;
```

## 🧪 Testing

### Component Testing
```bash
npm run test              # Run test suite
npm run test:watch        # Watch mode for development
npm run test:coverage     # Generate coverage report
```

### E2E Testing
```bash
npm run test:e2e          # End-to-end tests
npm run test:e2e:ui       # Interactive test runner
```

## 🚀 Performance Optimization

### Build Optimizations
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Eliminate unused code
- **Asset Optimization**: Image compression and lazy loading
- **Bundle Analysis**: Visualize bundle composition

### Runtime Performance
- **React.memo**: Prevent unnecessary re-renders
- **useCallback/useMemo**: Optimize expensive computations
- **Virtual Scrolling**: Handle large data sets efficiently
- **Service Workers**: Offline capability and caching

## 📊 Monitoring

### Performance Metrics
- **Core Web Vitals**: LCP, FID, CLS tracking
- **Bundle Size**: Monitor JavaScript payload
- **Load Times**: Page load performance
- **Error Boundaries**: Graceful error handling

### Analytics Integration
- User interaction tracking
- Performance monitoring
- Error reporting and alerting

## 🚀 Deployment

### Static Hosting
```bash
npm run build
# Deploy build/client/ to static hosting (Vercel, Netlify, S3)
```

### Server-Side Rendering
```bash
npm run build
npm run start
# Deploy full-stack application with SSR
```

### Docker Deployment
```bash
docker build -t brokerpro-frontend .
docker run -p 3000:3000 brokerpro-frontend
```

## 🔐 Security Features

- **XSS Protection**: Sanitized user inputs and outputs
- **CSRF Prevention**: Token-based request validation
- **Secure Authentication**: JWT tokens with secure storage
- **Content Security Policy**: Restrict resource loading
- **HTTPS Enforcement**: Secure data transmission

## 📚 Browser Support

- **Modern Browsers**: Chrome 88+, Firefox 85+, Safari 14+
- **ES2020 Features**: Native async/await, optional chaining
- **Module Support**: Native ES modules
- **WebSocket Support**: Real-time communication

## 🤝 Contributing

1. Follow TypeScript strict mode conventions
2. Use provided ESLint and Prettier configurations
3. Maintain responsive design principles
4. Write comprehensive component tests
5. Update documentation for new features

## 📖 Documentation

- **React Router v7**: https://reactrouter.com/
- **TailwindCSS**: https://tailwindcss.com/
- **Vite**: https://vitejs.dev/
- **TypeScript**: https://www.typescriptlang.org/

---

Built with ❤️ using React Router v7 and modern web technologies.
