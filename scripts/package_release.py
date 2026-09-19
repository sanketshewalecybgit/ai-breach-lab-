"""Build a clean source archive without local databases or environments."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    '.gitignore', '.gitattributes', '.dockerignore', 'README.md', 'LICENSE',
    'CONTRIBUTING.md', 'SECURITY.md', 'Dockerfile', 'docker-compose.yml',
    'requirements.txt', 'requirements-dev.txt', 'pytest.ini', 'app.py', 'config.py',
)
# Only source/documentation extensions from these directories enter the archive.
DIRECTORIES = ('.github', 'ai', 'challenges', 'database', 'docs', 'security',
               'static', 'templates', 'tests', 'tools', 'scripts')
EXTENSIONS = {'.py', '.sql', '.md', '.txt', '.html', '.css', '.js', '.svg', '.png', '.yml', '.yaml'}


def release_files(root=ROOT):
    for name in FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing or unsafe release file: {name}')
        yield path
    for directory in DIRECTORIES:
        for path in sorted((root / directory).rglob('*')):
            relative = path.relative_to(root)
            if any(part.startswith('.') and part != '.github' for part in relative.parts):
                continue
            if '__pycache__' in relative.parts or path.suffix not in EXTENSIONS:
                continue
            if path.is_file() and not any(parent.is_symlink() for parent in (path, *path.parents)):
                yield path


def main():
    destination = ROOT / 'dist' / 'ai-breachlab.zip'
    destination.parent.mkdir(exist_ok=True)
    paths = list(release_files())
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, Path('ai-breachlab') / path.relative_to(ROOT))
    with ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Release archive failed its integrity check')
    print(f'Created {destination} ({len(paths)} files)')


if __name__ == '__main__':
    main()
