"""SQLite persistence. Each operation owns its connection and transaction."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.media = self.root / 'media'
        self.media.mkdir(exist_ok=True)
        self.projects = self.root / 'projects'
        self.projects.mkdir(exist_ok=True)
        self.db = self.root / 'studio.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, role TEXT, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_asset(self, role, name, path, width, height, source_url=None):
        aid = path.stem
        asset = dict(id=aid, role=role, name=name, url=f'/api/media/{aid}', width=width,
                     height=height, is_default=False, source_url=source_url, path=str(path))
        with self.connect() as db:
            db.execute('INSERT INTO assets VALUES (?,?,?)', (aid, role, json.dumps(asset)))
        return asset

    def get_asset(self, aid):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM assets WHERE id=?', (aid,)).fetchone()
        if not row:
            raise KeyError('找不到参考图片，请重新上传。')
        return json.loads(row[0])

    def assets(self, role=None):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM assets WHERE (? IS NULL OR role=?) ORDER BY rowid DESC', (role, role)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def set_default(self, aid):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute("SELECT id,payload FROM assets WHERE role='character'").fetchall()
            if aid not in [row[0] for row in rows]:
                raise ValueError('只能把人物图片设为默认角色。')
            for key, raw in rows:
                asset = json.loads(raw)
                asset['is_default'] = key == aid
                db.execute('UPDATE assets SET payload=? WHERE id=?', (json.dumps(asset), key))
        return self.get_asset(aid)

    def create_job(self, request):
        jid = uuid4().hex
        job = dict(id=jid, theme=request['theme'], request=request, status='drafting', created_at=now(), updated_at=now())
        with self.connect() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?)', (jid, job['status'], json.dumps(job)))
        return job

    def get_job(self, jid):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM jobs WHERE id=?', (jid,)).fetchone()
        if not row:
            raise KeyError('任务不存在。')
        return json.loads(row[0])

    def jobs(self):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM jobs ORDER BY rowid DESC').fetchall()
        return [json.loads(row[0]) for row in rows]

    def active_jobs(self):
        """All recoverable/pollable jobs, independent of history display size."""
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM jobs WHERE status IN ('drafting','submitting','queued','running','submission_unknown') ORDER BY rowid DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def update_job(self, jid, **changes):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM jobs WHERE id=?', (jid,)).fetchone()
            if not row:
                raise KeyError('任务不存在。')
            job = json.loads(row[0])
            job.update(changes, updated_at=now())
            db.execute('UPDATE jobs SET status=?,payload=? WHERE id=?', (job['status'], json.dumps(job), jid))
        return job

    def claim_submission(self, jid):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM jobs WHERE id=? AND status=?', (jid, 'draft_ready')).fetchone()
            if not row:
                return False
            job = json.loads(row[0])
            job.update(status='submitting', updated_at=now(), error=None)
            db.execute('UPDATE jobs SET status=?,payload=? WHERE id=?', ('submitting', json.dumps(job), jid))
        return True

    def claim_submissions(self, job_ids):
        """Atomically move an entire reviewed batch across the paid boundary."""
        if not job_ids or len(set(job_ids)) != len(job_ids):
            return False
        placeholders = ','.join('?' for _ in job_ids)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute(
                f'SELECT id,payload FROM jobs WHERE id IN ({placeholders})',
                tuple(job_ids),
            ).fetchall()
            jobs = {jid: json.loads(payload) for jid, payload in rows}
            if len(jobs) != len(job_ids) or any(jobs[jid]['status'] != 'draft_ready' for jid in job_ids):
                return False
            requests = [jobs[jid].get('request') or {} for jid in job_ids]
            batch_ids = {request.get('batch_id') for request in requests}
            counts = {request.get('variation_count') for request in requests}
            indexes = {request.get('variation_index') for request in requests}
            if (
                len(batch_ids) != 1 or None in batch_ids
                or counts != {len(job_ids)}
                or indexes != set(range(1, len(job_ids) + 1))
            ):
                return False
            timestamp = now()
            for jid in job_ids:
                job = jobs[jid]
                job.update(status='submitting', updated_at=timestamp, error=None)
                db.execute(
                    'UPDATE jobs SET status=?,payload=? WHERE id=?',
                    ('submitting', json.dumps(job), jid),
                )
        return True

    def recover(self):
        for job in self.active_jobs():
            if job['status'] == 'drafting':
                self.update_job(job['id'], status='interrupted', error='策划时服务中断，请重新创建策划。')
            elif job['status'] == 'submitting':
                self.update_job(job['id'], status='submission_unknown', error='提交期间服务中断，请先核对服务商任务，避免重复计费。')

    def public_settings(self):
        with self.connect() as db:
            return dict(db.execute('SELECT key,value FROM settings').fetchall())

    def save_settings(self, data):
        with self.connect() as db:
            for key, value in data.items():
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value))
