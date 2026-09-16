from pathlib import Path
import pytest
import requests

from studio.providers import WaveSpeedPreSubmitError, WaveSpeedProvider


def test_wavespeed_uploads_three_refs_and_submits_480p_fifteen_seconds_once(tmp_path):
    session = FakeSession()
    provider = WaveSpeedProvider(api_key='ws-secret', session=session)
    refs = []
    for index in range(3):
        path = tmp_path / f'ref-{index}.webp'
        path.write_bytes(f'image-{index}'.encode())
        refs.append(path)
    result = provider.submit(
        prompt='one continuous take', reference_paths=refs,
        model='bytedance/seedance-2.0-mini/text-to-video', resolution='480p', duration=15,
    )
    assert result['id'] == 'prediction-1'
    prediction = next(call for call in session.posts if '/bytedance/seedance-2.0-mini/text-to-video' in call['url'])
    assert prediction['json'] == {
        'prompt': 'one continuous take',
        'reference_images': ['https://cdn.example/ref-0', 'https://cdn.example/ref-1', 'https://cdn.example/ref-2'],
        'aspect_ratio': '9:16', 'resolution': '480p', 'duration': 15,
        'enable_web_search': False, 'generate_audio': True,
    }
    assert prediction['headers']['Authorization'] == 'Bearer ws-secret'
    assert len(session.puts) == 3
    assert all('Authorization' not in put['headers'] for put in session.puts)


def test_wavespeed_query_and_download_use_returned_prediction_output(tmp_path):
    session = FakeSession()
    provider = WaveSpeedProvider(api_key='ws-secret', session=session)
    task = provider.query('prediction-1')
    assert task['status'] == 'completed'
    target = tmp_path / 'final.mp4'
    provider.download(task['outputs'][0], target)
    assert target.read_bytes() == b'video-result'


def test_wavespeed_upload_timeout_is_known_to_be_before_paid_submission(tmp_path):
    class UploadTimeoutSession(FakeSession):
        def post(self, url, **kwargs):
            if url.endswith('/media/uploads'):
                raise requests.ReadTimeout('ticket timed out')
            raise AssertionError('paid endpoint must not be reached')

    reference = tmp_path / 'reference.webp'
    reference.write_bytes(b'image')
    provider = WaveSpeedProvider(api_key='ws-secret', session=UploadTimeoutSession())
    with pytest.raises(WaveSpeedPreSubmitError, match='尚未提交付费任务'):
        provider.submit(
            prompt='one take', reference_paths=[reference, reference],
            model='bytedance/seedance-2.0-mini/text-to-video', resolution='480p', duration=15,
        )


class Response:
    def __init__(self, body=None, content=b'', status=200):
        self.body, self.content, self.status_code = body or {}, content, status
        self.ok = 200 <= status < 300

    def json(self):
        return self.body

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.status_code)

    def iter_content(self, chunk_size=1024):
        yield self.content


class FakeSession:
    def __init__(self):
        self.posts, self.puts = [], []

    def post(self, url, **kwargs):
        self.posts.append({'url': url, **kwargs})
        if url.endswith('/media/uploads'):
            index = len([call for call in self.posts if call['url'].endswith('/media/uploads')]) - 1
            return Response({'code': 200, 'data': {
                'download_url': f'https://cdn.example/ref-{index}',
                'upload': {'method': 'PUT', 'url': f'https://upload.example/{index}', 'headers': {'Content-Type': 'image/webp'}},
            }})
        return Response({'code': 200, 'data': {'id': 'prediction-1', 'status': 'created'}})

    def put(self, url, **kwargs):
        data = kwargs['data']
        self.puts.append({'url': url, 'headers': kwargs.get('headers', {}), 'bytes': data.read()})
        return Response()

    def get(self, url, **kwargs):
        if '/predictions/' in url:
            return Response({'code': 200, 'data': {'id': 'prediction-1', 'status': 'completed', 'outputs': ['https://cdn.example/final.mp4']}})
        return Response(content=b'video-result')
