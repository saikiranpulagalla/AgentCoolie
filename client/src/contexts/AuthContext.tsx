import { createContext, useContext, useEffect, useState } from "react";
import {
  User,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  updateProfile,
} from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, displayName: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const authInstance = getFirebaseAuth();
    if (!authInstance) {
      // Only allow test user in development mode
      if (process.env.NODE_ENV === 'development') {
        console.warn("Firebase auth not initialized; creating test user for development only");
        const mockUser = {
          uid: "test-user-123",
          email: "test@example.com",
          displayName: "Test User",
          emailVerified: true,
        } as any;
        setUser(mockUser);
        localStorage.setItem('userId', 'test-user-123');
        setLoading(false);
        return;
      } else {
        console.error("Firebase auth not initialized in production - authentication required");
        setUser(null);
        setLoading(false);
        return;
      }
    }

    const unsubscribe = onAuthStateChanged(authInstance, (user) => {
      setUser(user);
      try {
        if (user) {
          localStorage.setItem('userId', user.uid);
        } else {
          localStorage.removeItem('userId');
        }
      } catch (e) {
        // ignore storage errors
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signUp = async (email: string, password: string, displayName: string) => {
    try {
      const authInstance = getFirebaseAuth();
      if (!authInstance) {
        // Create mock user for testing
        console.warn("Firebase not initialized - using test user");
        const mockUser = {
          uid: `test-${Date.now()}`,
          email,
          displayName,
          emailVerified: false,
        } as any;
        setUser(mockUser);
        localStorage.setItem('userId', mockUser.uid);
        return;
      }

      const userCredential = await createUserWithEmailAndPassword(authInstance, email, password);
      await updateProfile(userCredential.user, { displayName });
      setUser(userCredential.user);
    } catch (error) {
      console.error("Sign up error:", error);
      throw error;
    }
  };

  const getIdToken = async () => {
    const authInstance = getFirebaseAuth();
    if (!authInstance) {
      // Return a dummy token for testing
      return "test-token-" + Date.now();
    }
    const current = authInstance.currentUser;
    if (!current) return null;
    try {
      return await current.getIdToken();
    } catch (err) {
      console.error('Failed to get ID token', err);
      return null;
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const authInstance = getFirebaseAuth();
      if (!authInstance) {
        // Create mock user for testing
        console.warn("Firebase not initialized - using test user");
        const mockUser = {
          uid: `test-${Date.now()}`,
          email,
          displayName: email.split("@")[0],
          emailVerified: false,
        } as any;
        setUser(mockUser);
        localStorage.setItem('userId', mockUser.uid);
        return;
      }

      await signInWithEmailAndPassword(authInstance, email, password);
    } catch (error) {
      console.error("Sign in error:", error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      const authInstance = getFirebaseAuth();
      if (!authInstance) {
        // For test user, just clear state
        setUser(null);
        localStorage.removeItem('userId');
        return;
      }

      await firebaseSignOut(authInstance);
    } catch (error) {
      console.error("Sign out error:", error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut, getIdToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
