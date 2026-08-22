import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppShellPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <main className="shell-page">
      <header className="shell-header">
        <div>
          <p className="eyebrow">AI Document RAG</p>
          <h1>Authenticated application shell</h1>
        </div>

        <button type="button" className="secondary" onClick={handleLogout}>
          Log out
        </button>
      </header>

      <section className="shell-card">
        <h2>Authentication is working</h2>
        <p className="muted">
          Signed in as <strong>{user?.email}</strong>.
        </p>

        <nav aria-label="Future application areas">
          <span>Dashboard</span>
          <span>Documents</span>
          <span>Chat</span>
          <span>Conversation History</span>
        </nav>

        <p className="muted">
          These areas are intentionally placeholders for later tasks.
        </p>
      </section>
    </main>
  );
}
