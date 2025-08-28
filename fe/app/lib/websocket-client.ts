/**
 * WebSocket client for real-time exchange integration
 * Based on exchange-integration-system.mmd design
 */

import { getAccessToken } from "./api-client";

// WebSocket connection URL
const WS_BASE_URL = "ws://localhost:8000";

// WebSocket Message Types (from design)
export interface WSAuthMessage {
  type: "auth";
  token: string;
}

export interface WSAuthSuccessMessage {
  type: "auth_success";
  user_id: number;
  message: string;
}

export interface WSSubscribeMessage {
  type: "subscribe";
  symbols: string[];
}

export interface WSSubscribedMessage {
  type: "subscribed";
  symbols: string[];
  count: number;
}

export interface WSUnsubscribeMessage {
  type: "unsubscribe";
  symbols: string[];
}

export interface WSUnsubscribedMessage {
  type: "unsubscribed";
  symbols: string[];
}

export interface WSPriceUpdateMessage {
  type: "price_update";
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  bid: number;
  ask: number;
  timestamp: string;
}

export interface WSPlaceOrderMessage {
  type: "place_order";
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  order_type: "market" | "limit";
  price?: number;
}

export interface WSOrderExecutedMessage {
  type: "order_executed";
  order_id: string;
  symbol: string;
  status: "filled" | "partial" | "cancelled";
  quantity: number;
  price: number;
  timestamp: string;
}

export interface WSMarketAlertMessage {
  type: "market_alert";
  symbol: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  timestamp: string;
}

export interface WSPingMessage {
  type: "ping";
}

export interface WSPongMessage {
  type: "pong";
  timestamp: string;
}

export type WSMessage = 
  | WSAuthMessage
  | WSAuthSuccessMessage
  | WSSubscribeMessage
  | WSSubscribedMessage
  | WSUnsubscribeMessage
  | WSUnsubscribedMessage
  | WSPriceUpdateMessage
  | WSPlaceOrderMessage
  | WSOrderExecutedMessage
  | WSMarketAlertMessage
  | WSPingMessage
  | WSPongMessage;

export type WSIncomingMessage = 
  | WSAuthSuccessMessage
  | WSSubscribedMessage
  | WSUnsubscribedMessage
  | WSPriceUpdateMessage
  | WSOrderExecutedMessage
  | WSMarketAlertMessage
  | WSPongMessage;

export type WSOutgoingMessage = 
  | WSAuthMessage
  | WSSubscribeMessage
  | WSUnsubscribeMessage
  | WSPlaceOrderMessage
  | WSPingMessage;

export interface WebSocketClientOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onAuthSuccess?: (message: WSAuthSuccessMessage) => void;
  onPriceUpdate?: (message: WSPriceUpdateMessage) => void;
  onOrderExecuted?: (message: WSOrderExecutedMessage) => void;
  onMarketAlert?: (message: WSMarketAlertMessage) => void;
  onSubscribed?: (message: WSSubscribedMessage) => void;
  onUnsubscribed?: (message: WSUnsubscribedMessage) => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

export class ExchangeWebSocketClient {
  private ws: WebSocket | null = null;
  private options: WebSocketClientOptions;
  private subscribedSymbols: string[] = [];
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isAuthenticated = false;
  private shouldReconnect = true;

