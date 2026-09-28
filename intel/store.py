"""SQLite owns documents, chunks, conversations and cached answers."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'intel.sqlite3'
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, digest TEXT UNIQUE,
                    pages TEXT NOT NULL, chunks TEXT NOT NULL, vectors TEXT,
                    embedding_model TEXT, warnings TEXT NOT NULL, created TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, created TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL, content TEXT NOT NULL, created TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS answer_cache (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def documents(self):
        with self.connect() as db:
            return [self.decode(r) for r in db.execute('SELECT * FROM documents ORDER BY created,id')]

    @staticmethod
    def decode(row):
        d = dict(row)
        for key in ('pages', 'chunks', 'vectors', 'warnings'):
            d[key] = json.loads(d[key]) if d[key] else None
        return d

    def add(self, name, digest, pages, chunks, vectors, model, warnings):
        ident = uuid.uuid4().hex
        with self.connect() as db:
            existing = db.execute('SELECT id FROM documents WHERE digest=?', (digest,)).fetchone()
            if existing:
                return existing['id'], False
            db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?)',
                       (ident, name, digest, json.dumps(pages), json.dumps(chunks),
                        json.dumps(vectors) if vectors is not None else None, model,
                        json.dumps(warnings), now()))
        return ident, True

    def set_vectors(self, ident, vectors, model):
        with self.connect() as db:
            db.execute('UPDATE documents SET vectors=?,embedding_model=? WHERE id=?',
                       (json.dumps(vectors), model, ident))
            db.execute('DELETE FROM answer_cache')

    def delete(self, ident):
        with self.connect() as db:
            db.execute('DELETE FROM documents WHERE id=?', (ident,))
            db.execute('DELETE FROM answer_cache')
            # Old conversations remain but their evidence is explicitly labelled unavailable in UI.

    def create_conversation(self, title='New investigation'):
        ident = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO conversations VALUES (?,?,?)', (ident, title[:100], now()))
        return ident

    def conversations(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM conversations ORDER BY created DESC,rowid DESC')]

    def messages(self, ident):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM conversations WHERE id=?', (ident,)).fetchone():
                raise ValueError('Conversation not found.')
            return [dict(r) | {'content': json.loads(r['content'])} for r in db.execute(
                'SELECT * FROM messages WHERE conversation_id=? ORDER BY id', (ident,))]

    def exchange(self, ident, question, answer):
        with self.connect() as db:
            db.execute('UPDATE conversations SET title=? WHERE id=? AND title=?',
                       (question[:70], ident, 'New investigation'))
            for role, content in [('user', question), ('assistant', answer)]:
                db.execute('INSERT INTO messages(conversation_id,role,content,created) VALUES (?,?,?,?)',
                           (ident, role, json.dumps(content), now()))

    def cache_get(self, key):
        with self.connect() as db:
            r = db.execute('SELECT value FROM answer_cache WHERE key=?', (key,)).fetchone()
            return json.loads(r['value']) if r else None

    def cache_put(self, key, result):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO answer_cache VALUES (?,?)', (key, json.dumps(result)))
