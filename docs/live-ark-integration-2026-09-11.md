# Seedance 2.0 Mini live integration — 2026-09-11

## Surface and credential handling

- Surface: Volcengine Ark, Beijing region, official asynchronous video-generation API.
- Model: `doubao-seedance-2-0-mini-260615`.
- Official create endpoint: `POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`.
- The supplied API key was used only from a process environment. It is not stored in the repository, SQLite database, ZIP, generated artifacts, or this report.
- The official create-task page was checked live on 2026-09-11; the page itself showed an update time of 2026-09-09. It documents Bearer API-key authentication, the asynchronous task ID response, reference media roles, `omni_reference_task_type`, 15-second duration, 9:16 ratio, 720p, and generated audio.

Official reference: <https://console.volcengine.com/ark/region:cn-beijing/docs/82379/1520757?lang=zh>

## Preflight and task result

- `GET /api/v3/models`: HTTP 200, 131 visible models, requested Mini model present.
- Final request: three ordered images (fictional identity, environment, sole phone-screen artwork), `reference_to_video`, `omni_reference_task_type=reference`, 15 seconds, 9:16, 720p, generated audio.
- Local preflight: 324,000 estimated completion tokens; list-price estimate ¥7.452 before any account promotion. The live docs advertised a temporary Mini discount; the billing console remains authoritative.
- Provider task: `cgt-20260911144733-mgcv7`.
- Result: succeeded; 324,900 completion tokens; provider duration 15 seconds; 9:16; 720p; 24 fps; generated audio; seed 91814.
- Local artifact: `.studio/projects/c3fb032d07d14932af13255f64ab3d40/renders/final.mp4` (12,059,564 bytes). Probe result: H.264 720×1280 at 24 fps plus stereo AAC 32 kHz, container duration 15.104 seconds.

## Findings and fixes made during the live test

1. The original prompt named references as plain “图片1/2/3”. Ark's current full-modal example uses explicit `@图像1` bindings. The compiler now emits those exact bindings, and the adapter sends `omni_reference_task_type=reference`.
2. A photo-real synthetic face was rejected before task creation as possible real-person/privacy content. Deterministic 4xx input rejections now become a clear failed state rather than the ambiguous-submission state. The UI-facing error instructs the operator to use a clearly fictional character or complete Ark's portrait authorization flow.
3. PNG-normalized uploads caused create acknowledgements to exceed 30 and then 120 seconds; the provider task list confirmed that neither timed-out request created a task. New uploads are now normalized to metadata-free WebP (quality 88 for actor/scene and 94 for game UI), reducing the three test references from roughly 6.5 MB to roughly 0.66 MB. The successful create then returned a task ID normally.
4. Fresh installs now default to Seedance 2.0 Mini rather than silently falling back to Standard.

## Human visual/audio QC boundary

- Passed in sampled frames: one character, one phone, same room, continuous camera progression, visible touch/lift/turn sequence, and stable final three-second phone hold.
- Failed strict screen-pixel fidelity: the final screen preserved the supplied puzzle layout but added small numeric/status details at the top that were not present in the source image. This confirms that prompt binding is not a pixel guarantee. Use a retake or post-production screen replacement for release material.
- An AAC stereo track is present with usable measured level (mean -24.7 dB, peak -3.6 dB). Portuguese pronunciation and lip synchronization were not transcribed automatically and still require a native-speaker listening pass.
- Scene-cut detection at threshold 10 found no abrupt cut in the generated file. This is supporting evidence, not a substitute for watching the full clip.
