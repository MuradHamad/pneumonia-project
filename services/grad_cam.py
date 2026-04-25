"""Grad-CAM for MultiTaskPneumoniaModel.

Target layer: model.vision_model.features[-1] (DenseNet norm5 — last BN before GAP).
Returns a uint8 numpy array (0–255) of shape (224, 224).

Notebook reference: project2.ipynb Cell 11/12, with these fixes:
  - Target layer is model.vision_model.features[-1], not model.img_extractor[-1]
  - Use p_diag.squeeze().backward(), not p_diag[0].backward()
"""
from __future__ import annotations

import logging

import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class DenseNetGradCAM:
    """Grad-CAM wrapper for MultiTaskPneumoniaModel.

    Create ONCE per model instance and reuse. The hooks registered in __init__
    accumulate no state between calls — each generate_cam() overwrites them.
    """

    def __init__(self, model: torch.nn.Module) -> None:
        self.model = model
        self._activations: torch.Tensor | None = None
        self._gradients: torch.Tensor | None = None

        target_layer = model.vision_model.features.denseblock4
        target_layer.register_forward_hook(self._forward_hook)
        target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output) -> None:
        self._activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output) -> None:
        self._gradients = grad_output[0].detach()

    def generate_cam(
        self,
        img_tensor: torch.Tensor,
        clinical_tensor: torch.Tensor,
        target: str = "diag",
    ) -> np.ndarray:
        """Forward + backward pass to produce a 224×224 Grad-CAM array (uint8).

        Args:
            img_tensor: Preprocessed image, shape (1, 3, 224, 224).
            clinical_tensor: Scaled clinical features, shape (1, 8).
            target: 'diag' uses the diagnostic head; 'severity' uses severity head.

        Returns:
            uint8 numpy array of shape (224, 224), values 0–255.
        """
        self.model.eval()
        self.model.zero_grad()

        p_diag, p_sev = self.model(img_tensor, clinical_tensor)

        if target == "diag":
            p_diag.squeeze().backward()
        else:
            p_sev.squeeze().backward()

        if self._activations is None or self._gradients is None:
            raise RuntimeError(
                "Grad-CAM hooks did not fire. "
                "Check that target layer is model.vision_model.features[-1]."
            )

        # Global-average-pool gradients → per-channel importance weights
        weights = self._gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        cam = (weights * self._activations).sum(dim=1).squeeze()   # (H, W)
        cam = F.relu(cam)
        cam_np = cam.cpu().numpy()

        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        cam_np = (cam_np * 255).astype(np.uint8)

        try:
            import cv2
            cam_np = cv2.resize(cam_np, (224, 224))
        except ImportError:
            from PIL import Image as _PIL
            cam_np = np.array(_PIL.fromarray(cam_np).resize((224, 224)))

        return cam_np
