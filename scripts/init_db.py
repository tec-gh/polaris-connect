from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import models  # noqa: F401
from app.core.database import Base, engine, session_scope
from app.services.mapping_service import ensure_default_template


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with session_scope() as session:
        ensure_default_template(session)
    print("Polaris Connect database initialized.")


if __name__ == "__main__":
    main()
