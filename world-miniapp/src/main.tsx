import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import MiniKitProvider from "./minikit-provider.tsx";
import { StrictMode } from "react";
import { ErudaProvider } from "./components/Eruda";

import "./index.css";
import "./font.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErudaProvider>
      <MiniKitProvider>
        <App />
      </MiniKitProvider>
    </ErudaProvider>
  </StrictMode>
);
