from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from source.output.writers.file_output_writer import FileOutputWriter
from source.output.writers.table_output_writer import TableOutputWriter


class OutputHandler:
    def __init__(self, base_dir: Path):
        self.output_dir = base_dir / "data" / "output"
        self.file_writer = FileOutputWriter(self.output_dir)
        self.table_writer = TableOutputWriter(self.output_dir / "warehouse.duckdb")

    def handle_data_outputs(
        self, outputs: List[Dict[str, Any]], transformed_datasets: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        written_outputs: Dict[str, pd.DataFrame] = {}

        for output_def in outputs:
            output_name = output_def.get("name")
            if not output_name:
                raise ValueError("Each output definition must include a 'name'.")

            input_name = output_def.get("input")
            if not input_name:
                raise ValueError(f"Output '{output_name}' must include an 'input'.")

            source_df = transformed_datasets.get(input_name)
            if source_df is None:
                print(
                    f"Warning: input dataset '{input_name}' not found for output "
                    f"'{output_name}'. Skipping output.\n"
                )
                continue

            self._write_output_data(output_def, source_df)
            written_outputs[output_name] = source_df

        return written_outputs

    def _write_output_data(self, output_def: Dict[str, Any], df: pd.DataFrame) -> None:
        output_type = str(output_def.get("type", "file")).lower()
        config = output_def.get("config", {})
        if not isinstance(config, dict):
            raise ValueError("Each output config must be a dictionary.")

        if output_type == "file":
            self.file_writer.write(config, df)
            return

        if output_type == "table":
            self.table_writer.write(config, df)
            return

        raise ValueError(f"Unsupported output type: {output_type}")

    