import { createContext } from "react";
import type { User } from "firebase/auth";

export interface AdminProfile {
  id: number;
  role: "super_admin" | "admin";
  first_name: string;
  last_name: string;
  email: string;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  adminProfile: AdminProfile | null;
  adminChecked: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<import("firebase/auth").UserCredential>;
  signOut: () => Promise<void>;
  recheckAdmin: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
