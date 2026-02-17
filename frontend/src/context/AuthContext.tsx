import { useEffect, useState, useCallback, type ReactNode } from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { auth } from "../config/firebase";
import { AuthContext, type AdminProfile } from "./AuthContextDef";
import { adminAuthApi } from "../services/api";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [adminProfile, setAdminProfile] = useState<AdminProfile | null>(null);
  const [adminChecked, setAdminChecked] = useState(false);

  const checkAdmin = useCallback(async (firebaseUser: User | null) => {
    if (!firebaseUser) {
      setAdminProfile(null);
      setAdminChecked(true);
      return;
    }
    try {
      const res = await adminAuthApi.getMe();
      setAdminProfile({
        id: res.data.id,
        role: res.data.role,
        first_name: res.data.first_name,
        last_name: res.data.last_name,
        email: res.data.email,
      });
    } catch {
      setAdminProfile(null);
    } finally {
      setAdminChecked(true);
    }
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
      setAdminChecked(false);
      checkAdmin(u);
    });
    return unsubscribe;
  }, [checkAdmin]);

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  const signUp = async (email: string, password: string) => {
    return createUserWithEmailAndPassword(auth, email, password);
  };

  const signOut = async () => {
    setAdminProfile(null);
    setAdminChecked(false);
    await firebaseSignOut(auth);
  };

  const recheckAdmin = useCallback(async () => {
    setAdminChecked(false);
    await checkAdmin(user);
  }, [checkAdmin, user]);

  return (
    <AuthContext.Provider
      value={{ user, loading, adminProfile, adminChecked, signIn, signUp, signOut, recheckAdmin }}
    >
      {children}
    </AuthContext.Provider>
  );
}
