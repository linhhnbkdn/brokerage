/**
 * React hook for exchange WebSocket integration
 * Provides real-time market data and trading functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ExchangeWebSocketClient, 
  getWebSocketClient,
  type WSPriceUpdateMessage,
  type WSOrderExecutedMessage,
  type WSMarketAlertMessage,
  type WSSubscribedMessage,
  type WSUnsubscribedMessage
} from '../lib/websocket-client';
import { 
  getExchangeStatus,
  getMarketData,
  getCurrentPrices,
  getSupportedSymbols,
  getMarketStatistics,
  type MarketDataSnapshot 
} from '../lib/api-client';

export interface ExchangeState {
  // Connection state
  isConnected: boolean;
  isAuthenticated: boolean;
  connectionError: string | null;
  
  // Market data
  marketData: Record<string, WSPriceUpdateMessage>;
  subscribedSymbols: string[];
  supportedSymbols: string[];
  
  // Orders
  orderHistory: WSOrderExecutedMessage[];
  
  // Alerts
  marketAlerts: WSMarketAlertMessage[];
  
  // System status
  exchangeStatus: any;
  isLoading: boolean;
}

export interface UseExchangeReturn {
  // State
  state: ExchangeState;
  
  // WebSocket actions
  connect: () => Promise<void>;
  disconnect: () => void;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  placeOrder: (symbol: string, side: 'buy' | 'sell', quantity: number, orderType: 'market' | 'limit', price?: number) => void;
  
  // API actions
  refreshMarketData: () => Promise<void>;
  refreshExchangeStatus: () => Promise<void>;
  loadSupportedSymbols: () => Promise<void>;
  getCurrentPrices: () => Promise<any>;
  loadCurrentPrices: (symbols: string[]) => Promise<void>;
  
  // Utilities
  getPriceForSymbol: (symbol: string) => WSPriceUpdateMessage | null;
  clearAlerts: () => void;
  clearOrderHistory: () => void;
}

export function useExchange(): UseExchangeReturn {
  const [state, setState] = useState<ExchangeState>({
    isConnected: false,
    isAuthenticated: false,
    connectionError: null,
    marketData: {},
    subscribedSymbols: [],
    supportedSymbols: [],
    orderHistory: [],
    marketAlerts: [],
    exchangeStatus: null,
    isLoading: false,
  });

  const webSocketClient = useRef<ExchangeWebSocketClient | null>(null);

  /**
   * Initialize WebSocket client
   */
  const initializeClient = useCallback(() => {
    if (webSocketClient.current) {
      return webSocketClient.current;
    }

    const client = getWebSocketClient({
      onConnect: () => {
        console.log('🔌 WebSocket connected');
        setState(prev => ({ 
          ...prev, 
          isConnected: true, 
          connectionError: null 
        }));
      },

      onDisconnect: () => {
        console.log('🔌 WebSocket disconnected');
        setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          isAuthenticated: false 
        }));
      },

      onAuthSuccess: (message) => {
        console.log('✅ WebSocket authenticated:', message);
        setState(prev => ({ 
          ...prev, 
          isAuthenticated: true 
        }));
      },

      onPriceUpdate: (message) => {
        setState(prev => ({
          ...prev,
          marketData: {
            ...prev.marketData,
            [message.symbol]: message
          }
        }));
      },

      onOrderExecuted: (message) => {
        setState(prev => ({
          ...prev,
          orderHistory: [...prev.orderHistory, message]
        }));
      },

      onMarketAlert: (message) => {
        setState(prev => ({
          ...prev,
          marketAlerts: [...prev.marketAlerts, message]
        }));
      },

      onSubscribed: (message) => {
        setState(prev => ({
          ...prev,
          subscribedSymbols: [...new Set([...prev.subscribedSymbols, ...message.symbols])]
        }));
      },

      onUnsubscribed: (message) => {
        setState(prev => ({
          ...prev,
          subscribedSymbols: prev.subscribedSymbols.filter(symbol => !message.symbols.includes(symbol))
        }));
      },

      onError: (error) => {
        console.error('❌ WebSocket error:', error);
        setState(prev => ({ 
          ...prev, 
          connectionError: 'WebSocket connection error' 
        }));
      },

      autoReconnect: true,
      reconnectInterval: 5000,
      heartbeatInterval: 30000,
    });

    webSocketClient.current = client;
    return client;
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, connectionError: null }));
      const client = initializeClient();
      await client.connect();
    } catch (error) {
      console.error('❌ Failed to connect to WebSocket:', error);
      setState(prev => ({ 
        ...prev, 
        connectionError: 'Failed to connect to WebSocket',
        isLoading: false
      }));
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [initializeClient]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    webSocketClient.current?.disconnect();
    setState(prev => ({
      ...prev,
      isConnected: false,
      isAuthenticated: false,
      subscribedSymbols: [],
      marketData: {}
    }));
  }, []);

  /**
   * Subscribe to symbols
   */
  const subscribe = useCallback((symbols: string[]) => {
    webSocketClient.current?.subscribe(symbols);
  }, []);

  /**
   * Unsubscribe from symbols
   */
  const unsubscribe = useCallback((symbols: string[]) => {
    webSocketClient.current?.unsubscribe(symbols);
  }, []);

  /**
   * Place order
   */
  const placeOrder = useCallback((
    symbol: string, 
    side: 'buy' | 'sell', 
    quantity: number, 
    orderType: 'market' | 'limit', 
    price?: number
  ) => {
    webSocketClient.current?.placeOrder(symbol, side, quantity, orderType, price);
  }, []);

  /**
   * Refresh market data from API
   */
  const refreshMarketData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const data = await getMarketData();
      console.log('📊 Market data refreshed:', data);
    } catch (error) {
      console.error('❌ Failed to refresh market data:', error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  /**
   * Refresh exchange status
   */
  const refreshExchangeStatus = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const status = await getExchangeStatus();
      setState(prev => ({ ...prev, exchangeStatus: status }));
      console.log('✅ Exchange status refreshed:', status);
    } catch (error) {
      console.error('❌ Failed to refresh exchange status:', error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  /**
   * Load supported symbols
   */
  const loadSupportedSymbols = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const symbols = await getSupportedSymbols();
      setState(prev => ({ ...prev, supportedSymbols: symbols }));
      console.log('📈 Supported symbols loaded:', symbols);
    } catch (error) {
      console.error('❌ Failed to load supported symbols:', error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  /**
   * Get current prices from API
   */
  const getCurrentPricesData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const prices = await getCurrentPrices();
      console.log('💰 Current prices fetched:', prices);
      return prices;
    } catch (error) {
      console.error('❌ Failed to get current prices:', error);
      return null;
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  /**
   * Load current prices for specific symbols and update state
   */
  const loadCurrentPrices = useCallback(async (symbols: string[]) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const symbolsParam = symbols.join(',');
      const response = await fetch(`http://localhost:8000/api/exchange/api/v1/market-data/current_prices/?symbols=${symbolsParam}`);
      const prices = await response.json();
      
      // Convert API data to market data format
      const newMarketData: Record<string, WSPriceUpdateMessage> = {};
      for (const [symbol, data] of Object.entries(prices)) {
        if (data) {
          const priceData = data as any;
          newMarketData[symbol] = {
            type: 'price_update',
            symbol: priceData.symbol,
            price: parseFloat(priceData.price),
            change: parseFloat(priceData.change),
            change_percent: parseFloat(priceData.change_percent),
            volume: priceData.volume,
            bid: parseFloat(priceData.bid),
            ask: parseFloat(priceData.ask),
            timestamp: priceData.timestamp
          };
        }
      }
      
      setState(prev => ({ 
        ...prev, 
        marketData: { ...prev.marketData, ...newMarketData }
      }));
      
      console.log('💰 Current prices loaded for symbols:', symbols, newMarketData);
    } catch (error) {
      console.error('❌ Failed to load current prices:', error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  /**
   * Get price for specific symbol
   */
  const getPriceForSymbol = useCallback((symbol: string): WSPriceUpdateMessage | null => {
    return state.marketData[symbol] || null;
  }, [state.marketData]);

  /**
   * Clear market alerts
   */
  const clearAlerts = useCallback(() => {
    setState(prev => ({ ...prev, marketAlerts: [] }));
  }, []);

  /**
   * Clear order history
   */
  const clearOrderHistory = useCallback(() => {
    setState(prev => ({ ...prev, orderHistory: [] }));
  }, []);

  /**
   * Load initial data on mount
   */
  useEffect(() => {
    refreshExchangeStatus();
    loadSupportedSymbols();
  }, [refreshExchangeStatus, loadSupportedSymbols]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    placeOrder,
    refreshMarketData,
    refreshExchangeStatus,
    loadSupportedSymbols,
    getCurrentPrices: getCurrentPricesData,
    loadCurrentPrices,
    getPriceForSymbol,
    clearAlerts,
    clearOrderHistory,
  };
}