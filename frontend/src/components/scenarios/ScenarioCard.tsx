import { Badge, Card, Image, Stack, Text } from "@chakra-ui/react";

export interface ScenarioCardProps {
  scenarioName: string;
  description: string;
  maxTime: number;
  difficulty: string;
  imageUrl: string;
}

function ScenarioCard({
  scenarioName,
  description,
  maxTime,
  difficulty,
  imageUrl,
}: ScenarioCardProps) {
  return (
    <Card.Root
      width="320px"
      overflow="hidden"
      transition="transform 0.2s ease, box-shadow 0.2s ease"
      _hover={{ transform: "translateY(-4px)", boxShadow: "lg" }}
    >
      <Image
        src={imageUrl}
        alt={scenarioName}
        height="180px"
        objectFit="cover"
        width="full"
      />
      <Card.Body gap="3">
        <Card.Title>{scenarioName}</Card.Title>
        <Card.Description>{description}</Card.Description>
        <Stack align="flex-start" gap="2" pt="2">
          <Text>Tiempo máximo: {maxTime} min</Text>
          <Badge colorPalette="purple">Dificultad: {difficulty}</Badge>
        </Stack>
      </Card.Body>
    </Card.Root>
  );
}

export default ScenarioCard;
