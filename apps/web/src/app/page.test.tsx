import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";
import { Providers } from "@/components/providers/Providers";

describe("HomePage Smoke Test", () => {
  it("renders the primary h1 heading and theme controls", () => {
    render(
      <Providers>
        <HomePage />
      </Providers>
    );

    const mainHeading = screen.getByRole("heading", {
      level: 1,
      name: /ai-native learning built for/i,
    });
    expect(mainHeading).toBeInTheDocument();

    const themeSelector = screen.getByRole("group", { name: /theme selector/i });
    expect(themeSelector).toBeInTheDocument();
  });
});
