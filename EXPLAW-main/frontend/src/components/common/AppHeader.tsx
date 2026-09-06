import React from "react";
import { Link } from "react-router-dom";

export interface Crumb {
  label: string;
  to?: string;
}

/** Contextual breadcrumb trail, shown above a page's content when it's
 * nested more than one level deep. Primary navigation lives in the
 * sidebar, so this renders nothing on top-level pages. */
export default function AppHeader({ crumbs = [] }: { crumbs?: Crumb[] }) {
  if (crumbs.length === 0) return null;

  return (
    <nav className="app-header" aria-label="Breadcrumb">
      <Link to="/">Inbox</Link>
      {crumbs.map((crumb, i) => (
        <React.Fragment key={i}>
          <span aria-hidden="true">/</span>
          {crumb.to ? <Link to={crumb.to}>{crumb.label}</Link> : <span>{crumb.label}</span>}
        </React.Fragment>
      ))}
    </nav>
  );
}
