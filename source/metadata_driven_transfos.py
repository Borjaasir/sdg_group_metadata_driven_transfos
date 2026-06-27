import json
from pathlib import Path
from typing import Any, Dict, List
from source.input_handler import InputHandler
from source.transfo_handler import TransfoHandler
from source.output_handler import OutputHandler


class MetadataDrivenTransfos:

    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent
        self.metadata_dir = self.base_dir
        self.input_handler = InputHandler(self.base_dir)
        self.transfo_handler = TransfoHandler()
        self.output_handle = OutputHandler(self.base_dir)

    def entrypoint(self, metadata_filename: str = "metadata.json") -> None:
        try:
            dataflows = self._read_metadata(metadata_filename).get("dataflows", [])
            validated_dataflows = self._validate_dataflows(dataflows)

            for dataflow in validated_dataflows:
                self._process_dataflow(dataflow)
        except Exception as exc:
            print(f"Unexpected error in metadata driven transformations: {exc}")

    def _process_dataflow(self, dataflow: Dict[str, Any]) -> None:
        name = dataflow.get("name")
        inputs = dataflow["inputs"]
        transformations = dataflow["transformations"]
        outputs = dataflow["outputs"]
        print(
            f"Processing dataflow '{name}' with {len(inputs)} inputs, "
            f"{len(transformations)} transformations, and {len(outputs)} outputs."
        )

        print("\n")
        print("#" * 64)
        print("Extraction")
        print("\n")

        print(f"Reading inputs for dataflow '{name}' with {len(inputs)} inputs.\n")
        inputs_data_dfs = self.input_handler.handle_data_inputs(inputs)
        for loaded_name, df in inputs_data_dfs.items():
            print(f"For dataflow '{name}', loaded input '{loaded_name}' with {len(df)} rows")
            print(df.head())
            print("\n")


        print("\n")
        print("#" * 64)
        print("Transformation")
        print("\n")

        print(f"Transforming dataflow '{name}' with {len(transformations)} transformations.\n")
        transformed_dfs = self.transfo_handler.apply_transformations(transformations, inputs_data_dfs)

        for transfo_name, df in transformed_dfs.items():
            print(f"For dataflow '{name}', transformation applied '{transfo_name}' with {len(df)} rows")
            print(df.head())
            print("\n")

        print("\n")
        print("#" * 64)
        print("Loading")
        print("\n")

        print(f"Generating outputs for dataflow '{name}' with {len(outputs)} outputs.\n")
        outputs_data_dfs = self.output_handle.handle_data_outputs(outputs, transformed_dfs)

        for output_name, df in outputs_data_dfs.items():
            print(f"For dataflow '{name}', output generated '{output_name}' with {len(df)} rows")
            print(df.head())
            print("\n")


    def _validate_dataflows(self, dataflows: Any) -> List[Dict[str, Any]]:
        if not isinstance(dataflows, list) or not dataflows:
            raise ValueError("No dataflows found in metadata.")

        validated_dataflows: List[Dict[str, Any]] = []
        for dataflow in dataflows:
            if not isinstance(dataflow, dict):
                raise ValueError("Each dataflow must be a JSON object.")

            name = dataflow.get("name")
            inputs = dataflow.get("inputs")
            transformations = dataflow.get("transformations")
            outputs = dataflow.get("outputs")

            if not isinstance(name, str) or not name:
                raise ValueError("Each dataflow must contain a non-empty 'name'.")
            if not isinstance(inputs, list) or not inputs:
                raise ValueError(f"Dataflow '{name}' must contain a non-empty list of inputs.")
            if not isinstance(transformations, list) or not transformations:
                raise ValueError(f"Dataflow '{name}' must contain a non-empty list of transformations.")
            if not isinstance(outputs, list) or not outputs:
                raise ValueError(f"Dataflow '{name}' must contain a non-empty list of outputs.")

            validated_dataflows.append(dataflow)

        return validated_dataflows  

    def _read_metadata(self, metadata_filename: str) -> Dict[str, Any]:
        metadata_path = self.metadata_dir / metadata_filename
        with metadata_path.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)

        return metadata
