"use client";

import { FormEvent, useMemo, useState } from "react";

export type AIChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type AISidebarProps = {
  messages: AIChatMessage[];
  isLoading: boolean;
  isSubmitting: boolean;
  errorMessage: string;
  onSendMessage: (message: string) => Promise<void> | void;
};

const roleLabel = (role: AIChatMessage["role"]) =>
  role === "assistant" ? "Assistant" : "You";

export const AISidebar = ({
  messages,
  isLoading,
  isSubmitting,
  errorMessage,
  onSendMessage,
}: AISidebarProps) => {
  const [draftMessage, setDraftMessage] = useState("");
  const canSubmit = useMemo(
    () => !isSubmitting && draftMessage.trim().length > 0,
    [draftMessage, isSubmitting]
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = draftMessage.trim();
    if (!message || isSubmitting) {
      return;
    }
    setDraftMessage("");
    await onSendMessage(message);
  };

  return (
    <aside className="flex h-full min-h-[480px] flex-col rounded-3xl border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
      <div className="border-b border-[var(--stroke)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
          Plan with AI
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Ask the assistant to create, edit, or move cards and summarize next actions.
        </p>
      </div>

      <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1" aria-live="polite">
        {isLoading ? (
          <p className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--gray-text)]">
            Loading chat history...
          </p>
        ) : null}

        {!isLoading && messages.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[var(--stroke)] px-4 py-6 text-sm text-[var(--gray-text)]">
            No messages yet. Ask the assistant to help with this board.
          </p>
        ) : null}

        {!isLoading
          ? messages.map((message, index) => (
              <article
                key={`${message.role}-${index}-${message.content.slice(0, 24)}`}
                className="rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3"
                data-testid={`ai-message-${index}`}
              >
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
                  {roleLabel(message.role)}
                </p>
                <p className="mt-2 text-sm leading-6 text-[var(--navy-dark)]">
                  {message.content}
                </p>
              </article>
            ))
          : null}
      </div>

      {errorMessage ? (
        <p className="mt-4 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm font-semibold text-[var(--secondary-purple)]">
          {errorMessage}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label className="block text-left">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Message AI
          </span>
          <textarea
            value={draftMessage}
            onChange={(event) => setDraftMessage(event.target.value)}
            rows={4}
            placeholder="Example: Move card-3 to In Progress and summarize blockers."
            aria-label="Message AI"
            className="mt-2 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm leading-6 text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          />
        </label>
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Thinking..." : "Send"}
        </button>
      </form>
    </aside>
  );
};
