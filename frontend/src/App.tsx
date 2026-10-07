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
    title: "Crea el espacio de tu organización",
    description:
      "Centraliza a tu equipo en un entorno de formación compartido y preparado para organizar sus actividades.",
  },
  {
    number: "02",
    title: "Asigna itinerarios de aprendizaje",
    description:
      "Selecciona escenarios y distribuye prácticas según los objetivos y responsabilidades de cada equipo.",
  },
  {
    number: "03",
    title: "Consulta la actividad y el avance",
    description:
      "Revisa el progreso de las personas y utiliza esa información para planificar los siguientes pasos.",
  },
];

function LandingPage() {
  return (
    <>
      <Box
        as="section"
        aria-labelledby="hero-title"
        id="portada"
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

      <Box
        as="section"
        aria-labelledby="platform-title"
        id="inicio"
        scrollMarginTop="76px"
        py={{ base: 16, md: 24 }}
      >
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
                Así funciona Guakamole
              </Text>
              <Heading
                as="h2"
                color="white"
                fontSize={{ base: "3xl", md: "4xl" }}
                id="platform-title"
              >
                De la configuración al seguimiento
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

    </>
  );
}

function BenefitsPage() {
  const outcomes = [
    {
      number: "01",
      title: "Menos errores ante situaciones de riesgo",
      description:
        "La práctica ayuda a reconocer señales de alerta y a responder con más seguridad ante intentos de engaño y otros riesgos cotidianos.",
    },
    {
      number: "02",
      title: "Una cultura de seguridad compartida",
      description:
        "Cuando todo el equipo participa, la seguridad deja de ser responsabilidad de unas pocas personas y se convierte en un hábito común.",
    },
    {
      number: "03",
      title: "Decisiones de formación con criterio",
      description:
        "El seguimiento del avance permite identificar necesidades, orientar los siguientes pasos y dedicar el esfuerzo donde más se necesita.",
    },
  ];

  return (
    <Box
      as="section"
      aria-labelledby="benefits-title"
      background="linear-gradient(180deg, rgba(45, 212, 191, 0.1), transparent 70%)"
      minH="calc(100vh - 152px)"
      py={{ base: 16, md: 24 }}
    >
      <Container maxW="7xl">
        <Stack gap={{ base: 10, md: 16 }}>
          <Stack gap={5} maxW="3xl">
            <Text
              color="teal.200"
              fontSize="sm"
              fontWeight="bold"
              letterSpacing="wider"
              textTransform="uppercase"
            >
              Beneficios para tu organización
            </Text>
            <Heading
              as="h1"
              color="white"
              fontSize={{ base: "4xl", md: "6xl" }}
              id="benefits-title"
              lineHeight="1.1"
            >
              Convierte la preparación en una ventaja.
            </Heading>
            <Text color="gray.300" fontSize={{ base: "lg", md: "xl" }} lineHeight="1.8">
              Guakamole ayuda a que las personas ganen confianza para actuar
              ante riesgos digitales y a que la organización construya hábitos
              de seguridad sostenibles.
            </Text>
          </Stack>

          <SimpleGrid columns={{ base: 1, md: 3 }} gap={5}>
            {outcomes.map((outcome) => (
              <Box
                key={outcome.number}
                background="rgba(12, 19, 31, 0.76)"
                border="1px solid"
                borderColor="rgba(255, 255, 255, 0.12)"
                borderRadius="2xl"
                minH={{ md: "270px" }}
                p={{ base: 6, md: 8 }}
              >
                <Stack align="flex-start" gap={6}>
                  <Text
                    color="teal.200"
                    fontSize="sm"
                    fontWeight="bold"
                    letterSpacing="wider"
                  >
                    {outcome.number}
                  </Text>
                  <Stack gap={3}>
                    <Heading as="h2" color="white" fontSize="xl">
                      {outcome.title}
                    </Heading>
                    <Text color="gray.400" lineHeight="1.8">
                      {outcome.description}
                    </Text>
                  </Stack>
                </Stack>
              </Box>
            ))}
          </SimpleGrid>

          <Stack
            align={{ base: "flex-start", md: "center" }}
            background="rgba(45, 212, 191, 0.08)"
            border="1px solid"
            borderColor="rgba(45, 212, 191, 0.2)"
            borderRadius="2xl"
            direction={{ base: "column", md: "row" }}
            justify="space-between"
            gap={6}
            p={{ base: 6, md: 8 }}
          >
            <Stack gap={2} maxW="2xl">
              <Heading as="h2" color="white" fontSize="2xl">
                Empieza a preparar a tu organización.
              </Heading>
              <Text color="gray.300">
                Crea tu espacio y descubre una forma práctica de fortalecer la
                seguridad de tu equipo.
              </Text>
            </Stack>
            <Button asChild colorPalette="teal" flexShrink={0} size="lg">
              <RouterLink to="/register">Crear cuenta</RouterLink>
            </Button>
          </Stack>
        </Stack>
      </Container>
    </Box>
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
        path="/beneficios"
        element={
          <AppLayout>
            <BenefitsPage />
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
