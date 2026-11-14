"""Export reviewed Pydantic wire models as versioned JSON Schema."""

import json
from pathlib import Path

from governed_dataops import contracts


def main():
    root = Path(__file__).resolve().parents[1] / "contracts" / "v1"
    root.mkdir(parents=True, exist_ok=True)
    for name in (
        "Incident",
        "Evidence",
        "Diagnosis",
        "Plan",
        "Approval",
        "EffectRequest",
        "EffectResult",
        "Verification",
    ):
        model = getattr(contracts, name)
        (root / f"{name}.schema.json").write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        )


if __name__ == "__main__":
    main()
