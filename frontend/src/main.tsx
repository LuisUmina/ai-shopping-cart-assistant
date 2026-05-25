import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { LandingPage } from "./components/LandingPage.tsx";

function Root() {
  const [entered, setEntered] = useState(false);
  const [exiting, setExiting] = useState(false);

  function handleEnter() {
    setExiting(true);
    setTimeout(() => setEntered(true), 500);
  }

  if (entered) return <App />;

  return (
    <div
      style={{
        opacity: exiting ? 0 : 1,
        transition: "opacity 0.5s ease",
      }}
    >
      <LandingPage onEnter={handleEnter} />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>
);
