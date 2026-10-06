import {
  Box,
  Button,
  Container,
  Heading,
  SimpleGrid,
  Stack,
  Text,
} from "@chakra-ui/react";
import { Link as RouterLink, Navigate, Route, Routes } from "react-router-dom";

import landingBackground from "./assets/landing-background.png";
import LoginForm from "./components/auth/LoginForm";
import RegisterCompanyForm from "./components/auth/RegisterCompanyForm";
import AuthPage from "./components/auth/AuthPage";
import AppLayout from "./layouts/AppLayout";

const features = [
  {
    number: "01",
    title: "Aprende haciendo",
    description:
      "Practica con escenarios realistas y laboratorios temporales diseñados para llevar la teoría a la acción.",
  },
  {
    number: "02",
    title: "Avanza en equipo",
    description:
      "Organiza equipos, asigna itinerarios y adapta el entrenamiento a las necesidades de tu organización.",
  },
  {
    number: "03",
    title: "Mide el progreso",
    description:
      "Sigue la evolución de cada persona y consulta la actividad para saber dónde reforzar conocimientos.",
  },
];

function LandingPage() {
  return (
    <>
      <Box
        as="section"
        aria-labelledby="hero-title"
        id="inicio"
        backgroundImage={`linear-gradient(90deg, rgba(7, 11, 19, 0.92) 0%, rgba(7, 11, 19, 0.76) 55%, rgba(7, 11, 19, 0.42) 100%), url("${landingBackground}")`}
        backgroundPosition="center"
        backgroundSize="cover"
        display="flex"
        alignItems="center"
        minH={{ base: "680px", lg: "calc(100vh - 76px)" }}
        position="relative"
        overflow="hidden"
      >
        <Container maxW="7xl" py={{ base: 16, md: 24 }}>
          <SimpleGrid columns={{ base: 1, lg: 2 }} gap={{ base: 12, lg: 20 }}>
            <Stack align="flex-start" gap={7} justify="center">
              <Text
                border="1px solid"
                borderColor="rgba(94, 234, 212, 0.35)"
                borderRadius="full"
                color="teal.200"
                fontSize="sm"
                fontWeight="semibold"
                letterSpacing="wider"
                px={4}
                py={2}
                textTransform="uppercase"
              >
                Entrenamiento en ciberseguridad
              </Text>
              <Stack gap={4}>
                <Heading
                  as="h1"
                  color="white"
                  fontSize={{ base: "4xl", md: "6xl" }}
                  id="hero-title"
                  lineHeight="1.08"
                  maxW="2xl"
                >
                  La seguridad se construye{" "}
                  <Text as="span" color="teal.200">
                    practicando.
                  </Text>
                </Heading>
                <Text
                  color="gray.300"
                  fontSize={{ base: "lg", md: "xl" }}
                  lineHeight="1.8"
                  maxW="xl"
                >
                  Prepara a tu equipo para los retos reales. Diseña itinerarios,
                  practica en laboratorios SOC y convierte cada reto en
                  experiencia.
                </Text>
              </Stack>
              <Stack direction={{ base: "column", sm: "row" }} gap={4}>
                <Button
                  asChild
                  colorPalette="teal"
                  fontWeight="bold"
                  size="lg"
                >
                  <RouterLink to="/register">Crear una cuenta</RouterLink>
                </Button>
                <Button
                  asChild
                  borderColor="rgba(255, 255, 255, 0.28)"
                  color="white"
                  size="lg"
                  variant="outline"
                  _hover={{ bg: "rgba(255, 255, 255, 0.08)" }}
                >
                    <RouterLink to="/login">Iniciar sesión</RouterLink>
                </Button>
              </Stack>
            </Stack>

            <Box
              alignSelf="center"
              backdropFilter="blur(16px)"
              background="rgba(12, 19, 31, 0.76)"
              border="1px solid"
              borderColor="rgba(255, 255, 255, 0.14)"
              borderRadius="2xl"
              boxShadow="0 24px 80px rgba(0, 0, 0, 0.32)"
              maxW={{ base: "full", lg: "420px" }}
              ml={{ lg: "auto" }}
              p={{ base: 6, md: 8 }}
              width="full"
            >
              <Stack gap={6}>
                <Stack align="flex-start" gap={3}>
                  <Text
                    color="teal.200"
                    fontSize="sm"
                    fontWeight="bold"
                    letterSpacing="wider"
                    textTransform="uppercase"
                  >
                    Preparados para lo inesperado
                  </Text>
                  <Heading as="h2" color="white" fontSize="2xl">
                    Del conocimiento a la acción
                  </Heading>
                  <Text color="gray.300" lineHeight="1.75">
                    Un espacio seguro donde cada persona puede aprender,
                    equivocarse y mejorar antes de enfrentarse a una amenaza
                    real.
                  </Text>
                </Stack>
                <Box borderTop="1px solid" borderColor="rgba(255,255,255,0.14)" pt={5}>
                  <SimpleGrid columns={2} gap={5}>
                    <Box>
                      <Text color="white" fontSize="lg" fontWeight="bold">
                        Escenarios
                      </Text>
                      <Text color="gray.400" fontSize="sm" mt={1}>
                        Práctica realista
                      </Text>
                    </Box>
                    <Box>
                      <Text color="white" fontSize="lg" fontWeight="bold">
                        Laboratorios SOC
                      </Text>
                      <Text color="gray.400" fontSize="sm" mt={1}>
                        Entornos temporales
                      </Text>
                    </Box>
                  </SimpleGrid>
                </Box>
              </Stack>
            </Box>
          </SimpleGrid>
        </Container>
      </Box>

      <Box as="section" id="como-funciona" py={{ base: 16, md: 24 }}>
        <Container maxW="7xl">
          <Stack gap={12}>
            <Stack gap={4} maxW="2xl">
              <Text
                color="teal.300"
                fontSize="sm"
                fontWeight="bold"
                letterSpacing="wider"
                textTransform="uppercase"
              >
                Una plataforma, un equipo más preparado
              </Text>
              <Heading as="h2" color="white" fontSize={{ base: "3xl", md: "4xl" }}>
                Entrena. Aprende. Evoluciona.
              </Heading>
              <Text color="gray.400" fontSize="lg" lineHeight="1.8">
                Todo lo que necesitas para convertir la ciberseguridad en una
                habilidad práctica para toda tu organización.
              </Text>
            </Stack>

            <SimpleGrid columns={{ base: 1, md: 3 }} gap={5}>
              {features.map((feature) => (
                <Box
                  key={feature.number}
                  background="rgba(255, 255, 255, 0.035)"
                  border="1px solid"
                  borderColor="rgba(255, 255, 255, 0.1)"
                  borderRadius="xl"
                  p={{ base: 6, md: 8 }}
                >
                  <Stack align="flex-start" gap={5}>
                    <Text
                      color="teal.300"
                      fontSize="sm"
                      fontWeight="bold"
                      letterSpacing="wider"
                    >
                      {feature.number}
                    </Text>
                    <Stack gap={3}>
                      <Heading as="h3" color="white" fontSize="xl">
                        {feature.title}
                      </Heading>
                      <Text color="gray.400" lineHeight="1.75">
                        {feature.description}
                      </Text>
                    </Stack>
                  </Stack>
                </Box>
              ))}
            </SimpleGrid>
          </Stack>
        </Container>
      </Box>

      <Box
        as="section"
        background="rgba(45, 212, 191, 0.08)"
        borderTop="1px solid"
        borderColor="rgba(45, 212, 191, 0.16)"
        id="beneficios"
        py={{ base: 12, md: 16 }}
      >
        <Container maxW="7xl">
          <Stack
            align={{ base: "flex-start", md: "center" }}
            direction={{ base: "column", md: "row" }}
            justify="space-between"
            gap={6}
          >
            <Stack gap={2} maxW="2xl">
              <Heading as="h2" color="white" fontSize="2xl">
                La próxima defensa empieza con la práctica.
              </Heading>
              <Text color="gray.300">
                Descubre una nueva forma de preparar a tu organización.
              </Text>
            </Stack>
            <Button asChild colorPalette="teal" flexShrink={0} size="lg">
              <RouterLink to="/register">Empezar ahora</RouterLink>
            </Button>
          </Stack>
        </Container>
      </Box>
    </>
  );
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppLayout>
            <LandingPage />
          </AppLayout>
        }
      />
      <Route
        path="/login"
        element={
          <AppLayout>
            <AuthPage
              title="Bienvenido de nuevo"
              description="Accede a tu espacio de entrenamiento y continúa preparando a tu equipo."
              alternateText="¿Aún no tienes cuenta?"
              alternateLabel="Registra tu empresa"
              alternateTo="/register"
            >
              <LoginForm />
            </AuthPage>
          </AppLayout>
        }
      />
      <Route
        path="/register"
        element={
          <AppLayout>
            <AuthPage
              title="Empieza a entrenar a tu equipo"
              description="Crea el espacio de tu organización y descubre una forma práctica de fortalecer su ciberseguridad."
              alternateText="¿Ya tienes una cuenta?"
              alternateLabel="Inicia sesión"
              alternateTo="/login"
            >
              <RegisterCompanyForm />
            </AuthPage>
          </AppLayout>
        }
      />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
}

export default App;
