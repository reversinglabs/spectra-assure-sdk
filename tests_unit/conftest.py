"""Make the project root importable so `spectra_assure_api_client` and `tools`
resolve when the tests run from a checkout rather than an installed package.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
