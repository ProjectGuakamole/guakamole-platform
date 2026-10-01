<<<<<<< HEAD
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'
=======
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
>>>>>>> d32ee92b3ae9753e514125e7dd6b7f50dec5fc07

export default defineConfig({
  plugins: [react()],
<<<<<<< HEAD
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
=======
  resolve: {
    tsconfigPaths: true,
  },
});
>>>>>>> d32ee92b3ae9753e514125e7dd6b7f50dec5fc07
