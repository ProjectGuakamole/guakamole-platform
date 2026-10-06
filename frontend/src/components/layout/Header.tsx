import { Box, Button, Container, HStack, Link, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

function Header() {
  return (
    <Box
      as="header"
      background="rgba(8, 12, 20, 0.96)"
      borderBottom="1px solid"
      borderColor="rgba(255, 255, 255, 0.08)"
      position="relative"
      zIndex={1}
    >
      <Container maxW="7xl">
        <HStack justify="space-between" minH="76px">
          <Link
            _hover={{ textDecoration: "none" }}
            aria-label="Guakamole, inicio"
            asChild
            display="inline-flex"
          >
            <RouterLink to="/#inicio">
              <HStack gap={3}>
                <Box
                  alignItems="center"
                  background="rgba(45, 212, 191, 0.14)"
                  border="1px solid"
                  borderColor="rgba(45, 212, 191, 0.35)"
                  borderRadius="lg"
                  color="teal.200"
                  display="flex"
                  fontSize="lg"
                  fontWeight="bold"
                  h={10}
                  justifyContent="center"
                  w={10}
                >
                  G
                </Box>
                <Text color="white" fontSize="xl" fontWeight="bold">
                  guakamole
                </Text>
              </HStack>
            </RouterLink>
          </Link>

          <HStack as="nav" aria-label="Navegación principal" gap={8}>
            <Link
              asChild
              color="gray.300"
              display={{ base: "none", md: "inline" }}
              _hover={{ color: "teal.200", textDecoration: "none" }}
            >
              <RouterLink to="/#como-funciona">La plataforma</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.300"
              display={{ base: "none", md: "inline" }}
              _hover={{ color: "teal.200", textDecoration: "none" }}
            >
              <RouterLink to="/#beneficios">Beneficios</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.300"
              display={{ base: "none", sm: "inline" }}
            >
              <RouterLink to="/login">Iniciar sesión</RouterLink>
            </Link>
            <Button asChild colorPalette="teal" size="sm">
              <RouterLink to="/register">Crear cuenta</RouterLink>
            </Button>
          </HStack>
        </HStack>
      </Container>
    </Box>
  );
}

export default Header;
