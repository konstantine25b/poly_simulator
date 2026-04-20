import { BrowserRouter, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./features/auth/components/RequireAuth.jsx";
import { AuthProvider } from "./features/auth/context/AuthContext.jsx";
import { LoginPage } from "./features/auth/pages/LoginPage.jsx";
import { ProfilePage } from "./features/auth/pages/ProfilePage.jsx";
import { RegisterPage } from "./features/auth/pages/RegisterPage.jsx";
import { MarketsPage } from "./features/markets/MarketsPage.jsx";
import { MarketDetailPage } from "./features/markets/pages/MarketDetailPage.jsx";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
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
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
