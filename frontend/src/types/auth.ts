// Datos de la organización durante el registro.
export interface OrganizationRegisterData {
  name: string;
}

// Datos del usuario durante el registro.
export interface UserRegisterData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

// Datos completos del registro.
export interface CompanyRegisterData {
  organization: OrganizationRegisterData;
  user: UserRegisterData;
}

// Datos necesarios para iniciar sesión.
export interface LoginData {
  email: string;
  password: string;
}

// Respuesta de autenticación.
export interface AuthResponse {
  token: string;

  user: {
    id: number;
    email: string;
    firstName: string;
    lastName: string;
    idOrganization: number;
  };
}
