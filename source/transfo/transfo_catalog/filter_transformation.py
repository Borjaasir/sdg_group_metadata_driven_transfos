from typing import Any, Dict

import pandas as pd


class FilterTransformation:
	def __call__(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
		filter_expression = config.get("filter")
		if not filter_expression:
			raise ValueError("Filter transformation requires a 'filter' expression.")

		return df.query(filter_expression)
