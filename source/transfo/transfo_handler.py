from typing import Any, Dict, List

import pandas as pd
from source.transfo.transfo_catalog.add_fields_transformation import AddFieldsTransformation
from source.transfo.transfo_catalog.filter_transformation import FilterTransformation
from source.transfo.transfo_catalog.group_transformation import GroupTransformation

DataflowDatasets = Dict[str, pd.DataFrame]
Transformation = Dict[str, Any]


class TransfoHandler:
    def __init__(self) -> None:
        self.transfo_catalog = {
            "filter": FilterTransformation(),
            "add_fields": AddFieldsTransformation(),
            "group": GroupTransformation(),
        }

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

        transformation_executor = self.transfo_catalog.get(transformation_type)
        if transformation_executor is None:
            raise ValueError(f"Unsupported transformation type: {transformation_type}")

        result = transformation_executor(source_df, config)

        datasets[transformation_name] = result
        print(
            f"Transformation '{transformation_name}' completed: output has {len(result)} rows, "
            f"{len(result.columns)} columns \n"
        )

        return result
