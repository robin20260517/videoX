# Independent review fixes — 2026-09-10

## Changes

- Removed the silent 100-job history cap. Recovery and background provider polling now use a separate unrestricted active-state query, so an older paid task remains eligible after more than 100 newer jobs.
- Current and historical draft review shows character, scene and game images resolved from the job's saved request IDs. Changing the form or default character cannot change those review references. Missing references are explicitly labeled.
- Added required, whitespace-trimmed, nonempty `hook` (maximum 1000 characters) to the validated director draft, artifact schema, director instruction, compiled prompt and draft review. Existing stored drafts can still be displayed without a hook. The 15-second, one-person, one-take and screen-reference constraints remain in place.
- Windows launcher checks a SHA256 fingerprint of frontend source, public assets, package/lockfile, HTML and configuration inputs. It rebuilds changed inputs and only writes `dist/inputs.sha256` after success. Packaging can reuse `studio.frontend_build.fingerprint` to stamp a prebuilt bundle.
- Aligned main/header/footer width to 1200px, kept 36px cards on mobile, and replaced arbitrary secondary radii with the existing 14px control token. SmoothUI component sources were not rewritten.
- Provider success regression now performs submission and its approved script/generation checkpoints before querying success, and asserts the restored job has no error.

## Verification

Before implementation, regressions failed on the 100-job cap, rejected hook field and missing historical actor image. The build-fingerprint test initially failed because the module did not exist.

- `.venv/bin/python -m pytest tests/studio -q`: 24 passed; two upstream FastAPI/Starlette deprecation warnings. Local API tests ran with sandbox escalation because this environment's sandbox stalls asyncio/TestClient.
- `pnpm exec vitest run`: 10 passed, including historical actor A after default changes to B and all three reference images.
- `pnpm build`: TypeScript and Vite production build passed.
- Fingerprint regression proves source/config/lock changes alter the hash while generated dist output does not.

Native Windows launcher execution, authenticated Pinterest, and live paid provider generation were not exercised on Linux. Browser visual evidence and final packaging are handled in the main review task.
