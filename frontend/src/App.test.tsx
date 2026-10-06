import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "./App";
import { renderWithProviders } from "./test/testUtils";

describe("Landing page", () => {
  it("renders the landing content inside the app layout", () => {
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
      within(main).getByRole("heading", {
        name: "La seguridad se construye practicando.",
      }),
    ).toBeInTheDocument();
    expect(
      within(main).getByRole("heading", {
        name: "Entrena. Aprende. Evoluciona.",
      }),
    ).toBeInTheDocument();
    expect(
      within(main).getByRole("link", { name: "Crear una cuenta" }),
    ).toHaveAttribute("href", "/register");
    expect(
      within(main).getByRole("link", { name: "Iniciar sesión" }),
    ).toHaveAttribute("href", "/login");
    expect(
      within(main).getByRole("heading", { name: "Aprende haciendo" }),
    ).toBeInTheDocument();
  });

  it("navigates from the landing page to company registration", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />);

    await user.click(screen.getByRole("link", { name: "Crear una cuenta" }));

    expect(
      await screen.findByRole("heading", {
        name: "Empieza a entrenar a tu equipo",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Datos de la empresa" })).toBeInTheDocument();
  });

  it("renders the login form for the login route", () => {
    renderWithProviders(<App />, ["/login"]);

    expect(screen.getByRole("heading", { name: "Bienvenido de nuevo" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });
});
