import { Container, Stack } from "@chakra-ui/react";

import RegisterCompanyForm from "./components/auth/RegisterCompanyForm";
import LoginForm from "./components/auth/LoginForm";

function App() {
  return (
    <Container maxW="container.md" py={10}>
      <Stack gap={10}>
        <RegisterCompanyForm />
        <LoginForm />
      </Stack>
    </Container>
  );
}

export default App;
