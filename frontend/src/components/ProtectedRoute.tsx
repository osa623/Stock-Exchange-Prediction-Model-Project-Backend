import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, adminProfile, adminChecked } = useAuth();

  if (loading || !adminChecked) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-900">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  // Firebase user exists but not registered as admin in backend
  if (!adminProfile) return <Navigate to="/register" replace />;

  return <>{children}</>;
}
