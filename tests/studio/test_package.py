from scripts import package_studio
from zipfile import ZipFile


def test_package_collects_only_local_bundled_reference_images(tmp_path):
    character = tmp_path / 'studio' / 'builtin' / 'character'
    scene = tmp_path / 'studio' / 'builtin' / 'scene'
    character.mkdir(parents=True)
    scene.mkdir(parents=True)
    actor = character / 'actor.webp'
    room = scene / 'room.webp'
    actor.write_bytes(b'actor')
    room.write_bytes(b'room')
    (character / 'notes.txt').write_text('not an image')
    (scene / 'link.webp').symlink_to(actor)

    assert hasattr(package_studio, 'bundled_files'), 'packager must include built-in images'
    assert package_studio.bundled_files(tmp_path) == {actor, room}


def test_windows_package_has_chinese_one_click_entry():
    package_studio.package()
    with ZipFile(package_studio.ROOT.parent / 'videoX-Brazil-UGC-Windows.zip') as archive:
        assert 'videoX/一键启动.cmd' in archive.namelist()
        assert 'videoX/使用说明.txt' in archive.namelist()
