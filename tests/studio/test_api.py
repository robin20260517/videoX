import io
from concurrent.futures import ThreadPoolExecutor
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from studio.app import create_app


def image_file():
    buffer = io.BytesIO()
    Image.new('RGB', (600, 800), '#eeeeee').save(buffer, 'PNG')
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app, base_url='http://127.0.0.1:8787') as client:
        yield client


def upload(client, role):
    result = client.post('/api/assets', data={'role': role}, files={'file': ('image.png', image_file(), 'image/png')})
    assert result.status_code == 200, result.text
    return result.json()


def test_rejects_disguised_non_image_and_does_not_persist(client):
    result = client.post('/api/assets', data={'role': 'character'}, files={'file': ('face.png', b'<script>alert(1)</script>', 'image/png')})
    assert result.status_code == 422
    assert client.get('/api/assets').json() == []


def test_uploaded_media_and_default_are_persisted(client):
    actor = upload(client, 'character')
    assert 'path' not in actor
    media = client.get(actor['url'])
    assert media.headers['content-type'] == 'image/webp'
    assert media.content.startswith(b'RIFF') and b'WEBP' in media.content[:16]
    assert client.post(f"/api/assets/{actor['id']}/default").json()['is_default'] is True
    scene = upload(client, 'scene')
    assert client.post(f"/api/assets/{scene['id']}/default").status_code == 422


def test_bundled_character_and_scene_are_imported_once_and_served_locally(tmp_path):
    library = tmp_path / 'builtin'
    for role, name, color in [('character', 'actor.jpg', '#ba906d'), ('scene', 'room.webp', '#d3c5aa')]:
        folder = library / role
        folder.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (600, 800), color).save(folder / name)
    data = tmp_path / 'data'

    first = create_app(data, builtin_dir=library)
    with TestClient(first, base_url='http://127.0.0.1:8787') as local:
        assets = local.get('/api/assets').json()
        assert {(asset['role'], asset['name']) for asset in assets} == {
            ('character', 'actor.jpg'), ('scene', 'room.webp'),
        }
        assert all(asset['source_url'].startswith('builtin://') for asset in assets)
        assert all(not asset['is_default'] for asset in assets)
        for asset in assets:
            media = local.get(asset['url'])
            assert media.status_code == 200
            assert media.content.startswith(b'RIFF')
            if asset['role'] == 'scene':
                assert media.content == (library / 'scene' / 'room.webp').read_bytes()

    second = create_app(data, builtin_dir=library)
    with TestClient(second, base_url='http://127.0.0.1:8787') as local:
        restored = local.get('/api/assets').json()
        assert {asset['id'] for asset in restored} == {asset['id'] for asset in assets}


def test_missing_credentials_does_not_create_fake_draft(client, monkeypatch):
    from studio.config import Settings
    monkeypatch.setattr(Settings, 'secret', lambda self, key: '')
    actor, scene = upload(client, 'character'), upload(client, 'scene')
    result = client.post('/api/drafts', json={'theme': '厨房游戏', 'character_mode': 'upload', 'character_id': actor['id'], 'scene_id': scene['id']})
    assert result.status_code == 409
    assert client.get('/api/jobs').json() == []


def test_cross_site_cannot_read_settings_or_upload(client):
    assert client.get('/api/settings', headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.get('/api/settings', headers={'Host': 'evil.example'}).status_code == 400


def test_seedance_mini_is_the_fresh_install_default(client):
    assert client.get('/api/settings').json()['ark_model'] == 'doubao-seedance-2-0-mini-260615'


def test_wavespeed_seedance_20_mini_480p_is_the_fresh_video_backend_default(client):
    settings = client.get('/api/settings').json()
    assert settings['video_provider'] == 'wavespeed'
    assert settings['wavespeed_model'] == 'bytedance/seedance-2.0-mini/text-to-video'
    assert settings['wavespeed_resolution'] == '480p'


def test_deepseek_vision_is_the_fresh_multimodal_director_default(tmp_path, monkeypatch):
    from studio.config import Settings
    from studio.store import Store
    monkeypatch.delenv('STUDIO_LLM_BASE_URL', raising=False)
    monkeypatch.delenv('STUDIO_LLM_MODEL', raising=False)
    settings = Settings(Store(tmp_path)).get()
    assert settings['llm_base_url'] == 'https://api.deepseek.com'
    assert settings['llm_model'] == 'deepseek-v4-flash-vision-exp'


def test_generate_duplicate_request_submits_only_once(client, monkeypatch):
    app = client.app
    actor, scene = upload(client, 'character'), upload(client, 'scene')
    job = app.state.store.create_job({'theme': '厨房游戏', 'character_mode': 'upload', 'character_id': actor['id'], 'scene_id': scene['id']})
    app.state.store.update_job(job['id'], status='draft_ready', prompt='one take')
    monkeypatch.setattr(app.state.settings, 'require', lambda provider: None)
    submitted = []
    def submit(job_id):
        submitted.append(job_id)
        app.state.store.update_job(job_id, status='queued', task_id='task-test')
    monkeypatch.setattr(app.state.service, 'submit', submit)
    r1 = client.post(f"/api/jobs/{job['id']}/generate")
    r2 = client.post(f"/api/jobs/{job['id']}/generate")
    assert r1.status_code == r2.status_code == 200
    assert submitted == [job['id']]


def test_atomic_submission_under_parallel_calls(client):
    store = client.app.state.store
    job = store.create_job({'theme': '并发'})
    store.update_job(job['id'], status='draft_ready')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: store.claim_submission(job['id']), range(8)))
    assert results.count(True) == 1


def test_batch_drafts_create_ten_independent_nonduplicate_contracts(client, monkeypatch):
    app = client.app
    actor, scene, game = upload(client, 'character'), upload(client, 'scene'), upload(client, 'game')
    monkeypatch.setattr(app.state.settings, 'require', lambda provider: None)
    monkeypatch.setattr(app.state.service, 'draft', lambda jid: None)
    response = client.post('/api/drafts/batch', json={
        'theme': '巴西游戏分享', 'count': 10, 'character_mode': 'upload',
        'character_ids': [actor['id']], 'scene_ids': [scene['id']], 'game_ids': [game['id']],
        'dialogue_lines': [],
    })
    assert response.status_code == 200, response.text
    jobs = response.json()
    assert len(jobs) == 10
    directions = [job['request']['variation_direction'] for job in jobs]
    assert len(set(directions)) == 10
    assert all(job['request']['character_id'] == actor['id'] for job in jobs)


def test_batch_generate_claims_and_submits_each_reviewed_draft_once(tmp_path, monkeypatch):
    import asyncio
    from fastapi import BackgroundTasks
    from studio.models import BatchGenerate
    app = create_app(tmp_path)
    created = [app.state.store.create_job({
        'theme': f'variation-{index}', 'batch_id': 'a' * 32,
        'variation_count': 3, 'variation_index': index + 1,
    }) for index in range(3)]
    for job in created:
        app.state.store.update_job(job['id'], status='draft_ready')
    monkeypatch.setattr(app.state.settings, 'require', lambda provider: None)
    submitted = []
    async def submit(jid):
        submitted.append(jid)
    monkeypatch.setattr(app.state.service, 'submit', submit)

    route = next(route for route in app.routes if getattr(route, 'path', '') == '/api/jobs/generate-batch')
    background = BackgroundTasks()
    response = route.endpoint(BatchGenerate(job_ids=[job['id'] for job in created]), background)
    asyncio.run(background())

    assert submitted == [job['id'] for job in created]
    assert [job['status'] for job in response] == ['submitting'] * 3
