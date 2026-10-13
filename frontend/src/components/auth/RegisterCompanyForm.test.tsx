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

function fillRequiredFields(password: string) {
  const fields = [
    ['Nombre de la empresa', 'Empresa de prueba'],
    ['Nombre', 'Jordi'],
    ['Apellidos', 'García'],
    ['Email', 'empresa@example.com'],
    ['Contraseña', password],
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

  it('registra la empresa enviando sólo los datos requeridos', async () => {
    vi.mocked(registerCompany).mockResolvedValue(authResponse)
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    fillRequiredFields('secure-password')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    const expectedData = {
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
      new Error('El email ya está registrado'),
    )
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    fillRequiredFields('secure-password')
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(await screen.findByText('El email ya está registrado')).toBeInTheDocument()
  })

  it('no envía datos con un email inválido ni con una contraseña demasiado corta', async () => {
    const user = userEvent.setup()
    renderWithProviders(<RegisterCompanyForm />)

    fillRequiredFields('secure-password')
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'correo-no-valido' },
    })
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'empresa@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'short' },
    })
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(registerCompany).not.toHaveBeenCalled()
  })
})
