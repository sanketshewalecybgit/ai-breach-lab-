from scripts.package_release import DIRECTORIES, FILES, release_files


def test_release_excludes_local_state_credentials_and_symlinks(tmp_path):
    for name in FILES:
        (tmp_path / name).write_text('release file')
    for directory in DIRECTORIES:
        (tmp_path / directory).mkdir(exist_ok=True)
    include = ['database/schema.sql', 'static/favicon.svg', '.github/workflows/tests.yml']
    exclude = ['database/lab.db', 'database/lab.db-wal', 'docs/.env.txt',
               'docs/.private/notes.md', 'ai/__pycache__/cached.py',
               'docs/debug.log', 'prompt.txt']
    for name in include + exclude:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture')
    (tmp_path / 'docs' / 'linked.md').symlink_to(tmp_path / 'prompt.txt')
    bundled = {str(path.relative_to(tmp_path)) for path in release_files(tmp_path)}
    assert set(include) <= bundled
    assert not set(exclude) & bundled
    assert 'docs/linked.md' not in bundled
