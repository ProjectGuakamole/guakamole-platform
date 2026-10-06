import { screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { login } from "../../api/authApi";
import type { AuthResponse } from "../../types/auth";
import { renderWithProviders } from "../../test/testUtils";
import LoginForm from "./LoginForm";

vi.mock("../../api/authApi", () => ({
  login: vi.fn(),
}));

const authResponse: AuthResponse = {
  token: "test-token",
  user: {
    id: 1,
    email: "empresa@example.com",
    firstName: "Darren",
    lastName: "Williams",
    idOrganization: 1,
  },
};

describe("LoginForm", () => {
  beforeEach(() => {
    vi.mocked(login).mockReset();
  });

  it("envía las credenciales y muestra la confirmación al iniciar sesión", async () => {
    vi.mocked(login).mockResolvedValue(authResponse);
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "empresa@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "secure-password");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledOnce();
      expect(vi.mocked(login).mock.calls[0][0]).toEqual({
        email: "empresa@example.com",
        password: "secure-password",
      });
    });
    expect(
      await screen.findByText("Inicio de sesión correcto."),
    ).toBeInTheDocument();
  });

  it("muestra el mensaje de error devuelto por la autenticación", async () => {
    vi.mocked(login).mockRejectedValue(new Error("Credenciales no válidas"));
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "empresa@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(
      await screen.findByText("Credenciales no válidas"),
    ).toBeInTheDocument();
  });
});
