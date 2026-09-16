from studio.frontend_build import fingerprint


def test_build_fingerprint_tracks_inputs_not_output(tmp_path):
    (tmp_path / 'src').mkdir()
    source = tmp_path / 'src' / 'App.tsx'
    source.write_text('original')
    before = fingerprint(tmp_path)
    (tmp_path / 'dist').mkdir()
    (tmp_path / 'dist' / 'index.html').write_text('built')
    (tmp_path / 'tsconfig.tsbuildinfo').write_text('generated compiler cache')
    assert fingerprint(tmp_path) == before
    for path in [source, tmp_path / 'pnpm-lock.yaml', tmp_path / 'vite.config.ts', tmp_path / 'tsconfig.app.json']:
        before = fingerprint(tmp_path)
        path.write_text('changed')
        assert fingerprint(tmp_path) != before
