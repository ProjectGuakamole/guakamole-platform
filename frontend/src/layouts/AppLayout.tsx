import type { ReactNode } from "react";
import { Box } from "@chakra-ui/react";

import Footer from "../components/layout/Footer";
import Header from "../components/layout/Header";
import Main from "../components/layout/Main";

interface AppLayoutProps {
  children: ReactNode;
}

function AppLayout({ children }: AppLayoutProps) {
  return (
    <Box
      background="var(--app-bg)"
      color="var(--app-fg)"
      display="flex"
      flexDirection="column"
      minH="100vh"
    >
      <Header />
      <Main>{children}</Main>
      <Footer />
    </Box>
  );
}

export default AppLayout;
