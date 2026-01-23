import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

interface User {
    id: number;
    email: string;
    name: string;
    picture: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    loginWithGoogle: (googleToken: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auto-logout timeout in milliseconds (10 minutes)
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Logout function (defined early for use in activity tracking)
    const performLogout = useCallback(() => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
    }, []);

    // Reset inactivity timer
    const resetInactivityTimer = useCallback(() => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        // Only set timeout if user is logged in
        if (token) {
            timeoutRef.current = setTimeout(() => {
                console.log('Session expired due to inactivity');
                performLogout();
            }, INACTIVITY_TIMEOUT);
        }
    }, [token, performLogout]);

    // Track user activity
    useEffect(() => {
        if (!token) return;

        const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart'];

        const handleActivity = () => {
            resetInactivityTimer();
        };

        // Add event listeners
        activityEvents.forEach(event => {
            window.addEventListener(event, handleActivity);
        });

        // Start the timer
        resetInactivityTimer();

        // Cleanup
        return () => {
            activityEvents.forEach(event => {
                window.removeEventListener(event, handleActivity);
            });
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, [token, resetInactivityTimer]);

    useEffect(() => {
        // Check for existing session
        const savedToken = localStorage.getItem('auth_token');
        const savedUser = localStorage.getItem('auth_user');

        if (savedToken && savedUser) {
            setToken(savedToken);
            setUser(JSON.parse(savedUser));
        }
        setIsLoading(false);
    }, []);

    const loginWithGoogle = async (googleToken: string) => {
        try {
            const response = await axios.post('/api/auth/google', { token: googleToken });
            const { access_token, user: userData } = response.data;

            setToken(access_token);
            setUser(userData);

            localStorage.setItem('auth_token', access_token);
            localStorage.setItem('auth_user', JSON.stringify(userData));
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    const logout = () => {
        performLogout();
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, loginWithGoogle, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
