import { Box, Container, HStack, Link, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

function Footer() {
  return (
    <Box
      as="footer"
      background="var(--app-header)"
      borderTop="1px solid"
      borderColor="var(--app-border)"
      py={6}
    >
      <Container maxW="7xl">
        <HStack
          align={{ base: "flex-start", sm: "center" }}
          justify="space-between"
          gap={3}
          flexDirection={{ base: "column", sm: "row" }}
        >
          <Text color="var(--app-text-subtle)" fontSize="sm">
            © Guakamole · Entrenamiento práctico en ciberseguridad.
          </Text>
          <Link
            asChild
            color="var(--app-text-subtle)"
            fontSize="sm"
            _hover={{ color: "var(--app-accent)", textDecoration: "none" }}
          >
            <RouterLink to="/#inicio">Volver al inicio ↑</RouterLink>
          </Link>
        </HStack>
      </Container>
    </Box>
  );
}

export default Footer;
