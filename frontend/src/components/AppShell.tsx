"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";

type SessionResponse = {
  authenticated: boolean;
  username: string | null;
};

type AuthState = "loading" | "authenticated" | "unauthenticated";

export const AppShell = () => {
  const [authState, setAuthState] = useState<AuthState>("loading");
  const [board, setBoard] = useState<BoardData | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const saveTimeoutId = useRef<number | null>(null);
  const lastPersistedBoardJson = useRef<string | null>(null);
  const queuedBoardJson = useRef<string | null>(null);

  const persistBoardJson = useCallback(async (boardJson: string) => {
    const response = await fetch("/api/board", {
      method: "PUT",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: boardJson,
    });

    if (!response.ok) {
      setErrorMessage("Unable to save board changes.");
      return false;
    }

    lastPersistedBoardJson.current = boardJson;
    if (queuedBoardJson.current === boardJson) {
      queuedBoardJson.current = null;
    }
    return true;
  }, []);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch("/api/auth/session", {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error("Unable to check session.");
        }
        const data = (await response.json()) as SessionResponse;
        setAuthState(data.authenticated ? "authenticated" : "unauthenticated");
      } catch {
        setAuthState("unauthenticated");
      }
    };

    void checkSession();
  }, []);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        setErrorMessage("Invalid credentials. Use user / password.");
        return;
      }

      setPassword("");
      setAuthState("authenticated");
    } catch {
      setErrorMessage("Unable to sign in right now.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setErrorMessage("");
    if (saveTimeoutId.current) {
      window.clearTimeout(saveTimeoutId.current);
      saveTimeoutId.current = null;
    }

    const pendingBoardJson = queuedBoardJson.current;
    if (
      authState === "authenticated" &&
      pendingBoardJson &&
      pendingBoardJson !== lastPersistedBoardJson.current
    ) {
      try {
        await persistBoardJson(pendingBoardJson);
      } catch {
        setErrorMessage("Unable to save board changes.");
      }
    }

    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    setBoard(null);
    queuedBoardJson.current = null;
    lastPersistedBoardJson.current = null;
    setAuthState("unauthenticated");
  };

  useEffect(() => {
    if (authState !== "authenticated") {
      return;
    }

    const loadBoard = async () => {
      try {
        const response = await fetch("/api/board", {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error("Unable to load board.");
        }
        const nextBoard = (await response.json()) as BoardData;
        if (saveTimeoutId.current) {
          window.clearTimeout(saveTimeoutId.current);
          saveTimeoutId.current = null;
        }
        lastPersistedBoardJson.current = JSON.stringify(nextBoard);
        queuedBoardJson.current = null;
        setBoard(nextBoard);
      } catch {
        setErrorMessage("Unable to load board right now.");
        setAuthState("unauthenticated");
      }
    };

    void loadBoard();
  }, [authState]);

  useEffect(() => {
    return () => {
      if (saveTimeoutId.current) {
        window.clearTimeout(saveTimeoutId.current);
      }
    };
  }, []);

  const handleBoardUpdated = useCallback(
    (nextBoard: BoardData) => {
      setBoard(nextBoard);

      if (authState !== "authenticated") {
        return;
      }

      const boardJson = JSON.stringify(nextBoard);
      if (boardJson === lastPersistedBoardJson.current) {
        queuedBoardJson.current = null;
        return;
      }
      queuedBoardJson.current = boardJson;

      if (saveTimeoutId.current) {
        window.clearTimeout(saveTimeoutId.current);
      }

      saveTimeoutId.current = window.setTimeout(() => {
        const queued = queuedBoardJson.current;
        if (!queued || queued === lastPersistedBoardJson.current) {
          return;
        }
        void persistBoardJson(queued);
      }, 300);
    },
    [authState, persistBoardJson]
  );

  if (authState === "loading") {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-lg items-center justify-center px-6 text-center text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
        Loading session...
      </main>
    );
  }

  if (authState === "authenticated") {
    if (!board) {
      return (
        <main className="mx-auto flex min-h-screen w-full max-w-lg items-center justify-center px-6 text-center text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Loading board...
        </main>
      );
    }

    return (
      <>
        {errorMessage ? (
          <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--secondary-purple)] shadow-[var(--shadow)]">
            {errorMessage}
          </div>
        ) : null}
        <KanbanBoard
          onLogout={handleLogout}
          initialBoard={board}
          onBoardUpdated={handleBoardUpdated}
        />
      </>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-screen w-full max-w-lg items-center px-6 py-10">
      <div className="w-full rounded-3xl border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
          Project Management MVP
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Sign in
        </h1>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Use the demo credentials to access your board.
        </p>

        <form onSubmit={handleLogin} className="mt-7 space-y-4">
          <label className="block text-left">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Username
            </span>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              autoComplete="username"
              placeholder="user"
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </label>

          <label className="block text-left">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Password
            </span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              placeholder="password"
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </label>

          {errorMessage ? (
            <p className="text-sm font-semibold text-[var(--secondary-purple)]">
              {errorMessage}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-5 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]">
          Demo credentials: user / password
        </p>
      </div>
    </main>
  );
};
