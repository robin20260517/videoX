"""Stable fingerprint for the Windows launcher's frontend build cache."""
import hashlib
from pathlib import Path


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    files = [p for folder in ('src', 'public') for p in (root / folder).rglob('*') if p.is_file()]
    files += [p for p in root.iterdir() if p.is_file() and (
        p.name in ('package.json', 'pnpm-lock.yaml', 'index.html', '.npmrc')
        or p.name.startswith(('vite.config.', '.env'))
        or (p.name.startswith('tsconfig') and p.suffix == '.json'))]
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


if __name__ == '__main__':
    print(fingerprint(Path(__file__).resolve().parent.parent / 'studio-web'))
