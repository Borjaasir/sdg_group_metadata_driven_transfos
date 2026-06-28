from typing import Any, Dict

import pandas as pd


class AddFieldsTransformation:
	def __call__(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
		fields = config.get("fields", [])
		if not isinstance(fields, list):
			raise ValueError("add_fields transformation requires a list of 'fields'.")

		result = df.copy()
		for field in fields:
			name = field.get("name")
			expression = field.get("expression")
			if not name or expression is None:
				raise ValueError("Each field must include a 'name' and an 'expression'.")

			result[name] = self._evaluate_expression(result, expression)

		return result

	def _evaluate_expression(self, df: pd.DataFrame, expression: str) -> Any:
		expression = expression.strip()
		if expression == "current_date()":
			return pd.Timestamp.now().normalize()

		return df.eval(expression, engine="python")

