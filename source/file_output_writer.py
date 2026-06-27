from pathlib import Path
from typing import Any, Dict

import pandas as pd


class FileOutputWriter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def write(self, config: Dict[str, Any], df: pd.DataFrame) -> None:
        path_value = config.get("path")
        if not path_value:
            raise ValueError("File output config must include a 'path'.")

        format_value = self._get_output_format(config)
        save_mode = str(config.get("save_mode", "overwrite")).lower()
        partition_column = config.get("partition")

        target_path = self._build_output_path(path_value)
        if partition_column:
            self._write_partitioned_output(target_path, df, partition_column, format_value, save_mode)
            return

        if not target_path.suffix:
            target_path = target_path.with_name(f"{target_path.name}.{format_value}")

        self._write_dataframe_to_path(target_path, df, format_value, save_mode)

    def _get_output_format(self, config: Dict[str, Any]) -> str:
        format_value = config.get("format") or config.get("type")
        if not format_value:
            return "parquet"
        return str(format_value).lower()

    def _build_output_path(self, path_value: str) -> Path:
        cleaned = path_value.lstrip("/")
        if cleaned.startswith("output/"):
            cleaned = cleaned[len("output/"):]
        return self.output_dir / cleaned

    def _write_partitioned_output(
        self,
        target_path: Path,
        df: pd.DataFrame,
        partition_column: str,
        format_value: str,
        save_mode: str,
    ) -> None:
        if partition_column not in df.columns:
            raise ValueError(f"Partition column '{partition_column}' not found in the dataframe.")

        for partition_value, partition_df in df.groupby(partition_column, dropna=False):
            partition_dir = target_path / f"{partition_column}={partition_value}"
            partition_file = partition_dir / f"data.{format_value}"
            self._write_dataframe_to_path(partition_file, partition_df, format_value, save_mode)

    def _write_dataframe_to_path(
        self, target_path: Path, df: pd.DataFrame, format_value: str, save_mode: str
    ) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if save_mode == "overwrite":
            if target_path.exists():
                target_path.unlink()
            self._write_dataframe(df, target_path, format_value)
            return

        if save_mode == "append":
            if target_path.exists():
                existing_df = self._read_existing_dataframe(target_path, format_value)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            else:
                combined_df = df
            self._write_dataframe(combined_df, target_path, format_value)
            return

        raise ValueError(f"Unsupported save mode: {save_mode}")

    def _write_dataframe(self, df: pd.DataFrame, target_path: Path, format_value: str) -> None:
        if format_value == "parquet":
            df.to_parquet(target_path, index=False)
            return

        if format_value == "csv":
            df.to_csv(target_path, index=False)
            return

        raise ValueError(f"Unsupported output format: {format_value}")

    def _read_existing_dataframe(self, target_path: Path, format_value: str) -> pd.DataFrame:
        if format_value == "parquet":
            return pd.read_parquet(target_path)

        if format_value == "csv":
            return pd.read_csv(target_path)

        raise ValueError(f"Unsupported output format: {format_value}")
