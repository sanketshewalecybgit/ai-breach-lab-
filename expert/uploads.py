"""Bounded text ingestion for the local knowledge-base poisoning exercise."""
from pathlib import PurePosixPath

from werkzeug.utils import secure_filename

from .cases import identifier


MAX_UPLOAD_BYTES = 12 * 1024
MAX_UPLOAD_CHARACTERS = 4000
MAX_UPLOADS = 20


def ingest(case, upload):
    if upload is None or not upload.filename:
        raise ValueError('Choose a UTF-8 .txt or .md document to upload.')
    filename = secure_filename(upload.filename)
    if PurePosixPath(filename).suffix.lower() not in ('.txt', '.md'):
        raise ValueError('Use a UTF-8 .txt or .md document. PDF and Word files are not supported.')
    content = upload.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError('The document must be no larger than 12 KiB.')
    try:
        body = content.decode('utf-8-sig').strip()
    except UnicodeDecodeError:
        raise ValueError('The document must contain UTF-8 text.') from None
    if not body or len(body) > MAX_UPLOAD_CHARACTERS:
        raise ValueError('Document text must contain 1–4000 characters.')
    if any((ord(c) < 32 and c not in '\n\r\t') or ord(c) == 127 for c in body):
        raise ValueError('Upload plain text without binary or control characters.')
    if sum(bool(d.get('uploaded')) for d in case['documents']) >= MAX_UPLOADS:
        raise ValueError('This case already has 20 uploads. Edit an existing reference or generate a fresh case.')
    return dict(id=identifier('DOC'), title=PurePosixPath(filename).stem[:120],
                body=body, classification='customer', tenant=case['tenant'],
                editable=True, revision=1, uploaded=True, filename=filename[:160])
