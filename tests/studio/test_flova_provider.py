import json
from pathlib import Path

from studio.providers import FlovaCLIProvider


def test_flova_cli_authenticates_without_putting_key_in_command_and_returns_video(tmp_path):
    calls = []
    source = tmp_path / 'generated.mp4'
    source.write_bytes(b'flova-video')

    def runner(command, **kwargs):
        calls.append((command, kwargs.get('input')))
        if command[1:3] == ['auth', 'login']:
            return Result(stdout='{"code":0,"data":{}}')
        if command[1:3] == ['project', 'create']:
            return Result(stdout=json.dumps({'code': 0, 'data': {'project_id': 'project-1', 'project_url': 'https://www.flova.ai/project/?id=project-1'}}))
        if command[1] == 'upload':
            return Result(stdout=json.dumps({'code': 0, 'data': {'file_id': Path(command[2]).name}}))
        if command[1] == 'run':
            event = {'type': 'resource_ready', 'asset_kind': 'video_playback', 'local_path': str(source)}
            final = {'code': 0, 'data': {'terminal': True, 'status': 'completed', 'project_id': 'project-1', 'stream_chat_id': 'stream-1', 'pending_actions': []}}
            return Result(stdout=json.dumps(final), stderr='flova_event=' + json.dumps(event))
        raise AssertionError(command)

    provider = FlovaCLIProvider(executable='flova-test', runner=runner)
    refs = []
    for name in ['actor.webp', 'scene.webp', 'game.webp']:
        path = tmp_path / name
        path.write_bytes(name.encode())
        refs.append(path)
    target = tmp_path / 'final.mp4'
    result = provider.generate(
        api_key='secret-that-must-not-be-an-argument', project_name='Batch 01',
        prompt='one take', reference_paths=refs, output_path=target,
        model='Seedance 2.5', resolution='720p', duration=15,
    )
    assert target.read_bytes() == b'flova-video'
    assert result['project_id'] == 'project-1' and result['stream_chat_id'] == 'stream-1'
    assert calls[0][1] == 'secret-that-must-not-be-an-argument\n'
    assert all('secret-that-must-not-be-an-argument' not in argument for command, _ in calls for argument in command)
    run_command = next(command for command, _ in calls if command[1] == 'run')
    assert '--file-from' in run_command
    assert 'Seedance 2.5' in run_command[run_command.index('--content') + 1]
    assert '720p' in run_command[run_command.index('--content') + 1]


def test_flova_pending_action_is_not_reported_as_generation_success(tmp_path):
    def runner(command, **kwargs):
        if command[1:3] == ['auth', 'status']:
            return Result(stdout='{"code":0,"data":{}}')
        if command[1:3] == ['project', 'create']:
            return Result(stdout='{"code":0,"data":{"project_id":"p"}}')
        if command[1] == 'upload':
            return Result(stdout='{"code":0,"data":{"file_id":"f"}}')
        final = {'code': 0, 'data': {'terminal': True, 'status': 'completed', 'project_id': 'p', 'stream_chat_id': 's',
                                     'pending_actions': [{'blocking': True, 'message': 'Confirm spend'}]}}
        return Result(stdout=json.dumps(final))

    ref = tmp_path / 'actor.webp'
    ref.write_bytes(b'x')
    result = FlovaCLIProvider(executable='flova-test', runner=runner).generate(
        api_key='', project_name='test', prompt='prompt', reference_paths=[ref],
        output_path=tmp_path / 'final.mp4', model='Seedance 2.5', resolution='720p', duration=15,
    )
    assert result['status'] == 'awaiting_user'
    assert not (tmp_path / 'final.mp4').exists()


class Result:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode
