import type {
  AuthResponse,
  CompanyRegisterData,
  LoginData,
} from "../types/auth";

const API_URL = "http://localhost:3000/api/auth";

/**
 * Registra una nueva organización
 * y el usuario asociado.
 */
export const registerCompany = async (
  data: CompanyRegisterData,
): Promise<AuthResponse> => {
  const response = await fetch(`${API_URL}/register`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();

    throw new Error(error.message || "No se ha podido registrar la empresa");
  }

  return response.json();
};

/**
 * Inicia sesión.
 */
export const login = async (data: LoginData): Promise<AuthResponse> => {
  const response = await fetch(`${API_URL}/login`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();

    throw new Error(error.message || "Email o contraseña incorrectos");
  }

  return response.json();
};
