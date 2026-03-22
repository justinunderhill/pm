import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/AppShell";
import { initialData } from "@/lib/kanban";

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const boardFixture = () => JSON.parse(JSON.stringify(initialData));

describe("AppShell", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("shows the sign-in form when there is no session", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, { authenticated: false, username: null })
    );

    render(<AppShell />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  it("falls back to sign-in when session check fails", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockRejectedValueOnce(new Error("network"));

    render(<AppShell />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  it("signs in successfully and renders the board", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(200, { authenticated: false, username: null })
      )
      .mockResolvedValueOnce(jsonResponse(200, { username: "user" }))
      .mockResolvedValueOnce(jsonResponse(200, boardFixture()));

    render(<AppShell />);

    await userEvent.type(await screen.findByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(
      await screen.findByRole("heading", { name: /kanban studio/i })
    ).toBeVisible();
    expect(screen.getByRole("button", { name: /log out/i })).toBeVisible();
  });

  it("shows an error for invalid credentials", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(200, { authenticated: false, username: null })
      )
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Invalid credentials." }));

    render(<AppShell />);

    await userEvent.type(await screen.findByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(
      await screen.findByText(/invalid credentials\. use user \/ password\./i)
    ).toBeVisible();
  });

  it("logs out and returns to sign-in", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(200, { authenticated: true, username: "user" })
      )
      .mockResolvedValueOnce(jsonResponse(200, boardFixture()))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    render(<AppShell />);

    await userEvent.click(
      await screen.findByRole("button", { name: /log out/i })
    );

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  it("returns to sign-in if board load fails after auth", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(200, { authenticated: true, username: "user" })
      )
      .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }));

    render(<AppShell />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeVisible();
    expect(screen.getByText(/unable to load board right now\./i)).toBeVisible();
  });

  it("shows an error when board save fails", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(200, { authenticated: true, username: "user" })
      )
      .mockResolvedValueOnce(jsonResponse(200, boardFixture()))
      .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }));

    render(<AppShell />);

    const firstColumnInput = (await screen.findAllByLabelText(/column title/i))[0];
    await userEvent.clear(firstColumnInput);
    await userEvent.type(firstColumnInput, "Unsaveable Backlog");

    await waitFor(() => {
      expect(
        screen.getByText(/unable to save board changes\./i)
      ).toBeInTheDocument();
    });
  });
});
