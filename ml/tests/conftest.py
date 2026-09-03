"""pytest conftest — expose factories' fixtures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import factories  # noqa: F401,E402

# re-export fixtures so tests see them via conftest
basic_ngo = factories.basic_ngo
demo_mandate = factories.make_demo_mandate
