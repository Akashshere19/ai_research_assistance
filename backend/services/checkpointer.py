import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


# Store checkpoints in a dedicated SQLite database.
CHECKPOINT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "langgraph_checkpoints.sqlite3"
)


def create_checkpointer():
    connection = sqlite3.connect(
        str(CHECKPOINT_DB_PATH),
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(connection)
    checkpointer.setup()

    return checkpointer