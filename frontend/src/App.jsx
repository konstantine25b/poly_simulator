import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Footer } from "./components/Footer.jsx";
import { Navbar } from "./components/Navbar.jsx";
import { RequireAuth } from "./features/auth/components/RequireAuth.jsx";
import { AuthProvider } from "./features/auth/context/AuthContext.jsx";
import { LoginPage } from "./features/auth/pages/LoginPage.jsx";
import { PortfolioDetailPage } from "./features/auth/pages/PortfolioDetailPage.jsx";
import { ProfilePage } from "./features/auth/pages/ProfilePage.jsx";
import { RegisterPage } from "./features/auth/pages/RegisterPage.jsx";
import { MarketsPage } from "./features/markets/MarketsPage.jsx";
import { MarketDetailPage } from "./features/markets/pages/MarketDetailPage.jsx";

const HIDE_NAV_ROUTES = ["/login", "/register"];

function AppShell({ children }) {
  const { pathname } = useLocation();
  const hideNav = HIDE_NAV_ROUTES.includes(pathname);
  return (
    <div className="app-root">
      {hideNav ? null : <Navbar />}
      <div className="app-main">{children}</div>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<MarketsPage />} />
            <Route path="/m/:marketRef" element={<MarketDetailPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/profile"
              element={
                <RequireAuth>
                  <ProfilePage />
                </RequireAuth>
              }
            />
            <Route
              path="/portfolios/:portfolioId"
              element={
                <RequireAuth>
                  <PortfolioDetailPage />
                </RequireAuth>
              }
            />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </AuthProvider>
  );
}
