import { useState, useEffect, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { adminAuthApi } from "../services/api";
import { Shield, UserPlus, AlertCircle, CheckCircle, LogIn } from "lucide-react";

export default function RegisterPage() {
  const { user, signUp, signIn, adminProfile, recheckAdmin } = useAuth();
  const navigate = useNavigate();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [registrationOpen, setRegistrationOpen] = useState(false);
  const [statusError, setStatusError] = useState("");

  // If user is already an admin, redirect to dashboard
  useEffect(() => {
    if (adminProfile) {
      navigate("/", { replace: true });
    }
  }, [adminProfile, navigate]);

  // Pre-fill email from Firebase user if already logged in
  useEffect(() => {
    if (user?.email && !email) {
      setEmail(user.email);
    }
  }, [user, email]);

  // Check if self-registration is open
  useEffect(() => {
    adminAuthApi
      .getRegistrationStatus()
      .then((res) => {
        setRegistrationOpen(res.data.registration_open);
      })
      .catch((err) => {
        console.error("Failed to check registration status:", err);
        setRegistrationOpen(true);
        setStatusError(
          "Could not verify registration status. Make sure the backend is running."
        );
      })
      .finally(() => setCheckingStatus(false));
  }, []);

  // Already logged in → only need to complete backend registration
  const alreadyLoggedIn = !!user;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate password fields only if not already logged in
    if (!alreadyLoggedIn) {
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }
    }

    setLoading(true);
    try {
      // Step 1: Ensure Firebase auth
      if (!alreadyLoggedIn) {
        try {
          // Try creating a new Firebase account
          await signUp(email, password);
        } catch (fbErr: unknown) {
          const msg = fbErr instanceof Error ? fbErr.message : "";
          if (msg.includes("email-already-in-use")) {
            // Account exists — sign in instead
            try {
              await signIn(email, password);
            } catch {
              setError(
                "This email is already registered. Please use the correct password or sign in from the login page."
              );
              return;
            }
          } else {
            throw fbErr;
          }
        }
      }

      // Step 2: Register as admin in the backend
      await adminAuthApi.register({
        first_name: firstName,
        last_name: lastName,
        email,
        phone_number: phone || undefined,
      });

      // Step 3: Refresh admin profile in context
      await recheckAdmin();

      // Navigate to dashboard
      navigate("/", { replace: true });
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const resp = (err as { response?: { data?: { detail?: string } } })
          .response;
        setError(resp?.data?.detail || "Registration failed.");
      } else {
        const msg =
          err instanceof Error ? err.message : "Registration failed.";
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  if (checkingStatus) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
      </div>
    );
  }

  if (!registrationOpen) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4">
        <div className="w-full max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-yellow-500/10">
            <AlertCircle className="h-8 w-8 text-yellow-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">
            Registration Closed
          </h1>
          <p className="mt-3 text-sm text-gray-400">
            An admin already exists. New admins must be invited by an existing
            administrator.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block rounded-lg bg-cyan-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-cyan-500"
          >
            Go to Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md">
        {/* Branding */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-500/10">
            <Shield className="h-8 w-8 text-cyan-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">Admin Registration</h1>
          <p className="mt-1 text-sm text-gray-500">
            {alreadyLoggedIn
              ? "Complete your admin profile"
              : "Create the first super-admin account"}
          </p>
        </div>

        {/* Info banner */}
        {statusError ? (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-yellow-500/10 px-4 py-3 text-sm text-yellow-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {statusError}
          </div>
        ) : (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-cyan-500/10 px-4 py-3 text-sm text-cyan-400">
            <CheckCircle className="h-4 w-4 shrink-0" />
            {alreadyLoggedIn
              ? `Signed in as ${user?.email}. Complete the form below to register as super admin.`
              : "No admins found. You will be registered as the super admin."}
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-gray-800 bg-gray-900 p-8 shadow-xl"
        >
          <h2 className="mb-6 text-lg font-semibold text-white">
            {alreadyLoggedIn ? "Complete Registration" : "Create Account"}
          </h2>

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-400">
                First Name
              </label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                placeholder="John"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-400">
                Last Name
              </label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                placeholder="Doe"
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </div>

          {!alreadyLoggedIn && (
            <>
              <label className="mb-1 block text-sm font-medium text-gray-400">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mb-4 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="admin@example.com"
              />
            </>
          )}

          <label className="mb-1 block text-sm font-medium text-gray-400">
            Phone Number{" "}
            <span className="text-gray-600">(optional)</span>
          </label>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mb-4 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            placeholder="+1 234 567 8900"
          />

          {!alreadyLoggedIn && (
            <>
              <label className="mb-1 block text-sm font-medium text-gray-400">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="mb-4 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="••••••••"
              />

              <label className="mb-1 block text-sm font-medium text-gray-400">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
                className="mb-6 w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="••••••••"
              />
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-cyan-500 disabled:opacity-50"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <>
                {alreadyLoggedIn ? (
                  <LogIn className="h-4 w-4" />
                ) : (
                  <UserPlus className="h-4 w-4" />
                )}
                {alreadyLoggedIn
                  ? "Complete Registration"
                  : "Create Super Admin"}
              </>
            )}
          </button>
        </form>

        {!alreadyLoggedIn && (
          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link to="/login" className="text-cyan-400 hover:text-cyan-300">
              Sign in
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
