import { Box, Text } from "@chakra-ui/react";

function Footer() {
  return (
    <Box as="footer" bg="gray.700" px={8} py={4}>
      <Text color="white" textStyle="sm" fontWeight="medium">
        Footer
      </Text>
    </Box>
  );
}

export default Footer;
