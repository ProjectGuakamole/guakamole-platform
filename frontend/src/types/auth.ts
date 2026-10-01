// Datos que enviamos al backend para registrar una empresa.
export interface CompanyRegisterData {
  companyName: string;
  email: string;
  password: string;
  confirmPassword: string;
  taxId: string;
}

// Datos que enviamos al backend para iniciar sesión.
export interface LoginData {
  email: string;
  password: string;
}

// Respuesta esperada del backend después de autenticarse.
export interface AuthResponse {
  token: string;
  user: {
    id: string;
    email: string;
    companyName: string;
  };
}
