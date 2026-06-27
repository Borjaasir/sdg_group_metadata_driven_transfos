from pathlib import Path
from typing import Any, Dict

import duckdb
import pandas as pd


class TableOutputWriter:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = duckdb.connect(str(self.database_path))

    def write(self, config: Dict[str, Any], df: pd.DataFrame) -> None:
        table_name = config.get("table")
        if not table_name:
            raise ValueError("Table output config must include a 'table' name.")

        save_mode = str(config.get("save_mode", "overwrite")).lower()

        self.connection.register("source_df", df)
        try:
            if save_mode == "overwrite":
                self.connection.execute(
                    f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM source_df'
                )
            elif save_mode == "append":
                self._append_table(table_name)
            elif save_mode == "merge":
                self._merge_table(table_name, config.get("primary_key"))
            else:
                raise ValueError(f"Unsupported save mode: {save_mode}")
        finally:
            self.connection.unregister("source_df")

    def _append_table(self, table_name: str) -> None:
        self.connection.execute(
            f'CREATE TABLE IF NOT EXISTS "{table_name}" AS SELECT * FROM source_df WHERE 1 = 0'
        )
        self.connection.execute(f'INSERT INTO "{table_name}" SELECT * FROM source_df')

    def _merge_table(
        self,
        table_name: str,
        primary_key: Any,
    ) -> None:
        if not primary_key:
            raise ValueError(
                f"Table output '{table_name}' with 'merge' save mode requires a 'primary_key'."
            )

        keys = primary_key if isinstance(primary_key, list) else [primary_key]
        key_columns = ", ".join(f'"{key}"' for key in keys)

        self.connection.execute(
            f'CREATE TABLE IF NOT EXISTS "{table_name}" AS SELECT * FROM source_df WHERE 1 = 0'
        )
        self.connection.execute(
            f'DELETE FROM "{table_name}" WHERE ({key_columns}) IN '
            f"(SELECT {key_columns} FROM source_df)"
        )
        self.connection.execute(f'INSERT INTO "{table_name}" SELECT * FROM source_df')
