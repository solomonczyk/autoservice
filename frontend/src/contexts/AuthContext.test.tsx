import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../lib/api';

// Mock the API module
vi.mock('../lib/api', () => ({
    api: {
        defaults: {
            headers: {
                common: {}
            }
        },
        post: vi.fn()
    }
}));

// Test component to consume the context
const TestComponent = () => {
    const { token, login, logout, isAuthenticated } = useAuth();
    return (
        <div>
            <div data-testid="auth-status">{isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</div>
            <div data-testid="token-value">{token}</div>
            <button onClick={() => login('fake-token')}>Login</button>
            <button onClick={logout}>Logout</button>
        </div>
    );
};

describe('AuthContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });

    it('provides initial state from localStorage', () => {
        localStorage.setItem('token', 'stored-token');
        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('token-value')).toHaveTextContent('stored-token');
        expect(api.defaults.headers.common['Authorization']).toBe('Bearer stored-token');
    });

    it('updates state and localStorage on login', () => {
        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');

        act(() => {
            screen.getByText('Login').click();
        });

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
        expect(screen.getByTestId('token-value')).toHaveTextContent('fake-token');
        expect(localStorage.getItem('token')).toBe('fake-token');
        expect(api.defaults.headers.common['Authorization']).toBe('Bearer fake-token');
    });

    it('updates state and localStorage on logout', () => {
        localStorage.setItem('token', 'stored-token');
        render(
            <AuthProvider>
                <TestComponent />
            </AuthProvider>
        );

        act(() => {
            screen.getByText('Logout').click();
        });

        expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
        expect(screen.getByTestId('token-value')).toHaveTextContent('');
        expect(localStorage.getItem('token')).toBeNull();
        expect(api.defaults.headers.common['Authorization']).toBeUndefined();
    });
});
