import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../../context/AuthContext';
import { LogIn } from 'lucide-react';

export const LoginPage: React.FC = () => {
    const { loginWithGoogle } = useAuth();
    const [error, setError] = React.useState<string | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);

    const googleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setIsLoading(true);
            try {
                // Exchange access token for user info
                const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                    headers: { Authorization: `Bearer ${tokenResponse.access_token}` }
                });
                await userInfoResponse.json();

                // Use the access token directly for login
                await loginWithGoogle(tokenResponse.access_token);
            } catch (err) {
                setError('Login failed. Please try again.');
                setIsLoading(false);
            }
        },
        onError: () => setError('Google login failed'),
        flow: 'implicit',
    });

    return (
        <div className="min-h-screen bg-[#121212] flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md bg-[#1a1a1a] border border-gray-800 rounded-2xl p-8 shadow-2xl text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-900/20">
                    <LogIn className="text-white w-8 h-8" />
                </div>

                <h1 className="text-3xl font-bold text-white mb-2">NoteTracker</h1>
                <p className="text-gray-400 mb-8">Personal Knowledge & Task Management</p>

                {error && (
                    <div className="mb-6 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400 text-sm">
                        {error}
                    </div>
                )}

                <button
                    onClick={() => googleLogin()}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-100 text-gray-800 font-medium py-3 px-6 rounded-full transition-colors disabled:opacity-50"
                >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    {isLoading ? 'Signing in...' : 'Continue with Google'}
                </button>

                <p className="mt-8 text-[11px] text-gray-500">
                    By signing in, you agree to store your notes on our secure server.
                </p>
            </div>
        </div>
    );
};
