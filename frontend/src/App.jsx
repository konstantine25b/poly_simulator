import { BrowserRouter, Route, Routes } from "react-router-dom";
import { MarketsPage } from "./features/markets/MarketsPage.jsx";
import { MarketDetailPage } from "./features/markets/pages/MarketDetailPage.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MarketsPage />} />
        <Route path="/m/:marketRef" element={<MarketDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}
