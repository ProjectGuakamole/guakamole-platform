import type { ReactNode } from "react";
import { Box } from "@chakra-ui/react";

interface MainProps {
  children: ReactNode;
}

function Main({ children }: MainProps) {
  return (
    <Box as="main" background="#0b1018" flex="1">
      {children}
    </Box>
  );
}

export default Main;
