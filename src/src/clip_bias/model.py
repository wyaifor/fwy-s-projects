from pathlib import Path

import numpy as np


def _load_torch():
    import torch

    return torch


def get_device():
    torch = _load_torch()
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ClipEncoder:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str | None = None):
        torch = _load_torch()
        from transformers import CLIPModel, CLIPProcessor

        self.device = torch.device(device) if device else get_device()
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def encode_texts(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        torch = _load_torch()
        from tqdm.auto import tqdm

        embeddings = []
        with torch.no_grad():
            for start in tqdm(range(0, len(texts), batch_size), desc="Encoding text"):
                batch = texts[start : start + batch_size]
                inputs = self.processor(text=batch, return_tensors="pt", padding=True, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                feats = self.model.get_text_features(**inputs)
                feats = torch.nn.functional.normalize(feats, dim=-1)
                embeddings.append(feats.cpu().numpy())
        return np.vstack(embeddings)

    def encode_images(self, image_paths: list[str], batch_size: int = 32) -> np.ndarray:
        torch = _load_torch()
        from PIL import Image
        from tqdm.auto import tqdm

        embeddings = []
        with torch.no_grad():
            for start in tqdm(range(0, len(image_paths), batch_size), desc="Encoding images"):
                paths = image_paths[start : start + batch_size]
                images = [Image.open(Path(path)).convert("RGB") for path in paths]
                inputs = self.processor(images=images, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                feats = self.model.get_image_features(**inputs)
                feats = torch.nn.functional.normalize(feats, dim=-1)
                embeddings.append(feats.cpu().numpy())
        return np.vstack(embeddings)
