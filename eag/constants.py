import os
from pathlib import Path

from eag.config import settings

APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = str(Path(APP_ROOT_DIR).parent.absolute())
ANNOUNCES_PATH = os.path.join(PROJECT_ROOT_DIR, settings.announces_relative_path)
OLD_ANNOUNCES_PATH = os.path.join(PROJECT_ROOT_DIR, settings.old_announces_relative_path)