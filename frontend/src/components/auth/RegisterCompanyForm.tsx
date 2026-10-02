import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Field,
  Heading,
  Input,
  Separator,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";

import { registerCompany } from "../../api/authApi";
import type { CompanyRegisterData } from "../../types/auth";

export default function RegisterCompanyForm() {
  /*
   * Estado principal del formulario.
   *
   * Los datos están separados en:
   *
   * organization -> datos de la empresa
   * user         -> datos del usuario
   */
  const [formData, setFormData] = useState<CompanyRegisterData>({
    organization: {
      name: "",
      slug: "",
      orgRegisteredName: "",
      orgTax: "",
      idCountry: 0,
      idState: 0,
      idCity: 0,
      orgAddress: "",
      orgZipcode: "",
    },

    user: {
      email: "",
      password: "",
      confirmPassword: "",
      firstName: "",
      lastName: "",
      birthdate: "",
      idCountry: 0,
      idState: 0,
      idCity: 0,
      userAddress: "",
      userZipcode: "",
    },
  });

  /*
   * Mutation encargada de enviar el registro
   * al backend.
   */
  const mutation = useMutation({
    mutationFn: registerCompany,

    onSuccess: (data) => {
      console.log("Registro correcto:", data);
    },

    onError: (error) => {
      console.error("Error en el registro:", error);
    },
  });

  /**
   * Actualiza un campo de ORGANIZATION.
   */
  const handleOrganizationChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,

      organization: {
        ...previousData.organization,
        [name]: value,
      },
    }));
  };

  /**
   * Actualiza un campo de USERS.
   */
  const handleUserChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,

      user: {
        ...previousData.user,
        [name]: value,
      },
    }));
  };

  /**
   * Envía el formulario.
   */
  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    // Comprobamos que las contraseñas coincidan.
    if (formData.user.password !== formData.user.confirmPassword) {
      return;
    }

    mutation.mutate(formData);
  };

  return (
    <Box maxW="700px" mx="auto" p={8} borderWidth="1px" borderRadius="lg">
      <Stack gap={6}>
        <Box>
          <Heading size="lg">Registrar empresa</Heading>

          <Text color="dark" mt={2}>
            Registra tu empresa y crea el usuario administrador.
          </Text>
        </Box>

        <form onSubmit={handleSubmit}>
          <Stack gap={6}>
            {/* ========================================= */}
            {/* DATOS DE LA ORGANIZACIÓN                  */}
            {/* ========================================= */}

            <Heading size="md">Datos de la empresa</Heading>

            {/* Nombre */}
            <Field.Root required>
              <Field.Label>Nombre de la empresa</Field.Label>

              <Input
                name="name"
                value={formData.organization.name}
                onChange={handleOrganizationChange}
                placeholder="Mi Empresa"
              />
            </Field.Root>

            {/* Slug */}
            <Field.Root required>
              <Field.Label>Slug</Field.Label>

              <Input
                name="slug"
                value={formData.organization.slug}
                onChange={handleOrganizationChange}
                placeholder="mi-empresa"
              />
            </Field.Root>

            {/* Razón social */}
            <Field.Root>
              <Field.Label>Razón social</Field.Label>

              <Input
                name="orgRegisteredName"
                value={formData.organization.orgRegisteredName}
                onChange={handleOrganizationChange}
                placeholder="Mi Empresa S.L."
              />
            </Field.Root>

            {/* CIF */}
            <Field.Root>
              <Field.Label>CIF / NIF</Field.Label>

              <Input
                name="orgTax"
                value={formData.organization.orgTax}
                onChange={handleOrganizationChange}
                placeholder="B12345678"
              />
            </Field.Root>

            {/* País */}
            <Field.Root required>
              <Field.Label>ID País</Field.Label>

              <Input
                name="idCountry"
                type="number"
                value={formData.organization.idCountry || ""}
                onChange={handleOrganizationChange}
              />
            </Field.Root>

            {/* Estado */}
            <Field.Root required>
              <Field.Label>ID Estado / Provincia</Field.Label>

              <Input
                name="idState"
                type="number"
                value={formData.organization.idState || ""}
                onChange={handleOrganizationChange}
              />
            </Field.Root>

            {/* Ciudad */}
            <Field.Root required>
              <Field.Label>ID Ciudad</Field.Label>

              <Input
                name="idCity"
                type="number"
                value={formData.organization.idCity || ""}
                onChange={handleOrganizationChange}
              />
            </Field.Root>

            {/* Dirección */}
            <Field.Root>
              <Field.Label>Dirección</Field.Label>

              <Input
                name="orgAddress"
                value={formData.organization.orgAddress}
                onChange={handleOrganizationChange}
                placeholder="Calle Mayor 10"
              />
            </Field.Root>

            {/* Código postal */}
            <Field.Root>
              <Field.Label>Código postal</Field.Label>

              <Input
                name="orgZipcode"
                value={formData.organization.orgZipcode}
                onChange={handleOrganizationChange}
                placeholder="08001"
              />
            </Field.Root>

            <Separator />

            {/* ========================================= */}
            {/* DATOS DEL USUARIO                         */}
            {/* ========================================= */}

            <Heading size="md">Datos del usuario</Heading>

            {/* Nombre */}
            <Field.Root required>
              <Field.Label>Nombre</Field.Label>

              <Input
                name="firstName"
                value={formData.user.firstName}
                onChange={handleUserChange}
                placeholder="Jordi"
              />
            </Field.Root>

            {/* Apellidos */}
            <Field.Root required>
              <Field.Label>Apellidos</Field.Label>

              <Input
                name="lastName"
                value={formData.user.lastName}
                onChange={handleUserChange}
                placeholder="García"
              />
            </Field.Root>

            {/* Email */}
            <Field.Root required>
              <Field.Label>Email</Field.Label>

              <Input
                name="email"
                type="email"
                value={formData.user.email}
                onChange={handleUserChange}
                placeholder="usuario@empresa.com"
              />
            </Field.Root>

            {/* Fecha de nacimiento */}
            <Field.Root>
              <Field.Label>Fecha de nacimiento</Field.Label>

              <Input
                name="birthdate"
                type="date"
                value={formData.user.birthdate}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* Contraseña */}
            <Field.Root required>
              <Field.Label>Contraseña</Field.Label>

              <Input
                name="password"
                type="password"
                value={formData.user.password}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* Confirmar contraseña */}
            <Field.Root required>
              <Field.Label>Confirmar contraseña</Field.Label>

              <Input
                name="confirmPassword"
                type="password"
                value={formData.user.confirmPassword}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* País */}
            <Field.Root required>
              <Field.Label>ID País</Field.Label>

              <Input
                name="idCountry"
                type="number"
                value={formData.user.idCountry || ""}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* Estado */}
            <Field.Root required>
              <Field.Label>ID Estado / Provincia</Field.Label>

              <Input
                name="idState"
                type="number"
                value={formData.user.idState || ""}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* Ciudad */}
            <Field.Root required>
              <Field.Label>ID Ciudad</Field.Label>

              <Input
                name="idCity"
                type="number"
                value={formData.user.idCity || ""}
                onChange={handleUserChange}
              />
            </Field.Root>

            {/* Dirección */}
            <Field.Root>
              <Field.Label>Dirección</Field.Label>

              <Input
                name="userAddress"
                value={formData.user.userAddress}
                onChange={handleUserChange}
                placeholder="Calle Mayor 10"
              />
            </Field.Root>

            {/* Código postal */}
            <Field.Root>
              <Field.Label>Código postal</Field.Label>

              <Input
                name="userZipcode"
                value={formData.user.userZipcode}
                onChange={handleUserChange}
                placeholder="08001"
              />
            </Field.Root>

            {/* Error de contraseñas */}
            {formData.user.password !== formData.user.confirmPassword &&
              formData.user.confirmPassword.length > 0 && (
                <Alert.Root status="error">
                  <Alert.Indicator />

                  <Alert.Content>Las contraseñas no coinciden.</Alert.Content>
                </Alert.Root>
              )}

            {/* Error del backend */}
            {mutation.isError && (
              <Alert.Root status="error">
                <Alert.Indicator />

                <Alert.Content>{mutation.error.message}</Alert.Content>
              </Alert.Root>
            )}

            {/* Registro correcto */}
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
              disabled={
                formData.user.password !== formData.user.confirmPassword
              }
            >
              Crear cuenta
            </Button>
          </Stack>
        </form>
      </Stack>
    </Box>
  );
}
