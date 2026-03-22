import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AISidebar } from "@/components/AISidebar";

describe("AISidebar", () => {
  it("renders empty state and sends a message", async () => {
    const onSendMessage = vi.fn().mockResolvedValue(undefined);
    render(
      <AISidebar
        messages={[]}
        isLoading={false}
        isSubmitting={false}
        errorMessage=""
        onSendMessage={onSendMessage}
      />
    );

    await userEvent.type(screen.getByLabelText("Message AI"), "Help me prioritize.");
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(onSendMessage).toHaveBeenCalledWith("Help me prioritize.");
  });

  it("renders history messages", () => {
    render(
      <AISidebar
        messages={[
          { role: "user", content: "Move card-2 to review." },
          { role: "assistant", content: "Done. I moved card-2 to Review." },
        ]}
        isLoading={false}
        isSubmitting={false}
        errorMessage=""
        onSendMessage={vi.fn()}
      />
    );

    expect(screen.getByText("Move card-2 to review.")).toBeInTheDocument();
    expect(screen.getByText("Done. I moved card-2 to Review.")).toBeInTheDocument();
  });
});
