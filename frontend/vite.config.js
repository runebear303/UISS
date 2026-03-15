import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,         // Dit zorgt ervoor dat Vite luistert op alle netwerkinterfaces (0.0.0.0)
    port: 3000,         // Zorg dat dit overeenkomt met je Dockerfile en docker-compose
    watch: {
      usePolling: true, // Cruciaal voor Windows: zorgt dat wijzigingen in je code direct verwerkt worden
    },
  },
})
