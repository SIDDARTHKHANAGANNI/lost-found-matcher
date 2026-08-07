import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

_MODEL_NAME = "openai/clip-vit-base-patch32"

class EmbeddingService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(_MODEL_NAME).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(_MODEL_NAME)
        self.model.eval()

    @torch.no_grad()
    def embed_image(self, image_path: str) -> list[float]:
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        features = self.model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze(0).cpu().tolist()

    @torch.no_grad()
    def embed_text(self, text: str) -> list[float]:
        inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        features = self.model.get_text_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze(0).cpu().tolist()

    def embed_combined(self, image_path: str, text: str, image_weight: float = 0.7) -> list[float]:
        img_emb = self.embed_image(image_path)
        txt_emb = self.embed_text(text)
        combined = [
            image_weight * i + (1 - image_weight) * t
            for i, t in zip(img_emb, txt_emb)
        ]
        norm = sum(x ** 2 for x in combined) ** 0.5
        return [x / norm for x in combined]

# singleton — load model once at startup, not per-request
embedding_service = EmbeddingService()