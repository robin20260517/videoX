import io
import json
from PIL import Image
from studio.assets import ingest_image
from studio.config import Settings
from studio.models import Brief, Draft
from studio.service import StudioService
from studio.store import Store
from tools.video.seedance_ark import SeedanceArkVideo
from test_contract import draft_data


def setup_job(tmp_path, monkeypatch):
    store = Store(tmp_path)
    settings = Settings(store)
    monkeypatch.setattr(settings, 'secret', lambda _: 'test-credential')
    store.save_settings({'video_provider': 'ark'})
    service = StudioService(store, settings)
    ids = []
    for role, color in [('character','red'),('scene','green'),('game','blue')]:
        b = io.BytesIO()
        Image.new('RGB', (600,800), color).save(b, 'PNG')
        ids.append(ingest_image(store, b.getvalue(), role, role)['id'])
    request = {'theme':'厨房游戏','character_mode':'upload','character_id':ids[0],'scene_id':ids[1],'game_id':ids[2]}
    job = store.create_job(request)
    store.update_job(job['id'], status='draft_ready', prompt='Test one take', draft=draft_data())
    store.claim_submission(job['id'])
    return store, settings, service, job['id'], ids


def test_real_ark_payload_preserves_three_refs_and_async_task(tmp_path, monkeypatch):
    store, _, service, jid, ids = setup_job(tmp_path, monkeypatch)
    payloads = []
    def create(self, payload, key):
        payloads.append(payload)
        return 'task-123'
    monkeypatch.setattr(SeedanceArkVideo, '_create_task', create)
    service.submit(jid)
    assert store.get_job(jid)['task_id'] == 'task-123'
    payload = payloads[0]
    assert payload['duration'] == 15 and payload['ratio'] == '9:16' and payload['generate_audio'] is True
    images = [item for item in payload['content'] if item['type']=='image_url']
    assert len(images) == 3
    import base64
    from pathlib import Path
    for item, aid in zip(images, ids):
        assert item['role'] == 'reference_image'
        assert base64.b64decode(item['image_url']['url'].split(',')[1]) == Path(store.get_asset(aid)['path']).read_bytes()


def test_network_ambiguity_is_not_auto_resubmitted(tmp_path, monkeypatch):
    store, _, service, jid, _ = setup_job(tmp_path, monkeypatch)
    def create(*args):
        raise TimeoutError('paid POST timed out')
    monkeypatch.setattr(SeedanceArkVideo, '_create_task', create)
    service.submit(jid)
    assert store.get_job(jid)['status'] == 'submission_unknown'
    assert store.claim_submission(jid) is False


def test_definitive_ark_input_rejection_is_failed_not_submission_unknown(tmp_path, monkeypatch):
    import requests
    store, _, service, jid, _ = setup_job(tmp_path, monkeypatch)
    response = requests.Response()
    response.status_code = 400
    response.url = 'https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks'

    def reject(*args):
        raise requests.HTTPError(
            "400 Client Error: InputImageSensitiveContentDetected.PrivacyInformation",
            response=response,
        )

    monkeypatch.setattr(SeedanceArkVideo, '_create_task', reject)
    service.submit(jid)
    job = store.get_job(jid)
    assert job['status'] == 'failed'
    assert job['task_id'] is None
    assert '真人' in job['error'] and '授权' in job['error']


def test_model_preflight_failure_is_retryable_without_paid_post(tmp_path, monkeypatch):
    store, settings, service, jid, _ = setup_job(tmp_path, monkeypatch)
    store.save_settings({'ark_model':'unrecognized-model'})
    def forbidden(*args):
        raise AssertionError('must not submit')
    monkeypatch.setattr(SeedanceArkVideo, '_create_task', forbidden)
    service.submit(jid)
    assert store.get_job(jid)['status'] == 'draft_ready'
    assert store.get_job(jid)['error']


def test_provider_success_download_and_restart_preserve_output(tmp_path, monkeypatch):
    store, _, service, jid, _ = setup_job(tmp_path, monkeypatch)
    monkeypatch.setattr(SeedanceArkVideo, '_create_task', lambda *args: 'task-existing')
    service.submit(jid)
    assert store.get_job(jid)['status'] == 'queued'
    monkeypatch.setattr(SeedanceArkVideo, '_query_task', lambda *args: {'id':'task-existing','status':'succeeded','content':{'video_url':'https://provider.example/video.mp4'}})
    def download(url, path):
        path.write_bytes(b'provider-response-test')
    monkeypatch.setattr(SeedanceArkVideo, '_download_video', staticmethod(download))
    service.refresh(jid)
    restored = Store(tmp_path).get_job(jid)
    assert restored['status'] == 'succeeded'
    assert restored['video_url'] == f'/api/videos/{jid}'
    assert not restored.get('error')


def test_llm_receives_images_and_preserves_explicit_dialogue(tmp_path, monkeypatch):
    from studio.director import create_draft
    from pathlib import Path
    store, settings, service, jid, ids = setup_job(tmp_path, monkeypatch)
    store.save_settings({'llm_base_url':'https://director.example/v1','llm_model':'vision-model'})
    bodies=[]
    class Response:
        ok=True
        def json(self):
            return {'choices':[{'message':{'content':json.dumps(draft_data())}}]}
    def post(url, **kwargs):
        bodies.append(kwargs['json'])
        return Response()
    monkeypatch.setattr('studio.director.requests.post', post)
    brief = Brief(**store.get_job(jid)['request'], dialogue_override='Olha este jogo!')
    draft = create_draft(brief, [store.get_asset(aid) for aid in ids], settings)
    assert draft.dialogue_pt_br == 'Olha este jogo!'
    messages = bodies[0]['messages']
    images = [c for c in messages[1]['content'] if c['type']=='image_url']
    assert len(images) == 3
    assert all(c['image_url']['url'].startswith('data:image/webp;base64,') for c in images)
    assert '厨房游戏' in messages[1]['content'][0]['text']


def test_deepseek_json_mode_marker_is_removed_without_relaxing_draft_schema(tmp_path, monkeypatch):
    from studio.director import create_draft
    store, settings, _, jid, ids = setup_job(tmp_path, monkeypatch)
    payload = {**draft_data(), 'type': 'json_object'}

    class Response:
        ok = True
        def json(self):
            return {'choices': [{'message': {'content': json.dumps(payload)}}]}

    monkeypatch.setattr('studio.director.requests.post', lambda *args, **kwargs: Response())
    brief = Brief(**store.get_job(jid)['request'])
    draft = create_draft(brief, [store.get_asset(aid) for aid in ids], settings)
    assert draft.title == payload['title']

    payload['unexpected'] = 'still forbidden'
    try:
        create_draft(brief, [store.get_asset(aid) for aid in ids], settings)
    except ValueError as exc:
        assert 'unexpected' in str(exc)
    else:
        raise AssertionError('unknown fields must remain forbidden')
