import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";
import { renderWithProviders } from "./test/testUtils";

describe("App layout", () => {
  it("renders the header, main content, and footer in order", () => {
    renderWithProviders(<App />);

    const header = screen.getByRole("banner");
    const main = screen.getByRole("main");
    const footer = screen.getByRole("contentinfo");

    expect(
      header.compareDocumentPosition(main) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      main.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      within(main).getByRole("heading", { name: "Registrar empresa" }),
    ).toBeInTheDocument();
    expect(within(main).getByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });
});
