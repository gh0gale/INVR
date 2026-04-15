import re
from typing import Dict, List, Tuple

class PortfolioNormalizer:
    """
    Normalizes noisy user portfolio descriptions into a standard sector weight model.
    """
    
    # Mapping of common terms to canonical sector names
    SECTOR_MAP = {
        "it": ["it", "tech", "software", "digital", "tcs", "infosys"],
        "banking": ["banking", "bank", "finance", "nbfc", "hdfc", "sbi", "loan"],
        "pharma": ["pharma", "health", "medicine", "doctor", "sun pharma"],
        "fmcg": ["fmcg", "consumer", "itc", "unilever", "household"],
        "auto": ["auto", "car", "vehicle", "maruti", "tata motors"],
        "infra": ["infra", "construction", "l&t", "building", "cement"]
    }

    def normalize(self, raw_text: str) -> Dict[str, Dict[str, float]]:
        """
        Processes text and returns a dictionary of weights.
        Example result: {"IT": {"min": 0.4, "max": 0.6}}
        """
        if not raw_text:
            return {}

        found_sectors = []
        text_lower = raw_text.lower()

        # Simple keyword matching
        for sector, keywords in self.SECTOR_MAP.items():
            for kw in keywords:
                if kw in text_lower:
                    found_sectors.append(sector)
                    break
        
        if not found_sectors:
            return {}

        # Equally distribute weights among found sectors for now
        # (Real fund manager logic: "mostly" = 50%+, "some" = 10-20%)
        # For simplicity, we assign equal ranges
        weight_per_sector = 1.0 / len(found_sectors)
        
        normalized_model = {}
        for sector in found_sectors:
            # We use a 15% variance range (e.g. 35% - 50%)
            min_w = max(0, weight_per_sector - 0.1)
            max_w = min(1.0, weight_per_sector + 0.1)
            normalized_model[sector.upper()] = {"min": round(min_w, 2), "max": round(max_w, 2)}
            
        return normalized_model
