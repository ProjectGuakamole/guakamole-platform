import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { login, registerCompany } from './authApi'
import type { AuthResponse, CompanyRegisterData, LoginData } from '../types/auth'

const authResponse: AuthResponse = {
  token: 'test-token',
  user: {
    id: 'company-1',
    email: 'empresa@example.com',
    companyName: 'Empresa de prueba',
  },
}

const registerData: CompanyRegisterData = {
  companyName: 'Empresa de prueba',
  email: 'empresa@example.com',
  password: 'secure-password',
  confirmPassword: 'secure-password',
  taxId: 'B12345678',
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
      json: vi.fn().mockResolvedValue({ message: 'El CIF ya está registrado' }),
    })

    await expect(registerCompany(registerData)).rejects.toThrow(
      'El CIF ya está registrado',
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
