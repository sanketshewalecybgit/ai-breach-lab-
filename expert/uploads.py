"""Bounded text ingestion for the local knowledge-base poisoning exercise."""
from .cases import identifier
from tools.text_uploads import read_text_upload


MAX_UPLOADS = 20


def ingest(case, upload):
    document = read_text_upload(upload)
    if sum(bool(d.get('uploaded')) for d in case['documents']) >= MAX_UPLOADS:
        raise ValueError('This case already has 20 uploads. Edit an existing reference or generate a fresh case.')
    return dict(document, id=identifier('DOC'), classification='customer', tenant=case['tenant'],
                editable=True, revision=1, uploaded=True)
