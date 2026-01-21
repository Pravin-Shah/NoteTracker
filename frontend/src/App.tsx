import NotesLayout from './components/notes/NotesLayout';
import { LoginPage } from './components/auth/LoginPage';
import { useAuth } from './context/AuthContext';

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen bg-[#121212] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return user ? <NotesLayout /> : <LoginPage />;
}

export default App;
