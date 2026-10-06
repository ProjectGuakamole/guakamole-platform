import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";

import { login } from "../../api/authApi";
import type { LoginData } from "../../types/auth";

export default function LoginForm() {
  // Datos introducidos por el usuario.
  const [formData, setFormData] = useState<LoginData>({
    email: "",
    password: "",
  });

  /**
   * Mutation encargada de realizar el login.
   */
  const mutation = useMutation({
    mutationFn: login,

    onSuccess: (data) => {
      console.log("Login correcto:", data);

      // Posteriormente podremos:
      // - guardar el token
      // - actualizar el usuario autenticado
      // - redirigir al dashboard
    },

    onError: (error) => {
      console.error("Error de login:", error);
    },
  });

  /**
   * Actualiza los datos del formulario.
   */
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  /**
   * Envía las credenciales al backend.
   */
  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    mutation.mutate(formData);
  };

  return (
    <Box
      width="full"
      maxW="500px"
      mx="auto"
      color="white"
      css={{
        "& label": {
          color: "#cbd5e1",
        },
        "& input": {
          background: "rgba(255, 255, 255, 0.045)",
          borderColor: "rgba(255, 255, 255, 0.16)",
          color: "#fff",
        },
        "& input::placeholder": {
          color: "#94a3b8",
          fontWeight: "normal",
          opacity: 1,
        },
        "& input:focus": {
          borderColor: "#5eead4",
          boxShadow: "0 0 0 1px #5eead4",
        },
      }}
    >
      <Stack gap={6}>
        <Box>
          <Heading color="white" size="lg">Iniciar sesión</Heading>
        </Box>

        <form onSubmit={handleSubmit}>
          <Stack gap={4}>
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

            {/* Error devuelto por el backend */}
            {mutation.isError && (
              <Alert.Root status="error">
                <Alert.Indicator />
                <Alert.Content>{mutation.error.message}</Alert.Content>
              </Alert.Root>
            )}

            {/* Login correcto */}
            {mutation.isSuccess && (
              <Alert.Root status="success">
                <Alert.Indicator />
                <Alert.Content>Inicio de sesión correcto.</Alert.Content>
              </Alert.Root>
            )}

            <Button
              type="submit"
              colorPalette="teal"
              fontWeight="bold"
              loading={mutation.isPending}
              width="full"
            >
              Iniciar sesión
            </Button>
          </Stack>
        </form>
      </Stack>
    </Box>
  );
}
