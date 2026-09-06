import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/common/Sidebar";
import InboxList from "./components/Inbox/InboxList";
import ChangeSummary from "./components/ChangeDetail/ChangeSummary";
import DocumentViewer from "./components/DocumentReview/DocumentViewer";
import DocumentsPage from "./components/Documents/DocumentsPage";

/**
 * Stage 2: inbox is the default/home view (list of changes).
 * Stage 2 continued: clicking a change opens ChangeSummary.
 * Stage 3/4: clicking a document within a change opens DocumentViewer.
 * /documents: onboarding firm document templates (not part of the
 * numbered workflow stages - a prerequisite for Stage 2 matching).
 */
export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <div className="app-shell__content">
          <Routes>
            <Route path="/" element={<InboxList />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/changes/:changeId" element={<ChangeSummary />} />
            <Route
              path="/changes/:changeId/documents/:documentId"
              element={<DocumentViewer />}
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