  constructor(options: WebSocketClientOptions = {}) {
    this.options = {
      autoReconnect: true,
      reconnectInterval: 5000,
      heartbeatInterval: 30000,
      ...options,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        console.log('🔄 Connecting to WebSocket server...');
        
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/market-data/`);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.options.onConnect?.();
          this.authenticate();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          console.log('❌ WebSocket disconnected:', event.code, event.reason);
          this.isAuthenticated = false;
          this.options.onDisconnect?.();
          
          if (this.shouldReconnect && this.options.autoReconnect) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.options.onError?.(error);
          reject(error);
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    console.log('🔄 Disconnecting from WebSocket server...');
    
    this.shouldReconnect = false;
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isAuthenticated = false;
    this.subscribedSymbols = [];
  }

  /**
   * Send authentication message
   */
  private authenticate(): void {
    const token = getAccessToken();
    if (!token) {
      console.error('❌ No access token available for WebSocket authentication');
      return;
    }

    const authMessage: WSAuthMessage = {
      type: "auth",
      token,
    };

    this.sendMessage(authMessage);
  }

  /**
   * Subscribe to market data for symbols
   */
  subscribe(symbols: string[]): void {
    if (!this.isAuthenticated) {
      console.warn('⚠️ Cannot subscribe: not authenticated');
      return;
    }

    console.log('🔄 Subscribing to symbols:', symbols);

    const subscribeMessage: WSSubscribeMessage = {
      type: "subscribe",
      symbols,
    };

    this.sendMessage(subscribeMessage);
  }

  /**
   * Unsubscribe from market data for symbols
   */
  unsubscribe(symbols: string[]): void {
    if (!this.isAuthenticated) {
      console.warn('⚠️ Cannot unsubscribe: not authenticated');
      return;
    }

    console.log('🔄 Unsubscribing from symbols:', symbols);

    const unsubscribeMessage: WSUnsubscribeMessage = {
      type: "unsubscribe",
      symbols,
    };

    this.sendMessage(unsubscribeMessage);
  }

  /**
   * Place order via WebSocket
   */
  placeOrder(symbol: string, side: "buy" | "sell", quantity: number, orderType: "market" | "limit", price?: number): void {
    if (!this.isAuthenticated) {
      console.warn('⚠️ Cannot place order: not authenticated');
      return;
    }

    console.log(`🔄 Placing ${orderType} ${side} order:`, { symbol, quantity, price });

    const orderMessage: WSPlaceOrderMessage = {
      type: "place_order",
      symbol,
      side,
      quantity,
      order_type: orderType,
      price,
    };

    this.sendMessage(orderMessage);
  }

  /**
   * Send ping to keep connection alive
   */
  ping(): void {
    const pingMessage: WSPingMessage = {
      type: "ping",
    };

    this.sendMessage(pingMessage);
  }

  /**
   * Get currently subscribed symbols
   */
  getSubscribedSymbols(): string[] {
    return [...this.subscribedSymbols];
  }

  /**
   * Check if WebSocket is connected and authenticated
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.isAuthenticated;
  }

  /**
   * Send message to WebSocket server
   */
  private sendMessage(message: WSOutgoingMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ WebSocket is not open, message not sent:', message);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSIncomingMessage = JSON.parse(event.data);
      console.log('📨 Received WebSocket message:', message.type);

      switch (message.type) {
        case "auth_success":
          this.isAuthenticated = true;
          console.log('✅ WebSocket authenticated successfully');
          this.options.onAuthSuccess?.(message);
          this.startHeartbeat();
          // Restore subscriptions if reconnecting
          if (this.subscribedSymbols.length > 0) {
            this.subscribe(this.subscribedSymbols);
          }
          break;

        case "subscribed":
          this.subscribedSymbols = [...new Set([...this.subscribedSymbols, ...message.symbols])];
          console.log('✅ Subscribed to symbols:', message.symbols);
          this.options.onSubscribed?.(message);
          break;

        case "unsubscribed":
          this.subscribedSymbols = this.subscribedSymbols.filter(symbol => !message.symbols.includes(symbol));
          console.log('✅ Unsubscribed from symbols:', message.symbols);
          this.options.onUnsubscribed?.(message);
          break;

        case "price_update":
          this.options.onPriceUpdate?.(message);
          break;

        case "order_executed":
          console.log('✅ Order executed:', message);
          this.options.onOrderExecuted?.(message);
          break;

        case "market_alert":
          console.log('🚨 Market alert:', message);
          this.options.onMarketAlert?.(message);
          break;

        case "pong":
          console.log('🏓 Received pong');
          break;

        default:
          console.warn('⚠️ Unknown message type:', (message as any).type);
      }
    } catch (error) {
      console.error('❌ Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.ping();
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    console.log(`🔄 Scheduling reconnect in ${this.options.reconnectInterval}ms...`);
    
    this.reconnectTimeout = setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch(() => {
          // Reconnection failed, will try again
        });
      }
    }, this.options.reconnectInterval);
  }
}

// Singleton instance for easy use
let globalWebSocketClient: ExchangeWebSocketClient | null = null;

/**
 * Get global WebSocket client instance
 */
export function getWebSocketClient(options?: WebSocketClientOptions): ExchangeWebSocketClient {
  if (!globalWebSocketClient) {
    globalWebSocketClient = new ExchangeWebSocketClient(options);
  }
  return globalWebSocketClient;
}

/**
 * Initialize WebSocket connection
 */
export async function initializeWebSocket(options?: WebSocketClientOptions): Promise<ExchangeWebSocketClient> {
  const client = getWebSocketClient(options);
  await client.connect();
  return client;
}