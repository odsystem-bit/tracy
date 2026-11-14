"""Module vision de Tracy Core.

Contient:
- product_vision: Identification produit par photo (CLIP + YOLOv8)
- authenticity: Vérification d'authenticité des photos produit
- conformity: Conformité post-livraison
- shop_quality: Score de qualité boutique
"""

from app.vision.product_vision import (
    ProductVisionEngine,
    get_product_vision_engine,
    IdentifyResult,
    ProductMatch,
    ProductEmbedding,
)
from app.vision.authenticity import (
    AuthenticityEngine,
    get_authenticity_engine,
    AuthenticityCheck,
)
from app.vision.conformity import (
    ConformityEngine,
    get_conformity_engine,
    ConformityCheck,
    ConformityVerdict,
)
from app.vision.shop_quality import (
    ShopQualityEngine,
    get_shop_quality_engine,
    ShopQualityScore,
    QualitySignal,
    QualitySignalType,
)

__all__ = [
    "ProductVisionEngine", "get_product_vision_engine", "IdentifyResult", "ProductMatch", "ProductEmbedding",
    "AuthenticityEngine", "get_authenticity_engine", "AuthenticityCheck",
    "ConformityEngine", "get_conformity_engine", "ConformityCheck", "ConformityVerdict",
    "ShopQualityEngine", "get_shop_quality_engine", "ShopQualityScore", "QualitySignal", "QualitySignalType",
]
