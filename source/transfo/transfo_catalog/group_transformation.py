import re
from typing import Any, Dict

import pandas as pd


class GroupTransformation:
	def __call__(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
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
