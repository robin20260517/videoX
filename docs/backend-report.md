# Backend implementation evidence

Domain/API/provider suite: 16 passed in 1.55s; includes actual existing Ark payload construction with network-boundary substitutes, image ingest, SQLite concurrency, missing config, and origin/host isolation. Scene search test: first failed with missing recommended_query, then 5 passed after implementation. Initial API RED was missing studio.app; initial domain import failed before implementation. Do not describe missing-module checks as complete red/green behavioral evidence for all code. Dependencies were initially unavailable and the full test framework installed during work.

Existing upstream Seedance tool unchanged, imported through ToolRegistry.register_module and registry.get. New custom pipeline ugc_script/ugc_generate and artifact schemas; LLM reads scene and actor images with installed director guidance translated into project skill. Prompt compiled with fixed single-take and reference ownership rules. Persistent async task id, preflight, no paid retry on uncertain POST, server-side refresh/download.

Known boundaries: live LLM/Ark/Pinterest calls not verified without user credentials; Windows launcher source written on Linux and not natively executed. Actual video content QA is a human review requirement, no false automated face/phone quality claims. Default actor is a user-saved library photo, no fake bundled actor. Pinterest is authenticated Board search, not unauthorized anonymous crawl. Non-Windows secrets use environment; Windows uses keyring.

Test output has 2 upstream deprecation warnings (Starlette httpx compatibility, AnyIO portal alias). No app test failures. Local asynchronous TestClient deadlocked inside sandbox before lifespan startup; rerun with approved local communication permissions completed in under two seconds.

Git commit attempted but current environment has no author identity; changes remain locally staged. No global Git config changed, no remote push.
