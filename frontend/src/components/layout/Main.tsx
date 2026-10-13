import type { ReactNode } from "react";
import { Box } from "@chakra-ui/react";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  return (
    <Box as="main" background="var(--app-bg)" flex="1">
      {children}
    </Box>
  );
}

export default Main;
