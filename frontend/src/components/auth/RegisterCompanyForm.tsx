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

import { registerCompany } from "../../api/authApi";
import type { CompanyRegisterData } from "../../types/auth";

export default function RegisterCompanyForm() {
  const [formData, setFormData] = useState<CompanyRegisterData>({
    organization: {
      name: "",
    },
    user: {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
    },
  });

  const mutation = useMutation({
    mutationFn: registerCompany,
  });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const companyName = formData.organization.name.trim();
    const firstName = formData.user.firstName.trim();
    const lastName = formData.user.lastName.trim();
    const email = formData.user.email.trim();

    if (
      mutation.isPending ||
      !companyName ||
      companyName.length > 150 ||
      !firstName ||
      firstName.length > 100 ||
      !lastName ||
      lastName.length > 100 ||
      !email ||
      email.length > 254 ||
      !formData.user.password ||
      formData.user.password.length < 12 ||
      formData.user.password.length > 128
    ) {
      return;
    }

    mutation.mutate({
      organization: {
        name: companyName,
      },
      user: {
        firstName,
        lastName,
        email,
        password: formData.user.password,
      },
    });
  };

  return (
    <Box
      width="full"
      maxW="700px"
      mx="auto"
      color="var(--app-fg)"
      css={{
        "& label": {
          color: "var(--app-text-muted)",
        },
        "& input": {
          background: "var(--app-input)",
          borderColor: "var(--app-input-border)",
          color: "var(--app-fg)",
        },
        "& input::placeholder": {
          color: "var(--app-input-placeholder)",
          fontWeight: "normal",
          opacity: 1,
        },
        "& input:focus": {
          borderColor: "var(--app-accent)",
          boxShadow: "0 0 0 1px var(--app-accent)",
        },
      }}
    >
      <Stack gap={6}>
        <form onSubmit={handleSubmit}>
          <Stack gap={6}>
            <Heading color="var(--app-fg)" size="md">
              Crear cuenta
            </Heading>

            <Field.Root required>
              <Field.Label>Nombre de la organización</Field.Label>
              <Input
                name="companyName"
                value={formData.organization.name}
                onChange={(event) =>
                  setFormData((previousData) => ({
                    ...previousData,
                    organization: { name: event.target.value },
                  }))
                }
                placeholder="Mi Organización"
                autoComplete="organization"
                maxLength={150}
                pattern={".*\\S.*"}
                title="Introduce un nombre que no esté vacío."
                required
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Nombre</Field.Label>
              <Input
                name="firstName"
                value={formData.user.firstName}
                onChange={(event) =>
                  setFormData((previousData) => ({
                    ...previousData,
                    user: { ...previousData.user, firstName: event.target.value },
                  }))
                }
                placeholder="Nombre"
                autoComplete="given-name"
                maxLength={100}
                pattern={".*\\S.*"}
                title="Introduce un nombre que no esté vacío."
                required
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Apellidos</Field.Label>
              <Input
                name="lastName"
                value={formData.user.lastName}
                onChange={(event) =>
                  setFormData((previousData) => ({
                    ...previousData,
                    user: { ...previousData.user, lastName: event.target.value },
                  }))
                }
                placeholder="Apellidos"
                autoComplete="family-name"
                maxLength={100}
                pattern={".*\\S.*"}
                title="Introduce unos apellidos que no estén vacíos."
                required
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Email</Field.Label>
              <Input
                name="email"
                type="email"
                value={formData.user.email}
                onChange={(event) =>
                  setFormData((previousData) => ({
                    ...previousData,
                    user: { ...previousData.user, email: event.target.value },
                  }))
                }
                placeholder="usuario@empresa.com"
                autoComplete="email"
                autoCapitalize="none"
                maxLength={254}
                required
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Contraseña</Field.Label>
              <Input
                name="password"
                type="password"
                value={formData.user.password}
                onChange={(event) =>
                  setFormData((previousData) => ({
                    ...previousData,
                    user: { ...previousData.user, password: event.target.value },
                  }))
                }
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                required
              />
            </Field.Root>

            {mutation.isError && (
              <Alert.Root status="error">
                <Alert.Indicator />
                <Alert.Content>{mutation.error.message}</Alert.Content>
              </Alert.Root>
            )}

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
              colorPalette="teal"
              fontWeight="bold"
              loading={mutation.isPending}
              disabled={mutation.isPending}
              width="full"
            >
              Crear cuenta
            </Button>
          </Stack>
        </form>
      </Stack>
    </Box>
  );
}
