"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface SyncStatusEvent {
  source: string;
  status: "started" | "completed" | "failed";
  records_synced?: number;
  error?: string;
}

interface TransactionEvent {
  source: string;
  transaction_id: string;
  status: string;
  amount?: number;
}

export function useWebSocket() {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus("connecting");

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        console.log("[WebSocket] Connected");
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle different message types
          switch (message.type) {
            case "sync_started":
            case "sync_completed":
            case "sync_failed":
              // Invalidate sync status query
              queryClient.invalidateQueries({ queryKey: ["sync", "status"] });
              break;

            case "new_transaction":
            case "transaction_updated":
              // Invalidate transactions and metrics
              queryClient.invalidateQueries({ queryKey: ["transactions"] });
              queryClient.invalidateQueries({ queryKey: ["metrics"] });
              break;

            case "reconciliation_completed":
              // Invalidate reconciliation queries
              queryClient.invalidateQueries({ queryKey: ["reconciliation"] });
              break;

            default:
              console.log("[WebSocket] Unknown message type:", message.type);
          }
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      ws.onerror = (error) => {
        setStatus("error");
        console.error("[WebSocket] Error:", error);
      };

      ws.onclose = (event) => {
        setStatus("disconnected");
        console.log("[WebSocket] Disconnected:", event.code, event.reason);

        // Reconnect after 5 seconds if not intentionally closed
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("[WebSocket] Reconnecting...");
            connect();
          }, 5000);
        }
      };
    } catch (error) {
      setStatus("error");
      console.error("[WebSocket] Connection error:", error);
    }
  }, [queryClient]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected");
      wsRef.current = null;
    }
    setStatus("disconnected");
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("[WebSocket] Cannot send - not connected");
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    status,
    lastMessage,
    connect,
    disconnect,
    send,
    isConnected: status === "connected",
  };
}

// Hook for displaying connection status indicator
export function useWebSocketStatus() {
  const { status, isConnected, lastMessage } = useWebSocket();

  return {
    status,
    isConnected,
    statusColor: {
      connecting: "text-yellow-500",
      connected: "text-green-500",
      disconnected: "text-gray-500",
      error: "text-red-500",
    }[status],
    statusText: {
      connecting: "Connecting...",
      connected: "Live",
      disconnected: "Disconnected",
      error: "Connection Error",
    }[status],
    lastMessage,
  };
}
