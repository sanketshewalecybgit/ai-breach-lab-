"""Text-only ingestion shared by the independent RAG and Expert workspaces."""
from pathlib import PurePosixPath

from werkzeug.utils import secure_filename


MAX_UPLOAD_BYTES = 12 * 1024
MAX_UPLOAD_CHARACTERS = 4000


def read_text_upload(upload):
    """Return inert text and display metadata; never use filenames as disk paths."""
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
    return dict(title=PurePosixPath(filename).stem[:120], body=body, filename=filename[:160])
