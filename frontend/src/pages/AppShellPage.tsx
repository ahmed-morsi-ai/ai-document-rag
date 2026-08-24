import { useEffect, useState } from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

function ChatIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path
        d="M7 18.5 4.5 21l.6-4A7.5 7.5 0 0 1 4 12.5C4 8.36 7.58 5 12 5s8 3.36 8 7.5-3.58 7.5-8 7.5c-1.77 0-3.42-.54-5-1.5Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function DocumentsIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path
        d="M7 3.75h7.25L19 8.5v11.75H7A2.25 2.25 0 0 1 4.75 18V6A2.25 2.25 0 0 1 7 3.75Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M14 3.75V8.5h5M8.5 12h7M8.5 15.5h7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path
        d="M12 5v14M5 12h14"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path
        d="M4 7h16M4 12h16M4 17h16"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function AppShellPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [isNavOpen, setIsNavOpen] = useState(false);

  useEffect(() => {
    setIsNavOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="app-shell-topbar">
        <div className="app-shell-topbar-inner">
          <button
            type="button"
            className="icon-button shell-menu-button"
            aria-label="Open navigation"
            aria-expanded={isNavOpen}
            onClick={() => setIsNavOpen((current) => !current)}
          >
            <MenuIcon />
          </button>

          <NavLink
            to="/app"
            className="app-brand"
            aria-label="AI Document RAG home"
          >
            <span className="app-brand-mark">A</span>

            <span className="app-brand-copy">
              <span className="app-brand-name">AI Document RAG</span>
              <span className="app-brand-subtitle">Document workspace</span>
            </span>
          </NavLink>

          <div className="app-shell-topbar-meta">
            <span className="app-shell-topbar-user">
              {user?.email}
            </span>
          </div>
        </div>
      </header>

      <div className="app-shell-layout">
        <aside
          className={`app-shell-sidebar${
            isNavOpen ? " is-open" : ""
          }`}
          aria-label="Application navigation"
        >
          <div className="app-shell-sidebar-scroll">
            <div className="app-shell-sidebar-section">
              <NavLink
                to="/app/chat"
                className="shell-new-chat"
              >
                <PlusIcon />
                <span>New Chat</span>
              </NavLink>
            </div>

            <nav
              className="app-shell-nav"
              aria-label="Primary"
            >
              <p className="app-shell-nav-label">
                Workspace
              </p>

              <NavLink
                to="/app/chat"
                className={({ isActive }) =>
                  `app-shell-nav-link${
                    isActive ? " is-active" : ""
                  }`
                }
              >
                <ChatIcon />
                <span>Chat</span>
              </NavLink>

              <NavLink
                to="/app"
                end
                className={({ isActive }) =>
                  `app-shell-nav-link${
                    isActive ? " is-active" : ""
                  }`
                }
              >
                <DocumentsIcon />
                <span>Documents</span>
              </NavLink>
            </nav>
          </div>

          <div className="app-shell-sidebar-footer">
            <div className="app-shell-user">
              <div className="app-shell-user-avatar" aria-hidden="true">
                {user?.email?.slice(0, 1).toUpperCase() || "U"}
              </div>

              <div className="app-shell-user-copy">
                <strong>{user?.email}</strong>
                <span>Signed in</span>
              </div>
            </div>

            <button
              type="button"
              className="shell-logout"
              aria-label="Log out from application"
              onClick={handleLogout}
            >
              Log out
            </button>
          </div>
        </aside>

        {isNavOpen ? (
          <button
            type="button"
            className="app-shell-overlay"
            aria-label="Close navigation"
            onClick={() => setIsNavOpen(false)}
          />
        ) : null}

        <main className="app-shell-main">
          <div className="app-shell-content">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
