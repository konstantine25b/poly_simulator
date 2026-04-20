import { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { AuthForm } from "../components/AuthForm.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import "../auth.css";

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || "/";

  useEffect(() => {
    if (isAuthenticated) navigate(redirectTo, { replace: true });
  }, [isAuthenticated, navigate, redirectTo]);

  const handleSubmit = async (email, password) => {
    await login(email, password);
    navigate(redirectTo, { replace: true });
  };

  return (
    <div className="auth-page">
      <div className="auth-bg" aria-hidden />
      <div className="auth-card">
        <Link to="/" className="auth-back">
          <span aria-hidden>←</span> Back to markets
        </Link>
        <div className="auth-brand">
          <img className="auth-brand-logo" src={polymarketMark} alt="" />
          <span className="auth-brand-name">Poly Simulator</span>
        </div>
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-sub">Log in to manage your paper portfolio and trade history.</p>
        <AuthForm submitLabel="Log in" onSubmit={handleSubmit} />
        <p className="auth-footer">
          New here?
          <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
