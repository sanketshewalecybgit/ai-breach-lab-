from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get('NOVACART_DATABASE', ROOT / 'database' / 'lab.db'))
DEMO_TOKEN = 'INTERNAL-DEMO-TOKEN-4821'
MAX_PROMPT_LENGTH = 4000
