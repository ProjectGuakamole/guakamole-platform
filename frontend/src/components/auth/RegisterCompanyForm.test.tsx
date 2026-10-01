import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { registerCompany } from '../../api/authApi'
import type { AuthResponse } from '../../types/auth'
import { renderWithProviders } from '../../test/testUtils'
import RegisterCompanyForm from './RegisterCompanyForm'

vi.mock('../../api/authApi', () => ({
  registerCompany: vi.fn(),
}))

const authResponse: AuthResponse = {
  token: 'test-token',
  user: {
    id: 'company-1',
    email: 'empresa@example.com',
    companyName: 'Empresa de prueba',
  },
}

describe('RegisterCompanyForm', () => {
  beforeEach(() => {
    vi.mocked(registerCompany).mockReset()
  })

  it('impide enviar contraseñas distintas y registra la empresa cuando coinciden', async () => {
    vi.mocked(registerCompany).mockResolvedValue(authResponse)
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    await user.type(screen.getByLabelText('Nombre de la empresa'), 'Empresa de prueba')
    await user.type(screen.getByLabelText('CIF / NIF'), 'B12345678')
    await user.type(screen.getByLabelText('Email'), 'empresa@example.com')
    await user.type(screen.getByLabelText('Contraseña'), 'secure-password')
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'different-password')

    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Crear cuenta' })).toBeDisabled()
    expect(registerCompany).not.toHaveBeenCalled()

    await user.clear(screen.getByLabelText('Confirmar contraseña'))
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'secure-password')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    await waitFor(() => {
      expect(registerCompany).toHaveBeenCalledOnce()
      expect(vi.mocked(registerCompany).mock.calls[0][0]).toEqual({
        companyName: 'Empresa de prueba',
        taxId: 'B12345678',
        email: 'empresa@example.com',
        password: 'secure-password',
        confirmPassword: 'secure-password',
      })
    })
    expect(
      await screen.findByText('La empresa se ha registrado correctamente.'),
    ).toBeInTheDocument()
  })

  it('muestra el error devuelto por el registro', async () => {
    vi.mocked(registerCompany).mockRejectedValue(
      new Error('El CIF ya está registrado'),
    )
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    await user.type(screen.getByLabelText('Nombre de la empresa'), 'Empresa de prueba')
    await user.type(screen.getByLabelText('CIF / NIF'), 'B12345678')
    await user.type(screen.getByLabelText('Email'), 'empresa@example.com')
    await user.type(screen.getByLabelText('Contraseña'), 'secure-password')
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'secure-password')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(await screen.findByText('El CIF ya está registrado')).toBeInTheDocument()
  })
})
