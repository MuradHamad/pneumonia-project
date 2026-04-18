"""FusionModel service — placeholder.

Returns random but plausible severity predictions so the end-to-end
flow (case submission → diagnosis → result page) works before the real
PyTorch model is trained. The real implementation will keep the same
`diagnose()` signature so swapping it later is a one-file change.
"""
from __future__ import annotations

import random
from typing import Any


RISK_CLASSES = ["I", "II", "III", "IV", "V"]


def diagnose(xray_path: str, clinical_data: dict[str, Any]) -> dict[str, Any]:
    """Run fusion inference on an X-ray + clinical payload.

    Args:
        xray_path: Path (relative to MEDIA_ROOT) to the chest X-ray.
        clinical_data: Vitals/labs dict matching ClinicalData fields.

    Returns:
        dict with keys:
            severity_score (float 0-1),
            risk_class (str in {I, II, III, IV, V}),
            heatmap_path (str | None),
            confidence_score (float 0-1).
    """
    severity = round(random.uniform(0.0, 1.0), 3)

    # Map severity roughly onto the 5 risk classes so outputs are internally consistent.
    idx = min(int(severity * len(RISK_CLASSES)), len(RISK_CLASSES) - 1)
    risk = RISK_CLASSES[idx]

    return {
        "severity_score": severity,
        "risk_class": risk,
        "heatmap_path": None,  # real model will emit a Grad-CAM overlay path
        "confidence_score": round(random.uniform(0.6, 0.99), 3),
    }
