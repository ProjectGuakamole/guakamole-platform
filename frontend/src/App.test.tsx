import { screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
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
      within(footer).getByRole("link", { name: "Volver al inicio ↑" }),
    ).toHaveAttribute("href", "/#inicio");
    expect(
      within(main).getByRole("heading", {
        name: "La seguridad se construye practicando.",
      }),
    ).toBeInTheDocument();
    expect(
      within(main).getByRole("heading", {
        name: "De la configuración al seguimiento",
      }),
    ).toBeInTheDocument();
    expect(
      within(main).getByRole("link", { name: "Crear una cuenta" }),
    ).toHaveAttribute("href", "/register");
    expect(
      within(main).getByRole("link", { name: "Iniciar sesión" }),
    ).toHaveAttribute("href", "/login");
    expect(
      within(main).getByRole("heading", {
        name: "Crea el espacio de tu organización",
      }),
    ).toBeInTheDocument();

    const platform = within(main).getByRole("region", {
      name: "De la configuración al seguimiento",
    });
    expect(
      within(platform).getByRole("heading", {
        name: "Asigna itinerarios de aprendizaje",
      }),
    ).toBeInTheDocument();
    expect(
      within(platform).getByRole("heading", {
        name: "Consulta la actividad y el avance",
      }),
    ).toBeInTheDocument();

    expect(
      within(main).queryByRole("heading", {
        name: "Convierte la preparación en una ventaja.",
      }),
    ).not.toBeInTheDocument();
    expect(
      screen
        .getAllByText("Beneficios")
        .some(
          (element) =>
            element.closest("a")?.getAttribute("href") === "/beneficios",
        ),
    ).toBe(true);
  });

  it("opens the responsive navigation menu and closes it after selecting a section", async () => {
    const user = userEvent.setup();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 375,
      writable: true,
    });
    window.dispatchEvent(new Event("resize"));
    renderWithProviders(<App />);

    await user.click(screen.getByRole("button", { name: "Abrir menú" }));

    const mobileNavigation = screen.getByRole("navigation", {
      name: "Navegación móvil",
    });
    expect(mobileNavigation).toBeVisible();
    expect(
      within(mobileNavigation).getByRole("link", { name: "Beneficios" }),
    ).toHaveAttribute("href", "/beneficios");

    await user.click(
      within(mobileNavigation).getByRole("link", { name: "Beneficios" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Convierte la preparación en una ventaja.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
        name: "La seguridad se construye practicando.",
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Abrir menú", hidden: true }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("renders a standalone benefits route with content distinct from the landing page", () => {
    renderWithProviders(<App />, ["/beneficios"]);

    expect(
      screen.getByRole("heading", {
        name: "Convierte la preparación en una ventaja.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Menos errores ante situaciones de riesgo",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Una cultura de seguridad compartida",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Decisiones de formación con criterio",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
        name: "La seguridad se construye practicando.",
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Crear cuenta" }),
    ).toHaveAttribute("href", "/register");
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
