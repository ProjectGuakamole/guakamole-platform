import type { ReactNode } from "react";
import { Box, Container, Heading, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import landingBackground from "../../assets/landing-background.png";

interface AuthPageProps {
  title: string;
  description: string;
  alternateText: string;
  alternateLabel: string;
  alternateTo: string;
  children: ReactNode;
}

function AuthPage({
  title,
  description,
  alternateText,
  alternateLabel,
  alternateTo,
  children,
}: AuthPageProps) {
  return (
    <Box
      as="section"
      backgroundImage={`linear-gradient(110deg, rgba(7, 11, 19, 0.97), rgba(7, 11, 19, 0.86)), url("${landingBackground}")`}
      backgroundPosition="center"
      backgroundSize="cover"
      minH="calc(100vh - 152px)"
      py={{ base: 12, md: 16 }}
    >
      <Container maxW="7xl">
        <SimpleGrid
          alignItems="start"
          columns={{ base: 1, lg: 2 }}
          gap={{ base: 10, lg: 20 }}
        >
          <Stack gap={5} pt={{ lg: 10 }}>
            <Text
              color="teal.200"
              fontSize="sm"
              fontWeight="bold"
              letterSpacing="wider"
              textTransform="uppercase"
            >
              Guakamole · Ciberseguridad práctica
            </Text>
            <Heading
              as="h1"
              color="white"
              fontSize={{ base: "3xl", md: "5xl" }}
              lineHeight="1.12"
            >
              {title}
            </Heading>
            <Text color="gray.300" fontSize="lg" lineHeight="1.8" maxW="lg">
              {description}
            </Text>
            <Text color="gray.400" fontSize="sm">
              {alternateText}{" "}
              <Link asChild color="teal.200" fontWeight="semibold">
                <RouterLink to={alternateTo}>{alternateLabel}</RouterLink>
              </Link>
            </Text>
          </Stack>
          <Box
            backdropFilter="blur(16px)"
            background="rgba(12, 19, 31, 0.82)"
            border="1px solid"
            borderColor="rgba(255, 255, 255, 0.14)"
            borderRadius="2xl"
            boxShadow="0 24px 80px rgba(0, 0, 0, 0.32)"
            p={{ base: 5, md: 8 }}
            width="full"
          >
            {children}
          </Box>
        </SimpleGrid>
      </Container>
    </Box>
  );
}

export default AuthPage;
