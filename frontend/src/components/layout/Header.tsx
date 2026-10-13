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
import { ColorModeButton } from "../ui/color-mode";

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const closeMenu = () => setIsMenuOpen(false);

  return (
    <Box
      as="header"
      background="var(--app-header)"
      borderBottom="1px solid"
      borderColor="var(--app-border)"
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
                  background="var(--app-accent-soft)"
                  border="1px solid"
                  borderColor="var(--app-border-strong)"
                  borderRadius="lg"
                  color="var(--app-accent)"
                  display="flex"
                  fontSize="lg"
                  fontWeight="bold"
                  h={10}
                  justifyContent="center"
                  w={10}
                >
                  G
                </Box>
                <Text color="var(--app-fg)" fontSize="xl" fontWeight="bold">
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
              color="var(--app-text-muted)"
              _hover={{ color: "var(--app-accent)", textDecoration: "none" }}
            >
              <RouterLink to="/#inicio">La plataforma</RouterLink>
            </Link>
            <Link
              asChild
              color="var(--app-text-muted)"
              _hover={{ color: "var(--app-accent)", textDecoration: "none" }}
            >
              <RouterLink to="/beneficios">Beneficios</RouterLink>
            </Link>
            <Link
              asChild
              color="var(--app-text-muted)"
            >
              <RouterLink to="/login">Iniciar sesión</RouterLink>
            </Link>
            <Button asChild colorPalette="teal" size="sm">
              <RouterLink to="/register">Crear cuenta</RouterLink>
            </Button>
            <ColorModeButton display={{ base: "none", md: "inline-flex" }} />
          </HStack>

          <ColorModeButton display={{ base: "inline-flex", md: "none" }} />
          <IconButton
            aria-label={isMenuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-controls="mobile-navigation"
            aria-expanded={isMenuOpen}
            display={{ base: "inline-flex", md: "none" }}
            onClick={() => setIsMenuOpen((open) => !open)}
            variant="ghost"
            color="var(--app-fg)"
          >
            {isMenuOpen ? <FiX /> : <FiMenu />}
          </IconButton>
        </HStack>
        <Box
          as="nav"
          aria-label="Navegación móvil"
          borderTop="1px solid"
          borderColor="var(--app-border)"
          display={{ base: isMenuOpen ? "block" : "none", md: "none" }}
          id="mobile-navigation"
          pb={4}
          pt={2}
        >
          <Stack align="stretch" gap={1}>
            <Link
              asChild
              color="var(--app-text-muted)"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "var(--app-hover)", textDecoration: "none" }}
            >
              <RouterLink to="/#inicio">La plataforma</RouterLink>
            </Link>
            <Link
              asChild
              color="var(--app-text-muted)"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "var(--app-hover)", textDecoration: "none" }}
            >
              <RouterLink to="/beneficios">Beneficios</RouterLink>
            </Link>
            <Link
              asChild
              color="var(--app-text-muted)"
              onClick={closeMenu}
              px={3}
              py={2}
              _hover={{ bg: "var(--app-hover)", textDecoration: "none" }}
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
