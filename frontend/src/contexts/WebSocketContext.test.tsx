import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { WebSocketProvider, useWebSocket } from '@/contexts/WebSocketContext';

// Mock WebSocket
class MockWebSocket {
    url: string;
    onopen: () => void = () => { };
    onmessage: (event: any) => void = () => { };
    onclose: () => void = () => { };
    send: (data: any) => void = vi.fn();
    close: () => void = vi.fn();
    readyState: number = WebSocket.CONNECTING;

    constructor(url: string) {
        this.url = url;
        setTimeout(() => {
            this.readyState = WebSocket.OPEN;
            this.onopen();
        }, 10);
    }
}

global.WebSocket = MockWebSocket as any;

const TestComponent = () => {
    const { isConnected, lastMessage } = useWebSocket();
    return (
        <div>
            <div data-testid="status">{isConnected ? 'Connected' : 'Disconnected'}</div>
            <div data-testid="message">{lastMessage ? JSON.stringify(lastMessage) : 'No message'}</div>
        </div>
    );
};

describe('WebSocketProvider', () => {
    it('connects to websocket', async () => {
        render(
            <WebSocketProvider url="ws://localhost:8000/ws">
                <TestComponent />
            </WebSocketProvider>
        );

        // Initial state
        expect(screen.getByTestId('status')).toHaveTextContent('Disconnected');

        // Wait for connection simulation
        await new Promise(r => setTimeout(r, 20));

        // Should be connected
        expect(screen.getByTestId('status')).toHaveTextContent('Connected');
    });
});
