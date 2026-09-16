# SDD progress — docs/superpowers/plans/2026-09-10-brazil-ugc.md

2026-09-10: implementation authorized by user (执行).

| Work | Shared interface | Validation |
|---|---|---|
| Domain/provider → server | Brief, Draft, Store, StudioService | Validated image-role map, 15s payload, durable provider task ID |
| Server → frontend | docs/brazil-ugc-spec.md API contract | Matching endpoints and request names; real localhost browser connected |
| Default actor → approval | request.character_id snapshot | Saved reference previews fixed; frontend regression passed |
| Job history → background worker | SQLite jobs | Unrestricted active query fixed; >100-job regression passed |
| Windows launcher → frontend dist | source/build fingerprint | Source hash rebuild implemented; cross-platform ordering and generated-file exclusions tested |

Completed: official SmoothUI frontend, typed API, image ingestion, default-character library, scene-conditioned LLM director, strict one-take compiler, official Pinterest Board reader/import, Seedance Ark preflight/create/query, SQLite tasks, Windows starter, pipeline manifest + project skills and artifacts.

Evidence before review fixes: frontend 9 passed plus typecheck/build; studio backend 21 passed; unchanged Seedance/checkpoint regressions 54 passed. Two upstream Python deprecation warnings recorded in backend-report.md. No paid or authenticated provider calls performed.

Independent review by studio_review: two important findings (old paid jobs excluded; approval refs wrong) and two minor findings (Windows UI rebuild; structured hook). Assigned one scoped fix agent, then scoped re-review. No data deletion, remote push, or Git identity changes. Git commit unavailable because author identity is not configured; local files remain available.

Final backend verification: 78 passed (24 Studio and 54 unchanged upstream regressions), two dependency deprecation warnings. Frontend: 10 passed, typecheck and production build passed. Re-review confirmed all four findings resolved. Packaging now requires essential sources staged and builds the frontend before stamping its source hash. ZIP audit passed: 2162 files, 74.2 MiB, essential sources and licenses present, no runtime data/secrets/virtualenv/node_modules; extracted frontend fingerprint matches the packaged build marker. Most archive size comes from upstream example videos retained with the source. Authenticated external services and native Windows execution are not verified.

Implementation choices: current default character is a saved one-photo library item; no random default actor asset. Current non-Windows build uses environment secrets; Windows uses OS credential manager. Source ZIP includes compiled frontend and source/license, excludes credentials/user media.

2026-09-11 live Ark verification: Seedance 2.0 Mini authentication and model discovery succeeded, and provider task `cgt-20260911144733-mgcv7` produced a 15.104-second 720×1280 H.264/AAC video with generated audio. Live testing led to explicit `@图像1/2/3` bindings, `omni_reference_task_type=reference`, deterministic portrait-policy rejection handling, metadata-free WebP ingestion, and Mini as the fresh-install default. Final verification is 80 backend tests and 11 frontend tests plus typecheck/build. Sampled visual QC confirmed one character, one phone and no abrupt cut; the model nevertheless invented small phone-screen status details, so strict screen-pixel fidelity remains a required human review/retake or post-production step.
