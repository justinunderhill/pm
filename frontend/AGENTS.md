# Frontend Overview

## Stack

- NextJS App Router (`next@16`)
- React 19 + TypeScript
- Tailwind CSS v4
- Drag/drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- Unit tests: Vitest + Testing Library
- E2E tests: Playwright

## Current App Behavior

- Entry route `/` renders `AppShell`.
- Unauthenticated users see login form.
- Demo credentials: `user` / `password`.
- Authenticated users see:
  - full Kanban board (backend-backed persistence via `GET/PUT /api/board`)
  - AI sidebar chat (`POST /api/ai/chat`, `GET /api/ai/history`)
  - logout action
- Board interactions supported:
  - rename columns
  - add/edit/delete cards
  - drag/drop move cards
- Board saves use optimistic local updates + debounced autosave.
- AI responses can optionally return a board update; UI applies it immediately.

## Key Files

- `src/components/AppShell.tsx`: auth flow, board load/save orchestration, AI history load, AI send/receive flow.
- `src/components/KanbanBoard.tsx`: board UI, drag/drop orchestration, responsive board + sidebar layout.
- `src/components/AISidebar.tsx`: AI chat sidebar UI and message form.
- `src/components/KanbanColumn.tsx`: column rendering, rename input, card list, add-card form.
- `src/components/KanbanCard.tsx`: card rendering, inline edit, delete action.
- `src/lib/kanban.ts`: board types, initial data, move utility, id generation.

## Tests

- `src/components/AppShell.test.tsx`: auth gating, board API behavior, AI chat flow and board refresh.
- `src/components/AISidebar.test.tsx`: sidebar interactions and message rendering.
- `src/components/KanbanBoard.test.tsx`: board interactions.
- `src/lib/kanban.test.ts`: move utility behavior.
- `tests/kanban.spec.ts`: end-to-end auth + board + AI sidebar flows against backend.

## Commands

- Install: `npm install`
- Build: `npm run build`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- Full frontend suite: `npm run test:all`
