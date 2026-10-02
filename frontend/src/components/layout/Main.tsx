import type { ReactNode } from "react";
import { Box } from "@chakra-ui/react";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  return (
    <Box as="main" bg="gray.700" flex="1" px={4} py={10}>
      {children}
    </Box>
  );
}

export default Main;
