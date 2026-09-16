"""Make non-person synthetic references for the public Windows CI run."""
from pathlib import Path

from PIL import Image


root = Path(__file__).resolve().parent.parent / 'studio' / 'builtin'
for role, color in [('character', '#b08c76'), ('scene', '#a9c4d1')]:
    folder = root / role
    folder.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (600, 800), color).save(folder / 'ci-synthetic.webp', 'WEBP')
