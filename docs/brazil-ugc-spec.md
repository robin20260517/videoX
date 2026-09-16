# Brazil UGC Studio — approved product specification

User-authorized implementation, 2026-09-10. Source: videoX da319b7; previous proposed multi-clip workflow is superseded.

## Product

Windows-local web studio around videoX. React + Vite frontend, Python FastAPI local server, SQLite durable jobs, existing videoX Seedance Ark tool. Bind loopback only. Keep original pipelines available. No paid generation during development without configured credentials and an explicit generate action.

## Fixed creative contract

- Exactly 15 seconds, 9:16, one continuous take, no cuts or scene swaps.
- Character: one uploaded image OR one previously saved default character image. Never require multi-view uploads. No other people may be created.
- Scene: Pinterest authorized Board candidates or user-uploaded scene reference. Reference governs environment only.
- Optional game image: sole permitted phone screen content. Prompt prohibits invented/replaced UI. Prompt constraints are instructions, not a pixel-exact model guarantee; result must be reviewed.
- Phone exists from first frame; unique phone; physical contact then pickup then display. Final ~3 seconds stable readable screen.
- Input theme drives pt-BR dialogue. Scene drives sound, continuously moving background details, actor behavior and continuous changes of framing. Timeline beats are within one take, never clips.
- Structured director output must contain hook, dialogue_pt_br, scene_description, background_motion, ambience, action, camera and audio for each timing beat. Compile immutable reference constraints separately from creative text.

## UI

Use actual SmoothUI registry source. Keep component provenance and licenses. Adapt component theme, labels and business wiring only. User's grey design file is authoritative: light canvas #f4f4f5, white cards, #09090b main actions, #ececee borders, 36px cards, 14px controls, 12px tags, restrained #ff5a00 accent. DM Sans substitute; Chinese fallback allowed. No fabricated decorative art or output videos. Empty states must be honest.

## API contract (all paths prefixed /api)

- GET /health => {ok:true}; GET /settings => {llm_base_url,llm_model,ark_model,pinterest_board_id,configured:{llm,ark,pinterest},credential_storage}; PATCH /settings receives optional llm_api_key,ark_api_key,pinterest_access_token and public fields. Secrets never returned. Windows uses keyring/credential manager; other platforms can use environment or available secure keyring, never plain JSON secrets.
- POST /assets multipart file + role(character|scene|game) => Asset. GET /assets?role=... => Asset[]. Asset {id,role,name,url,width,height,is_default,source_url?}. POST /assets/{id}/default selects sole default character. GET /media/{id} returns persisted image; no filesystem paths accepted.
- POST /scenes/search {query,bookmark?} => {items:[{id,title,url,image_url}],bookmark,search_url}. Reads configured authorized Pinterest board, filters candidate metadata with query; does not pretend this is global Pinterest API search. POST /scenes/import {pin_id} => Asset re-fetches Pin via official API, validates i.pinimg.com image URL, capped image download. UI says authorized Board clearly.
- POST /drafts {theme,character_mode:'upload'|'default',character_id?,scene_id,game_id?,dialogue_override?} => Job. GET /jobs => Job[]. GET /jobs/{id} => Job. Jobs {id,theme,status,created_at,updated_at,error?,draft?,prompt?,task_id?,video_url?,request}. Status drafting|draft_ready|submitting|submission_unknown|queued|running|succeeded|failed|interrupted. Draft {title,hook,dialogue_pt_br,scene_description,background_motion,ambience,beats:[{start,end,action,camera,audio}]}. Four beats [0,1.5],[1.5,8.5],[8.5,12],[12,15] in one take. LLM multimodal OpenAI-compatible chat endpoint, credentials configurable, real response validated.
- POST /jobs/{id}/generate => Job; only draft_ready -> submitting, persisted before provider call; duplicate click returns same active job; submits ordered local image references to WaveSpeed `bytedance/seedance-2.0-mini/text-to-video` at 480p, 15s, 9:16, with native audio. No automatic paid resubmission after an uncertain paid POST.
- POST /jobs/generate-batch => Job[]; 1–10 unique jobs, and multi-item submissions must share one batch ID, contain the complete declared variation count and indexes, and all be draft_ready before the atomic transition.
- POST /jobs/{id}/refresh => Job; queries durable provider task id, downloads successful video to local project output; browser reopening can resume polling. Pending draft without a provider task after process interruption is marked interrupted. Submitted task IDs survive restarts.
- GET /videos/{id} returns persisted mp4; GET /jobs/{id}/packet returns prompt and reference map JSON for manual use.

## Acceptance

Given one character and scene, when a theme is submitted, the real LLM drafts scene-specific pt-BR, sound, background motion, action and framing. Given game image, compiled payload preserves reference order character/scene/game and explicit only-screen constraint. Missing character, non-image upload, missing credentials or invalid timing fails visibly. Repeated Generate cannot charge twice. No fake percentage/video/sample assets. Job and media persist across server restart.

## External verification boundary

Without user's provider credentials, external paid generation and authenticated Pinterest requests cannot be verified live. Contract tests exercise real local logic with HTTP-boundary doubles; report that distinction. Windows scripts can be reviewed on Linux, but native Windows installation needs Windows validation.
