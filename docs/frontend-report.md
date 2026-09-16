# Frontend implementation report

Completed 2026-09-10. Scope: `studio-web/**` and this report only. No backend edits or commits.

## Delivered

- React + Vite TypeScript + Tailwind v4 studio; 5173 loopback development proxy to 8787; production `dist/` build.
- Actual SmoothUI official registry source for smooth-button, animated-input, animated-file-upload, animated-tabs. Original JSON, MIT license and attribution preserved under `vendor/smoothui/`. Theme adaptations use the user's grey design file: #f4f4f5 canvas, white cards, 36px main card radius, 14px controls, restrained orange pt-BR badge. DM Sans font assets are bundled.
- Theme, single character upload/default library, scene upload/authorized Pinterest Board search/import, optional game image, pt-BR override, director draft, continuous four-beat review, complete prompt expansion, manual packet export and explicit video submission.
- Pinterest optional keywords fall back to the theme; backend `recommended_query` is displayed when supplied. Search copy explicitly identifies the authorized Board and exposes the external `search_url`.
- Settings PATCH stores no browser secrets; GET booleans display configuration state. Blank secret inputs preserve existing secrets. Submission explicitly labels Seedance Ark and the configured model/default model.
- Backend-restored job history, returned video playback/download, visible errors, pending-button locks and no automatic paid resubmission. Polls about every 10 seconds with a request guard, including `submission_unknown` only when a task id exists. No fake percentages, videos or default actor images.
- Source formatted with Prettier. DraftReview, SettingsPanel and shared presentation helpers extracted from App.

## Verification

- `pnpm build`: PASS (production JavaScript ~418.5 kB, ~134.5 kB gzip).
- `pnpm typecheck`: PASS.
- `pnpm test`: PASS, 9 tests in 2 files. Covers image validation, theme/character validation, network failure, multipart upload and persisted reference display, provider draft errors, history restore, duplicate Generate lock, Pinterest theme fallback and uncertain-submission polling conditions.
- Isolated Chromium desktop (1440px) and mobile (390px) screenshots inspected using mocked GET API data. Mobile document scrollWidth equals viewport width (390px). These test responses contain empty arrays, no fabricated assets. Screenshots: `/tmp/studio-desktop.png`, `/tmp/studio-mobile.png` (temporary review artifacts, not committed).
- Fixed Unicode/Windows Vite alias path handling exposed during the build.

## Integration boundary

The local API was not listening on 8787 during the frontend smoke check, so the primary agent must finish real local API/browser integration verification. Authenticated Pinterest, real LLM drafting and paid Seedance generation were not called. Native Windows startup/install requires Windows validation. Browser screenshot checks exercise empty-state layout and genuine component behavior using HTTP-boundary responses; they are not provider integration tests.

Dev server remains available on `http://127.0.0.1:5173` for integration review (terminal session 91147). No user browser profile or credentials were used.
