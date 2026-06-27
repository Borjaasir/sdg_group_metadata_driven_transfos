import re
from typing import Any, Dict, List

import pandas as pd

DataflowDatasets = Dict[str, pd.DataFrame]
Transformation = Dict[str, Any]


class TransfoHandler:
    def apply_transformations(
        self, transformations: List[Transformation], input_datasets: DataflowDatasets
    ) -> DataflowDatasets:
        datasets = dict(input_datasets)
        pending = list(transformations)

        while pending:
            progress = False
            for transformation in pending[:]:
                input_name = transformation.get("input")
                if not input_name or input_name not in datasets:
                    continue

                transformation_name = transformation.get("name")
                try:
                    self.apply_transformation(transformation, datasets)
                    pending.remove(transformation)
                    progress = True
                except Exception as exc:
                    print(f"Error applying transformation '{transformation_name}': {exc}")
                    pending.remove(transformation)
                    progress = True

            if not progress:
                for transformation in pending:
                    print(
                        f"Unable to apply transformation '{transformation.get('name')}' because "
                        f"input '{transformation.get('input')}' is unavailable.\n"
                    )
                break
            
        transformed_datasets = {name: df for name, df in datasets.items() if name not in set(input_datasets)}

        return transformed_datasets

    def apply_transformation(
        self, transformation: Transformation, datasets: DataflowDatasets
    ) -> pd.DataFrame:
        transformation_type = transformation.get("type")
        input_name = transformation.get("input")
        config = transformation.get("config", {})
        transformation_name = transformation.get("name")

        if not transformation_type:
            raise ValueError("Each transformation must include a 'type'.")
        if not input_name:
            raise ValueError("Each transformation must include an 'input'.")
        if not isinstance(config, dict):
            raise ValueError("Each transformation must include a 'config' dictionary.")
        if not transformation_name:
            raise ValueError("Each transformation must have a 'name'.")

        source_df = datasets.get(input_name)
        if source_df is None:
            raise ValueError(
                f"Input dataset '{input_name}' not found for transformation '{transformation_name}'."
            )

        print(
            f"Applying transformation '{transformation_name}' ({transformation_type}) using input '{input_name}'"
            f"({len(source_df)} rows, {len(source_df.columns)} columns)"
        )

        match transformation_type:
            case "filter":
                result = self._apply_filter(source_df, config)
            case "add_fields":
                result = self._apply_add_fields(source_df, config)
            case "group":
                result = self._apply_group(source_df, config)
            case _:
                raise ValueError(f"Unsupported transformation type: {transformation_type}")

        datasets[transformation_name] = result
        print(
            f"Transformation '{transformation_name}' completed: output has {len(result)} rows, "
            f"{len(result.columns)} columns \n"
        )

        return result

    def _apply_filter(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        filter_expression = config.get("filter")
        if not filter_expression:
            raise ValueError("Filter transformation requires a 'filter' expression.")
        return df.query(filter_expression)

    def _apply_add_fields(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> pd.DataFrame:
        fields = config.get("fields", [])
        if not isinstance(fields, list):
            raise ValueError("add_fields transformation requires a list of 'fields'.")

        result = df.copy()
        for field in fields:
            name = field.get("name")
            expression = field.get("expression")
            if not name or expression is None:
                raise ValueError(
                    "Each field must include a 'name' and an 'expression'."
                )
            result[name] = self._evaluate_expression(result, expression)
        return result

    def _evaluate_expression(self, df: pd.DataFrame, expression: str) -> Any:
        expression = expression.strip()
        if expression == "current_date()":
            return pd.Timestamp.now().normalize()
        return df.eval(expression, engine="python")

    def _apply_group(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        group_fields = config.get("group_fields", [])
        aggregations = config.get("aggregations", [])

        if not group_fields or not isinstance(group_fields, list):
            raise ValueError("group transformation requires a list of 'group_fields'.")
        if not aggregations or not isinstance(aggregations, list):
            raise ValueError("group transformation requires a list of 'aggregations'.")

        agg_map = {}
        for agg in aggregations:
            func, column, alias = self._parse_aggregation(agg)
            agg_map[alias] = (column, func)

        grouped = df.groupby(group_fields).agg(**agg_map)
        return grouped.reset_index()

    def _parse_aggregation(self, aggregation: str) -> tuple[str, str, str]:
        match_obj = re.match(
            r"^\s*(\w+)\s*\(\s*([^)]+)\s*\)\s*(?:as\s+(\w+))?\s*$",
            aggregation,
            re.IGNORECASE,
        )
        if not match_obj:
            raise ValueError(f"Invalid aggregation syntax: {aggregation}")

        func = match_obj.group(1).lower()
        column = match_obj.group(2)
        alias = match_obj.group(3) or f"{func}_{column}"

        supported = {"sum", "mean", "max", "min", "count", "nunique"}
        if func not in supported:
            raise ValueError(f"Unsupported aggregation function: {func}")

        return func, column, alias
