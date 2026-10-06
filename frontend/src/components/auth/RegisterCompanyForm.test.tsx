import { fireEvent, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
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
    id: 1,
    email: 'empresa@example.com',
    firstName: 'Empresa',
    lastName: 'de prueba',
    idOrganization: 1,
  },
}

function fillRequiredFields(password: string, confirmPassword: string) {
  const fields = [
    ['Nombre de la empresa', 'Empresa de prueba'],
    ['Slug', 'empresa-de-prueba'],
    ['CIF / NIF', 'B12345678'],
    ['ID País', '1'],
    ['ID Estado / Provincia', '2'],
    ['ID Ciudad', '3'],
    ['Nombre', 'Jordi'],
    ['Apellidos', 'García'],
    ['Email', 'empresa@example.com'],
    ['Contraseña', password],
    ['Confirmar contraseña', confirmPassword],
  ]

  for (const [label, value] of fields) {
    for (const input of screen.queryAllByLabelText(label)) {
      fireEvent.change(input, { target: { value } })
    }
  }
}

describe('RegisterCompanyForm', () => {
  beforeEach(() => {
    vi.mocked(registerCompany).mockReset()
  })

  it('impide enviar contraseñas distintas y registra la empresa cuando coinciden', async () => {
    vi.mocked(registerCompany).mockResolvedValue(authResponse)
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    fillRequiredFields('secure-password', 'different-password')

    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Crear cuenta' })).toBeDisabled()
    expect(registerCompany).not.toHaveBeenCalled()

    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), {
      target: { value: 'secure-password' },
    })
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    const expectedData = {
      organization: {
        name: 'Empresa de prueba',
        slug: 'empresa-de-prueba',
        orgRegisteredName: '',
        orgTax: 'B12345678',
        idCountry: '1',
        idState: '2',
        idCity: '3',
        orgAddress: '',
        orgZipcode: '',
      },
      user: {
        email: 'empresa@example.com',
        password: 'secure-password',
        confirmPassword: 'secure-password',
        firstName: 'Jordi',
        lastName: 'García',
        birthdate: '',
        idCountry: '1',
        idState: '2',
        idCity: '3',
        userAddress: '',
        userZipcode: '',
      },
    }

    await waitFor(() => {
      expect(registerCompany).toHaveBeenCalledOnce()
      expect(vi.mocked(registerCompany).mock.calls[0][0]).toEqual(expectedData)
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

    fillRequiredFields('secure-password', 'secure-password')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(await screen.findByText('El CIF ya está registrado')).toBeInTheDocument()
  })
})
