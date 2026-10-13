import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { login, registerCompany } from './authApi'
import type { AuthResponse, CompanyRegisterData, LoginData } from '../types/auth'

const authResponse: AuthResponse = {
  token: 'test-token',
  user: {
    id: 1,
    email: 'empresa@example.com',
    firstName: 'Jordi',
    lastName: 'García',
    idOrganization: 1,
  },
}

const registerData: CompanyRegisterData = {
  organization: {
    name: 'Empresa de prueba',
  },
  user: {
    firstName: 'Jordi',
    lastName: 'García',
    email: 'empresa@example.com',
    password: 'secure-password',
  },
}

const loginData: LoginData = {
  email: 'empresa@example.com',
  password: 'secure-password',
}

describe('authApi', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('registra una empresa y devuelve la respuesta de autenticación', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(authResponse),
    })

    await expect(registerCompany(registerData)).resolves.toEqual(authResponse)
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registerData),
    })
  })

  it('propaga el mensaje devuelto por el servidor al fallar el registro', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ message: 'El email ya está registrado' }),
    })

    await expect(registerCompany(registerData)).rejects.toThrow(
      'El email ya está registrado',
    )
  })

  it('inicia sesión y devuelve la respuesta de autenticación', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(authResponse),
    })

    await expect(login(loginData)).resolves.toEqual(authResponse)
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData),
    })
  })

  it('usa un mensaje predeterminado cuando falla el login sin mensaje del servidor', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({}),
    })

    await expect(login(loginData)).rejects.toThrow('Email o contraseña incorrectos')
  })
})
