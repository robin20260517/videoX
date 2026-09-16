# videoX 巴西 UGC 工作室

React 19 + Vite + TypeScript + Tailwind CSS v4, with official SmoothUI registry components. DM Sans is bundled locally; Chinese text uses the system Chinese fallback.

```sh
pnpm install
pnpm dev
```

The development server binds `127.0.0.1:5173`, proxying `/api` to `http://127.0.0.1:8787`. Start the Python studio API separately using the repository's studio instructions.

```sh
pnpm typecheck
pnpm test
pnpm build
```

Production assets are emitted to `dist/` for the local Python server to serve. The Vite alias uses `fileURLToPath` for Windows and Unicode-path support.

`src/App.tsx` owns API loading, uploads, scene selection and polling; `components/DraftReview.tsx` and `components/SettingsPanel.tsx` own draft review and settings. `api.ts` contains the shared wire types and HTTP error handling; `status.ts` defines the polling conditions.

Secrets are sent only to `/api/settings` and cleared after a successful save. Nothing is stored in browser localStorage. History is reloaded from the backend. The browser does not create sample videos, figures or sample reference images.

SmoothUI original registry payloads, attribution and MIT license are in `vendor/smoothui/`. Local changes preserve their interaction implementation while adapting labels, input password support and the required grey theme.

Tests use real React/SmoothUI components with HTTP-boundary doubles. They do not call paid providers. Live credentials and native Windows validation remain integration checks.
