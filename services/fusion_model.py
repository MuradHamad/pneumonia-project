"""FusionModel service — DenseNet121 multi-task pneumonia inference.

Loads model weights + clinical scaler once at startup via _load_artifacts().
Called from apps.cases.apps.CasesConfig.ready().

MODEL_AVAILABLE is False if the .pth or .joblib file is missing; diagnose()
raises RuntimeError in that case so the view can set status='FAILED'.
"""
from __future__ import annotations

import logging
import traceback
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODEL_AVAILABLE: bool = False
_model = None
_scaler = None
_grad_cam = None
_initialized: bool = False


# ── Model architecture ────────────────────────────────────────────────────────

def _build_model():
    """Instantiate MultiTaskPneumoniaModel.

    Attribute names must match the saved checkpoint exactly.
    self.vision_model = densenet  ← do NOT rename.
    """
    import torch.nn as nn
    import torchvision.models as tv_models
    import torch

    class MultiTaskPneumoniaModel(nn.Module):
        """DenseNet121 vision + 8-dim clinical MLP + shared fusion head.

        Forward returns two logits as (B,1) tensors:
            diag_logit, severity_logit
        Apply torch.sigmoid() to convert to probabilities.
        """

        def __init__(self, num_clinical_features: int = 8, num_classes: int = 2) -> None:
            super().__init__()
            densenet = tv_models.densenet121(weights=None)
            self.vision_features = densenet.classifier.in_features
            densenet.classifier = nn.Identity()
            self.vision_model = densenet  # attribute name locked by checkpoint

            self.clinical_mlp = nn.Sequential(
                nn.Linear(num_clinical_features, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, 32),
                nn.BatchNorm1d(32),
                nn.ReLU(),
                nn.Dropout(0.3),
            )
            fusion_dim = self.vision_features + 32
            self.fc = nn.Linear(fusion_dim, num_classes)

        def forward(self, img: torch.Tensor, clinical: torch.Tensor):
            img_feat = self.vision_model(img)
            clin_feat = self.clinical_mlp(clinical)
            fused = torch.cat((img_feat, clin_feat), dim=1)
            out = self.fc(fused)
            return out[:, 0].unsqueeze(1), out[:, 1].unsqueeze(1)

    return MultiTaskPneumoniaModel()


# ── Singleton loader ──────────────────────────────────────────────────────────

def _load_artifacts() -> None:
    """Load model + scaler once. Safe to call multiple times (idempotent)."""
    global MODEL_AVAILABLE, _model, _scaler, _grad_cam, _initialized
    if _initialized:
        return
    _initialized = True

    try:
        import torch
        import joblib
        from django.conf import settings
        from services.grad_cam import DenseNetGradCAM
        model_path = Path(settings.BASE_DIR) / "models" / "p3_best_densenet.pth"
        scaler_path = Path(settings.BASE_DIR) / "models" / "clinical_scaler.joblib"        
        if not model_path.exists():
            logger.warning(
                "Fusion model not found at %s — inference disabled.", model_path
            )
            return
        if not scaler_path.exists():
            logger.warning(
                "Clinical scaler not found at %s — inference disabled.", scaler_path
            )
            return

        model = _build_model()
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
        # الكود الذكي: إذا كان الملف checkpoint استخرج الأوزان منه، وإذا كان صافياً اقرأه مباشرة!
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        model.eval()

        _model = model
        _scaler = joblib.load(scaler_path)
        _grad_cam = DenseNetGradCAM(_model)
        MODEL_AVAILABLE = True
        logger.info("Fusion model loaded from %s", model_path)

    except Exception:
        logger.error("Failed to load fusion model:\n%s", traceback.format_exc())


# ── Image preprocessing ───────────────────────────────────────────────────────

def _get_preprocess():
    from torchvision import transforms as T
    return T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# ── Heatmap overlay & save ────────────────────────────────────────────────────

