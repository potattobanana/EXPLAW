import React from "react";
import { NavLink } from "react-router-dom";

function InboxIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 12h4l2 3h4l2-3h4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 12 6 5h12l2 7v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-6Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DocumentsIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 3v4h4M9 12h6M9 16h6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const NAV_ITEMS: { to: string; label: string; icon: React.ReactNode; end?: boolean }[] = [
  { to: "/", label: "Inbox", icon: <InboxIcon />, end: true },
  { to: "/documents", label: "Documents", icon: <DocumentsIcon /> },
];

/** Persistent left-hand navigation, shown on every page. */
export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">xplaw</div>
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => "sidebar__link" + (isActive ? " sidebar__link--active" : "")}
          >
            <span className="sidebar__icon" aria-hidden="true">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
