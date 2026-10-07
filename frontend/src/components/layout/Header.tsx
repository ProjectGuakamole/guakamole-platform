import { useState } from "react";
import {
  Box,
  Button,
  Container,
  HStack,
  IconButton,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react";
import { FiMenu, FiX } from "react-icons/fi";
import { Link as RouterLink } from "react-router-dom";

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const closeMenu = () => setIsMenuOpen(false);

  return (
    <Box
      as="header"
      background="rgba(8, 12, 20, 0.96)"
      borderBottom="1px solid"
      borderColor="rgba(255, 255, 255, 0.08)"
      position="sticky"
      top={0}
      zIndex={1000}
    >
      <Container maxW="7xl">
        <Stack gap={0}>
        <HStack justify="space-between" minH="76px">
          <Link
            _hover={{ textDecoration: "none" }}
            aria-label="Guakamole, inicio"
            asChild
            display="inline-flex"
            onClick={closeMenu}
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

          <HStack
            as="nav"
            aria-label="Navegación principal"
            display={{ base: "none", md: "flex" }}
            gap={8}
          >
            <Link
              asChild
              color="gray.300"
              _hover={{ color: "teal.200", textDecoration: "none" }}
            >
              <RouterLink to="/#inicio">La plataforma</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.300"
              _hover={{ color: "teal.200", textDecoration: "none" }}
            >
              <RouterLink to="/beneficios">Beneficios</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.300"
            >
              <RouterLink to="/login">Iniciar sesión</RouterLink>
            </Link>
            <Button asChild colorPalette="teal" size="sm">
              <RouterLink to="/register">Crear cuenta</RouterLink>
            </Button>
          </HStack>

          <IconButton
            aria-label={isMenuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-controls="mobile-navigation"
            aria-expanded={isMenuOpen}
            display={{ base: "inline-flex", md: "none" }}
            onClick={() => setIsMenuOpen((open) => !open)}
            variant="ghost"
            color="white"
          >
            {isMenuOpen ? <FiX /> : <FiMenu />}
          </IconButton>
        </HStack>
        <Box
          as="nav"
          aria-label="Navegación móvil"
          borderTop="1px solid"
          borderColor="rgba(255, 255, 255, 0.08)"
          display={{ base: isMenuOpen ? "block" : "none", md: "none" }}
          id="mobile-navigation"
          pb={4}
          pt={2}
        >
          <Stack align="stretch" gap={1}>
            <Link
              asChild
              color="gray.200"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "rgba(255, 255, 255, 0.06)", textDecoration: "none" }}
            >
              <RouterLink to="/#inicio">La plataforma</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.200"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "rgba(255, 255, 255, 0.06)", textDecoration: "none" }}
            >
              <RouterLink to="/beneficios">Beneficios</RouterLink>
            </Link>
            <Link
              asChild
              color="gray.200"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "rgba(255, 255, 255, 0.06)", textDecoration: "none" }}
            >
              <RouterLink to="/login">Iniciar sesión</RouterLink>
            </Link>
            <Button
              asChild
              colorPalette="teal"
              mt={2}
              onClick={closeMenu}
            >
              <RouterLink to="/register">Crear cuenta</RouterLink>
            </Button>
          </Stack>
        </Box>
        </Stack>
      </Container>
    </Box>
  );
}

export default Header;
