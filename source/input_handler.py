from typing import Any, Dict, List
import pandas as pd
from pathlib import Path


class InputHandler:
    def __init__(self, base_dir: Path):
        self.input_dir = base_dir / "data"

    def handle_data_inputs(
        self, inputs: List[Dict[str, Any]]
    ) -> Dict[str, pd.DataFrame]:
        loaded_inputs = {}
        for input_def in inputs:
            name = input_def.get("name")
            if not name:
                raise ValueError("Each input definition must include a 'name'.")
            try:
                loaded_inputs[name] = self._read_input_data(input_def)
            except FileNotFoundError as exc:
                print(f"Warning: input file for '{name}' was not found: {exc}\n")
                continue
        return loaded_inputs

    def _read_input_data(self, input_def: Dict[str, Any]) -> pd.DataFrame:
        config = input_def.get("config")
        options = input_def.get("options", {})
        if not isinstance(config, dict):
            raise ValueError("Input config is required for reading input data.")

        path_value = config.get("path")
        if not path_value:
            raise ValueError("Input config must contain a 'path' field.")

        format_value = config.get("format", "csv").lower()
        data_path = self.input_dir / path_value.lstrip("/")

        if format_value == "csv":
            return self._read_csv_path(data_path, options)
        if format_value == "parquet":
            return self._read_parquet_path(data_path)

        raise ValueError(f"Unsupported input format: {format_value}")

    def _read_csv_path(self, csv_path: Path, options: Dict[str, Any]) -> pd.DataFrame:
        delimiter = options.get("delimiter", ",")
        header = options.get("header", "infer")

        if isinstance(header, str) and header.lower() == "true":
            header_value = 0
        elif isinstance(header, str) and header.lower() == "false":
            header_value = None
        else:
            header_value = header

        return pd.read_csv(csv_path, sep=delimiter, header=header_value)

    def _read_parquet_path(self, parquet_path: Path) -> pd.DataFrame:
        return pd.read_parquet(parquet_path)
