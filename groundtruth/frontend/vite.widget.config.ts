import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    outDir: 'dist/widget',
    lib: {
      entry: 'widget/gt-widget.ts',
      name: 'GroundTruthWidget',
      fileName: () => 'gt-widget.js',
      formats: ['iife'],
    },
    rollupOptions: {
      external: [],
    },
    minify: true,
    sourcemap: false,
  },
});
