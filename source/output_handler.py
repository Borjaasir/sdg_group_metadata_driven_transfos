from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


class OutputHandler:
    def __init__(self, base_dir: Path):
        self.output_dir = base_dir / "data" / "output"

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
                raise ValueError(f"Input dataset '{input_name}' not found for output '{output_name}'.")

            self._write_output_data(output_def, source_df)
            written_outputs[output_name] = source_df

        return written_outputs

    def _write_output_data(self, output_def: Dict[str, Any], df: pd.DataFrame) -> None:
        output_type = str(output_def.get("type", "file")).lower()
        config = output_def.get("config", {})
        if not isinstance(config, dict):
            raise ValueError("Each output config must be a dictionary.")

        if output_type == "file":
            self._write_file_output(config, df)
            return

        if output_type == "table":
            self._write_table_output(config, df)
            return

        raise ValueError(f"Unsupported output type: {output_type}")

    def _get_output_format(self, config: Dict[str, Any]) -> str:
        format_value = config.get("format") or config.get("type")
        if not format_value:
            return "parquet"
        return str(format_value).lower()

    def _write_file_output(self, config: Dict[str, Any], df: pd.DataFrame) -> None:
        path_value = config.get("path")
        if not path_value:
            raise ValueError("File output config must include a 'path'.")

        format_value = self._get_output_format(config)
        save_mode = str(config.get("save_mode", "overwrite")).lower()
        partition_column = config.get("partition")

        target_path = self._build_output_path(path_value)
        if partition_column:
            if target_path.suffix:
                raise ValueError(
                    "Partitioned file output path must be a directory, not a file path."
                )
            self._write_partitioned_output(target_path, df, partition_column, format_value, save_mode)
            return

        if not target_path.suffix:
            target_path = target_path / f"data.{format_value}"

        self._write_dataframe_to_path(target_path, df, format_value, save_mode)

    def _write_table_output(self, config: Dict[str, Any], df: pd.DataFrame) -> None:
        table_name = config.get("table") or "table"
        format_value = self._get_output_format(config)
        path_value = config.get("path") or f"/output/{table_name}"
        target_path = self._build_output_path(path_value)
        if not target_path.suffix:
            target_path = target_path / f"{table_name}.{format_value}"

        save_mode = str(config.get("save_mode", "overwrite")).lower()

        if save_mode == "merge":
            self._merge_dataframe_to_path(target_path, df, config.get("primary_key"))
            return

        self._write_dataframe_to_path(target_path, df, format_value, save_mode)

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

    def _merge_dataframe_to_path(
        self, target_path: Path, df: pd.DataFrame, primary_key: Any = None
    ) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            existing_df = self._read_existing_dataframe(target_path, target_path.suffix.lstrip("."))
            if primary_key is None:
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            else:
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df = (
                    combined_df.drop_duplicates(subset=primary_key, keep="last")
                    .reset_index(drop=True)
                )
        else:
            combined_df = df

        self._write_dataframe(combined_df, target_path, target_path.suffix.lstrip("."))

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

    