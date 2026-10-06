import { Box, Container, HStack, Link, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

function Footer() {
  return (
    <Box
      as="footer"
      background="rgba(8, 12, 20, 0.96)"
      borderTop="1px solid"
      borderColor="rgba(255, 255, 255, 0.08)"
      py={6}
    >
      <Container maxW="7xl">
        <HStack
          align={{ base: "flex-start", sm: "center" }}
          justify="space-between"
          gap={3}
          flexDirection={{ base: "column", sm: "row" }}
        >
          <Text color="gray.400" fontSize="sm">
            © Guakamole · Entrenamiento práctico en ciberseguridad.
          </Text>
          <Link
            asChild
            color="gray.400"
            fontSize="sm"
            _hover={{ color: "teal.200", textDecoration: "none" }}
          >
            <RouterLink to="/#inicio">Volver al inicio ↑</RouterLink>
          </Link>
        </HStack>
      </Container>
    </Box>
  );
}

export default Footer;
