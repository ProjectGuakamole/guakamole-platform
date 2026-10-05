import { Box, Text } from "@chakra-ui/react";

function Header() {
  return (
    <Box as="header" bg="gray.700" px={8} py={4}>
      <Text color="white" textStyle="2xl" fontWeight="bold">
        Header
      </Text>
    </Box>
  );
}

export default Header;
