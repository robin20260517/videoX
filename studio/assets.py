import io
import warnings
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024


def ingest_image(store, content: bytes, role, filename, source_url=None, preserve_webp=False):
    if role not in ('character', 'scene', 'game'):
        raise ValueError('未知图片用途。')
    if len(content) > MAX_BYTES:
        raise ValueError('图片不可超过 10 MB。')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('请上传单张 JPG、PNG 或 WebP 图片。')
                if not (300 <= image.width <= 6000 and 300 <= image.height <= 6000):
                    raise ValueError('图片宽高需在 300–6000 像素之间。')
                if not 0.4 <= image.width / image.height <= 2.5:
                    raise ValueError('参考图宽高比需在 0.4–2.5 之间。')
                if preserve_webp and image.format == 'WEBP' and not any(
                    field in image.info for field in ('exif', 'icc_profile', 'xmp')
                ):
                    encoded = content
                else:
                    image = ImageOps.exif_transpose(image).convert('RGB')
                    # Normalize uploads and discard EXIF/private metadata.
                    buffer = io.BytesIO()
                    image.save(buffer, 'WEBP', quality=94 if role == 'game' else 88, method=6)
                    encoded = buffer.getvalue()
                if len(encoded) > 20 * 1024 * 1024:
                    raise ValueError('转换后图片过大，请压缩或降低分辨率。')
                path = store.media / (uuid4().hex + '.webp')
                path.write_bytes(encoded)
                return store.add_asset(role, Path(filename).name[:200], path, image.width, image.height, source_url)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError('无法读取图片，请上传有效 JPG、PNG 或 WebP。') from exc


def public_asset(asset):
    return {key: value for key, value in asset.items() if key != 'path'}


def seed_builtin_assets(store, library: Path):
    """Import packaged references once into the same local asset store as uploads."""
    known = {asset.get('source_url') for asset in store.assets()}
    for role in ('character', 'scene'):
        folder = Path(library) / role
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
                continue
            source = f'builtin://{role}/{path.name}'
            if source in known:
                continue
            ingest_image(store, path.read_bytes(), role, path.name, source_url=source, preserve_webp=True)
            known.add(source)
