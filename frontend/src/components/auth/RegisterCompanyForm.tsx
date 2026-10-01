import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";

import { registerCompany } from "../../api/authApi";
import type { CompanyRegisterData } from "../../types/auth";

export default function RegisterCompanyForm() {
  // Estado que almacena los datos introducidos
  // por el usuario en el formulario.
  const [formData, setFormData] = useState<CompanyRegisterData>({
    companyName: "",
    email: "",
    password: "",
    confirmPassword: "",
    taxId: "",
  });

  /*
   * useMutation gestiona la petición de registro.
   *
   * isPending  -> la petición está en curso.
   * isSuccess  -> el registro se ha realizado correctamente.
   * isError    -> se ha producido un error.
   * error      -> contiene el error devuelto.
   */
  const mutation = useMutation({
    mutationFn: registerCompany,

    onSuccess: (data) => {
      console.log("Empresa registrada:", data);

      // Posteriormente podremos:
      // - guardar el token
      // - actualizar el usuario autenticado
      // - redirigir al dashboard
    },

    onError: (error) => {
      console.error("Error al registrar:", error);
    },
  });

  /**
   * Actualiza el estado del campo que está
   * modificando el usuario.
   */
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  /**
   * Se ejecuta cuando el usuario envía el formulario.
   */
  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>) => {
    // Evitamos que el navegador recargue la página.
    event.preventDefault();

    // Comprobamos que las contraseñas coincidan.
    if (formData.password !== formData.confirmPassword) {
      return;
    }

    // Enviamos los datos al backend.
    mutation.mutate(formData);
  };

  return (
    <Box maxW="500px" mx="auto" p={8} borderWidth="1px" borderRadius="lg">
      <Stack gap={6}>
        <Box>
          <Heading size="lg">Registrar empresa</Heading>

          <Text color="gray.600" mt={2}>
            Crea una cuenta para tu empresa.
          </Text>
        </Box>

        <form onSubmit={handleSubmit}>
          <Stack gap={4}>
            {/* Nombre de la empresa */}
            <Field.Root required>
              <Field.Label>Nombre de la empresa</Field.Label>

              <Input
                name="companyName"
                type="text"
                value={formData.companyName}
                onChange={handleChange}
                placeholder="Mi Empresa S.L."
              />
            </Field.Root>

            {/* CIF / NIF */}
            <Field.Root required>
              <Field.Label>CIF / NIF</Field.Label>

              <Input
                name="taxId"
                type="text"
                value={formData.taxId}
                onChange={handleChange}
                placeholder="B12345678"
              />
            </Field.Root>

            {/* Email */}
            <Field.Root required>
              <Field.Label>Email</Field.Label>

              <Input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="empresa@email.com"
              />
            </Field.Root>

            {/* Contraseña */}
            <Field.Root required>
              <Field.Label>Contraseña</Field.Label>

              <Input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="********"
              />
            </Field.Root>

            {/* Confirmación de contraseña */}
            <Field.Root required>
              <Field.Label>Confirmar contraseña</Field.Label>

              <Input
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="********"
              />
            </Field.Root>

            {/* Error cuando las contraseñas no coinciden */}
            {formData.password !== formData.confirmPassword &&
              formData.confirmPassword.length > 0 && (
                <Alert.Root status="error">
                  <Alert.Indicator />
                  <Alert.Content>Las contraseñas no coinciden.</Alert.Content>
                </Alert.Root>
              )}

            {/* Error devuelto por el backend */}
            {mutation.isError && (
              <Alert.Root status="error">
                <Alert.Indicator />
                <Alert.Content>{mutation.error.message}</Alert.Content>
              </Alert.Root>
            )}

            {/* Registro realizado correctamente */}
            {mutation.isSuccess && (
              <Alert.Root status="success">
                <Alert.Indicator />
                <Alert.Content>
                  La empresa se ha registrado correctamente.
                </Alert.Content>
              </Alert.Root>
            )}

            <Button
              type="submit"
              colorPalette="blue"
              loading={mutation.isPending}
              disabled={formData.password !== formData.confirmPassword}
            >
              Crear cuenta
            </Button>
          </Stack>
        </form>
      </Stack>
    </Box>
  );
}
