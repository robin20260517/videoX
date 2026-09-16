# Brazil UGC Studio Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development for the bounded frontend task and independent review; primary agent implements backend integration.

**Goal:** Deliver a working Windows-local web UI and real configurable videoX generation backend.

**Architecture:** Preserve videoX tools. Add studio/ local server and studio-web/ frontend; deterministic validation surrounds LLM creative generation. SQLite persists tasks and assets.

**Tech Stack:** Python FastAPI, SQLite, Pillow, requests, keyring; React, Vite, TypeScript, Tailwind, official SmoothUI.

**Spec:** docs/brazil-ugc-spec.md

## Global Constraints

One character image; fixed 15 seconds 9:16 one take; optional game image is sole screen content. Theme + scene determine pt-BR, movement, audio, camera. Official SmoothUI components; grey design tokens. No fake provider results. Loopback binding and no plaintext credential persistence.

### Task 1: Domain, persistence and provider bridge

Files: studio/models.py, studio/store.py, studio/director.py, studio/providers.py, tests/studio/test_contract.py.
Interfaces: validated Brief and Draft; compile_prompt; durable Store; generate via existing SeedanceArkVideo create/query.

- [x] Add tests rejecting missing refs and bad timing; assert single-person prompt constraints, image-reference order and duration at outgoing provider boundary.
- [x] Run tests before implementation. Initial suite failed on absent modules/dependencies; this is not full behavioral red/green evidence. Later scene-query and review-fix regressions have explicit behavioral failures before fixes.
- [x] Implement image validation, draft schema, dynamic multimodal director and strict prompt compilation.
- [x] Implement SQLite storage and secret configuration without browser exposure.
- [x] Verify durable jobs, duplicate-submit protection, network ambiguity handling.

### Task 2: SmoothUI frontend

Files: studio-web/**; exact task brief docs/frontend-task.md.
Consumes API contract in spec. Produces built studio-web/dist.

- [x] Fetch actual official registry components and retain provenance.
- [x] Implement theme, uploads, default character, Pinterest Board selection, draft review, generate, history, settings and download.
- [x] Test interaction-to-request mapping; run typecheck/build and local browser validation. Live provider workflow remains unverified.

### Task 3: HTTP integration and Windows launcher

Files: studio/app.py, studio/__main__.py, requirements-studio.txt, scripts/start-studio.ps1, Start Studio.cmd, README_STUDIO.md, pipeline_defs/brazil-ugc-game-ad.yaml, skills/pipelines/brazil-ugc-game-ad/**.

- [x] Write API tests for rejected uploads, missing configuration, default selection, persistence and duplicate generation.
- [x] Implement routes and local static frontend; protect local requests with same-origin + trusted host loopback checks (not multi-user authentication).
- [x] Add pipeline manifest/director skills and launch/setup documentation.
- [x] Run backend suite, frontend checks, real local browser and build smoke checks.
- [x] Perform independent review and fix concrete findings. Record unavailable live-provider and Windows checks.
