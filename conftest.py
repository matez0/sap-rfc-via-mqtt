# Having this module in the repository root makes pytest find application modules without specifying PYTHONPATH.

from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

assert load_dotenv(BASE_DIR / 'tests' / '.env')
