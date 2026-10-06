import { Container, Stack } from "@chakra-ui/react";

import ScenarioCard from "./components/scenarios/ScenarioCard";
import AppLayout from "./layouts/AppLayout";

function App() {
  return (
    <AppLayout>
      <Container maxW="container.md">
        <Stack gap={10}>
          <ScenarioCard
            scenarioName="Escenario de Phishing"
            description="Recibes un correo supuestamente de tu banco informando sobre una transacción sospechosa. Te piden verificar tu cuenta haciendo clic en un enlace que te lleva a una página de login idéntica a la real, donde capturan tus credenciales."
            maxTime={90}
            difficulty="Intermedia"
            imageUrl="https://picsum.photos/640/360"
          />
        </Stack>
      </Container>
    </AppLayout>
  );
}

export default App;
