# Frontend Overview

## Purpose

This `frontend/` project is a standalone NextJS Kanban demo used as the starting point for the full MVP. It currently runs fully on the client with in-memory state and no backend integration.

## Stack

- NextJS App Router (`next@16`)
- React 19 + TypeScript
- Tailwind CSS v4
- Drag and drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- Unit testing: Vitest + Testing Library
- E2E testing: Playwright
- Static export mode: `next.config.ts` uses `output: "export"` so builds emit `frontend/out`.

## Current App Behavior

- Entry route `/` renders auth-gated `AppShell`.
- Unauthenticated users see login form.
- Demo credentials: `user` / `password`.
- Authenticated users see the Kanban board and can log out.
- Board has 5 columns by default.
- Column titles are editable inline.
- Cards can be added and removed.
- Cards can be reordered within a column and moved across columns with drag/drop.
- Data is seeded from `src/lib/kanban.ts` and stored in React component state only (not persistent).

## Key Files

- `src/app/page.tsx`: app entry route, renders board.
- `src/components/AppShell.tsx`: auth gating and login/logout flow.
- `src/components/KanbanBoard.tsx`: top-level board state and drag/drop orchestration.
- `src/components/KanbanColumn.tsx`: column rendering, rename input, card list, add-card form.
- `src/components/KanbanCard.tsx`: sortable card rendering + delete action.
- `src/components/NewCardForm.tsx`: add-card UI and form state.
- `src/lib/kanban.ts`: board types, initial seed data, card move utility, id generator.
- `src/app/globals.css`: color tokens and base styles aligned with project palette.

## Test Setup

- `src/lib/kanban.test.ts` covers core `moveCard` behavior.
- `src/components/KanbanBoard.test.tsx` covers render/rename/add/remove behaviors.
- `src/components/AppShell.test.tsx` covers session check, login success/failure, and logout.
- `tests/kanban.spec.ts` covers page load, add-card flow, and drag/drop between columns.
- Vitest config: `vitest.config.ts` with `jsdom` environment and coverage reporter enabled.
- Playwright config: `playwright.config.ts` runs against backend server at `127.0.0.1:8000`.

## Commands

- Install: `npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Start: `npm run start`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- All tests: `npm run test:all`

## Known Gaps (Expected for Current Stage)

- No real user system beyond hardcoded demo credentials.
- No board persistence API usage yet (board is still local client state).
- No persistence.
- No AI sidebar/chat.
- No server-side data model alignment yet (board data is still client-side state).
