# NYX Web Portal (Week 02)

Purpose
- Provide a deterministic, evidence-driven web portal shell for Q8.

Scope
- Static HTML/CSS only.
- Navigation routes for Home, World, Exchange, Chat, Marketplace, Entertainment, Trust, Protocol Library.

Non-Scope
- No live system data.
- No accounts, identity, or wallet features.
- No protocol semantics or fee logic.

Run (Dev)
- Serve the static directory and open the home route:
  - python -m http.server --directory apps/nyx-web/static 8081
  - http://localhost:8081/home/

UI Rules
- Evidence fields are displayed verbatim from the backend.
- Preview banner is required on every page.
- No live operational claims.