def _save_heatmap(original_pil, cam: Any, case_id: Any, media_root: Path) -> str:
    """Blend Grad-CAM overlay onto the X-ray and write to MEDIA_ROOT/heatmaps/."""
    import cv2
    import numpy as np

    orig_bgr = cv2.cvtColor(
        np.array(original_pil.resize((224, 224))), cv2.COLOR_RGB2BGR
    )
    colored = cv2.applyColorMap(cam, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(orig_bgr, 0.6, colored, 0.4, 0)

    heatmap_dir = media_root / "heatmaps"
    heatmap_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{case_id}.png"
    cv2.imwrite(str(heatmap_dir / filename), overlay)
    return f"heatmaps/{filename}"


# ── Public API ────────────────────────────────────────────────────────────────

def diagnose(
    xray_path: str,
    clinical_data: dict[str, Any],
    case_id: int | None = None,
) -> dict[str, Any]:
    """Run multi-task inference on a chest X-ray + clinical values.

    Args:
        xray_path: Path relative to MEDIA_ROOT (e.g. 'xrays/foo.png').
        clinical_data: Keys age, bun, hr, sys_bp, rr, temp_fahrenheit, spo2, gcs_total.
                       Temperature must already be in Fahrenheit.
        case_id: Used to name the saved heatmap file (defaults to a UUID).

    Returns:
        {
            "diag_probability": float 0.0–1.0,
            "severity_probability": float 0.0–1.0,
            "has_pneumonia": bool,
            "is_severe": bool,
            "heatmap_path": str (relative to MEDIA_ROOT) or None,
        }

    Raises:
        RuntimeError if the model is unavailable.
    """
    _load_artifacts()

    if not MODEL_AVAILABLE:
        raise RuntimeError(
            "Fusion model is unavailable. Ensure models/p3_best_densenet.pth "
            "and models/clinical_scaler.joblib exist."
        )

    import numpy as np
    import torch
    from django.conf import settings
    from PIL import Image

    media_root = Path(settings.MEDIA_ROOT)
    img_pil = Image.open(media_root / xray_path).convert("RGB")

    preprocess = _get_preprocess()
    img_tensor = preprocess(img_pil).unsqueeze(0)  # (1, 3, 224, 224)

    # Clinical input must be in exact order: age, bun, hr, sys_bp, rr, temp_f, spo2, gcs
    clinical_array = np.array(
        [[
            float(clinical_data["age"]),
            float(clinical_data["bun"]),
            float(clinical_data["hr"]),
            float(clinical_data["sys_bp"]),
            float(clinical_data["rr"]),
            float(clinical_data["temp_fahrenheit"]),
            float(clinical_data["spo2"]),
            float(clinical_data["gcs_total"]),
        ]],
        dtype=np.float32,
    )
    scaled = _scaler.transform(clinical_array)
    clinical_tensor = torch.from_numpy(scaled).float()

    # Inference pass
    with torch.no_grad():
        p_diag, p_sev = _model(img_tensor, clinical_tensor)
        diag_prob = float(torch.sigmoid(p_diag).item())
        sev_prob = float(torch.sigmoid(p_sev).item())

    # Grad-CAM pass (separate — needs gradients)
    heatmap_path: str | None = None
    try:
        cam = _grad_cam.generate_cam(img_tensor.clone(), clinical_tensor, target="diag")
        heatmap_path = _save_heatmap(
            img_pil, cam, case_id if case_id is not None else uuid.uuid4().hex, media_root
        )
    except Exception:
        logger.error(
            "Grad-CAM failed for case %s:\n%s", case_id, traceback.format_exc()
        )

    return {
        "diag_probability": round(diag_prob, 4),
        "severity_probability": round(sev_prob, 4),
        "has_pneumonia": diag_prob > 0.5,
        "is_severe": sev_prob > 0.5,
        "heatmap_path": heatmap_path,
    }
