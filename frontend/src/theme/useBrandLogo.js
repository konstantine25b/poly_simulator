import polymarketMarkDark from "../../assets/polymarket.jpg";
import polymarketMarkLight from "../../assets/polymarket-white.jpg";
import { useTheme } from "./ThemeContext.jsx";

export function useBrandLogo() {
  const { theme } = useTheme();
  return theme === "light" ? polymarketMarkLight : polymarketMarkDark;
}
