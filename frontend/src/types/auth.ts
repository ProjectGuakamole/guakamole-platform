// Datos de la organización.
export interface OrganizationRegisterData {
  name: string;
  slug: string;
  orgRegisteredName: string;
  orgTax: string;

  idCountry: number;
  idState: number;
  idCity: number;

  orgAddress: string;
  orgZipcode: string;
}

// Datos del usuario durante el registro.
export interface UserRegisterData {
  email: string;
  password: string;
  confirmPassword: string;

  firstName: string;
  lastName: string;
  birthdate: string;

  idCountry: number;
  idState: number;
  idCity: number;

  userAddress: string;
  userZipcode: string;
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
