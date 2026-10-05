import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ScenarioCard from "./ScenarioCard";
import { renderWithProviders } from "../../test/testUtils";

describe("ScenarioCard", () => {
  it("renders the image and scenario details", () => {
    // Renderiza un escenario de ejemplo con todos los datos que recibe la card.
    renderWithProviders(
      <ScenarioCard
        scenarioName="Escenario de Phishing"
        description="Recibes un correo supuestamente de tu banco informando sobre una transacción sospechosa. Te piden verificar tu cuenta haciendo clic en un enlace que te lleva a una página de login idéntica a la real, donde capturan tus credenciales. 

"
        maxTime={90}
        difficulty="Intermedia"
        imageUrl="https://picsum.photos/200/300"
      />,
    );

    // Comprueba que la imagen y el título se identifican correctamente.
    expect(
      screen.getByRole("img", { name: "Escenario de Phishing" }),
    ).toHaveAttribute("src", "https://picsum.photos/200/300");
    expect(
      screen.getByRole("heading", { name: "Escenario de Phishing" }),
    ).toBeInTheDocument();

    // Verifica que también se muestran la descripción y los datos del escenario.
    expect(
      screen.getByText(
        "Recibes un correo supuestamente de tu banco informando sobre una transacción sospechosa. Te piden verificar tu cuenta haciendo clic en un enlace que te lleva a una página de login idéntica a la real, donde capturan tus credenciales.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Tiempo máximo: 90 min")).toBeInTheDocument();
    expect(screen.getByText("Dificultad: Intermedia")).toBeInTheDocument();
  });
});
