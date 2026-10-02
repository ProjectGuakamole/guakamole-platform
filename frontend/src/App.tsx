import { Container, Stack } from "@chakra-ui/react";

import RegisterCompanyForm from "./components/auth/RegisterCompanyForm";
import LoginForm from "./components/auth/LoginForm";
import AppLayout from "./layouts/AppLayout";

function App() {
  return (
    <AppLayout>
      <Container maxW="container.md">
        <Stack gap={10}>
          <RegisterCompanyForm />
          <LoginForm />
        </Stack>
      </Container>
    </AppLayout>
  );
}

export default App;
