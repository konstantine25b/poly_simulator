import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { AuthForm } from "../components/AuthForm.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import "../auth.css";

export function RegisterPage() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (email, password) => {
    await register(email, password);
    navigate("/", { replace: true });
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
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-sub">Start trading Polymarkets with a paper balance in seconds.</p>
        <AuthForm
          submitLabel="Create account"
          onSubmit={handleSubmit}
          minPasswordLength={8}
          passwordHint="Minimum 8 characters."
        />
        <p className="auth-footer">
          Already have an account?
          <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
