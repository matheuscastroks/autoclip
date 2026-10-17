import { defineConfig, type Plugin } from 'vite';
import vue from '@vitejs/plugin-vue';
import Icons from 'unplugin-icons/vite';
import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';

interface BackendSession {
  port?: number;
  token?: string;
  pid?: number;
  workspace?: string;
}

const currentDir = path.dirname(fileURLToPath(import.meta.url));

function getBackendSession(): BackendSession | null {
  try {
    const sessionPath = path.resolve(currentDir, '../.autoclip/session.json');
    if (fs.existsSync(sessionPath)) {
      const content = fs.readFileSync(sessionPath, 'utf-8');
      return JSON.parse(content) as BackendSession;
    }
  } catch {
    // Session file might not exist or be mid-write
  }
  return null;
}

function autoSessionPlugin(): Plugin {
  return {
    name: 'autoclip-auto-session',
    transformIndexHtml(html: string) {
      const session = getBackendSession();
      if (session?.token) {
        return html.replace(
          '</head>',
          `<script>if (!window.location.hash.includes('session=')) { window.location.hash = 'session=' + ${JSON.stringify(session.token)}; }</script></head>`
        );
      }
      return html;
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url || (!req.url.startsWith('/api/') && !req.url.startsWith('/media/'))) {
          return next();
        }

        const session = getBackendSession();
        const port =
          session?.port || (process.env.AUTOCLIP_PORT ? Number(process.env.AUTOCLIP_PORT) : null);
        if (!port) {
          res.statusCode = 502;
          res.setHeader('Content-Type', 'application/json');
          res.end(
            JSON.stringify({
              detail:
                'Motor local não encontrado. Inicie o serviço local do AutoClip (.venv/Scripts/autoclip-engine.exe ou serve.py).',
            })
          );
          return;
        }

        const headers = { ...req.headers };
        headers.host = `127.0.0.1:${port}`;
        headers.origin = `http://127.0.0.1:${port}`;
        const auth = headers['authorization'];
        if (session?.token && (!auth || auth === 'Bearer' || auth === 'Bearer ')) {
          headers['authorization'] = `Bearer ${session.token}`;
        }

        const proxyReq = http.request(
          {
            hostname: '127.0.0.1',
            port,
            path: req.url,
            method: req.method,
            headers,
          },
          (proxyRes) => {
            res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
            proxyRes.pipe(res);
          }
        );

        proxyReq.on('error', (err) => {
          if (!res.headersSent) {
            res.writeHead(502, { 'Content-Type': 'application/json' });
            res.end(
              JSON.stringify({
                detail: `Falha de comunicação com o motor local na porta ${port}: ${err.message}`,
              })
            );
          }
        });

        req.pipe(proxyReq);
      });
    },
  };
}

export default defineConfig({
  plugins: [
    vue(),
    autoSessionPlugin(),
    Icons({ compiler: 'vue3', autoInstall: false }),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: false })],
    }),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    maxWorkers: 2,
    testTimeout: 15000,
    setupFiles: ['./tests/setup.ts'],
  },
  server: {
    host: '127.0.0.1',
  },
});
