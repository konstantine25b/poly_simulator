import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import favicon from "../assets/polymarket.jpg";
import "./index.css";
import App from "./App.jsx";

const link = document.createElement("link");
link.rel = "icon";
link.type = "image/jpeg";
link.href = favicon;
document.head.appendChild(link);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
