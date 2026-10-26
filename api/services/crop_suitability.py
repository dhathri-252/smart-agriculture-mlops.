"""Rules-based crop suitability guidance for daily farming intelligence.

Honesty contract (must be preserved by API + UI):
- Every entry is ``rules_based_guidance`` — general educational information
  derived from widely known Indian agricultural season cycles (Kharif / Rabi /
  Zaid) and general crop needs. NOT verified against a cited publication.
- Never invent citations, planting dates, weather values, soil measurements,
  or yield estimates. Where a value is not known, it is omitted or marked
  general rather than fabricated.
- Never substitute weather data for missing soil measurements. Missing soil
  inputs degrade the suitability score honestly; they are never guessed from
  weather.
- Clearly separate from ML predictions: the 22-crop Random Forest model output
  is labelled ``ml_prediction``; everything here is ``rules_based_guidance`` or
  ``estimate``.
- Sources are listed only when they can be genuinely identified. General
  Indian agricultural extension knowledge is cited as such, with a recommendation
  to verify with ICAR / state agricultural extension services.

Season model (Andhra Pradesh / Telangana appropriate):
- Kharif (monsoon): June – September
- Rabi (winter): October – March
- Zaid (summer): March – June
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CropSuitability:
    """One crop's general cultivation suitability profile."""

    id: str
    name_en: str
    category: str
    emoji: str
    planting_months: list[int]  # 1..12, months suitable for planting
    water: str  # "low" | "medium" | "high"
    water_mm_note: Optional[str] = None
    soil_types: list[str] = field(default_factory=list)
    temp_min_c: Optional[float] = None
    temp_max_c: Optional[float] = None
    duration_days: Optional[int] = None
    risks: list[str] = field(default_factory=list)
    precautions: list[str] = field(default_factory=list)
    data_source: str = "General Indian agricultural guidance (Kharif/Rabi/Zaid cycles)"
    last_updated: Optional[str] = None

# ---------------------------------------------------------------------------
# Curated crop suitability table (~60 crops across 10 catalogue categories)
# ---------------------------------------------------------------------------
# Reuses catalogue crop IDs where they exist so the frontend can link to the
# existing catalogue (images, names, guides). Non-catalogue IDs are new
# entries added purely for daily-guidance coverage.
# ---------------------------------------------------------------------------

SUITABILITY_TABLE: list[CropSuitability] = [
    # ---- Vegetables ----
    CropSuitability(
        id="tomato", name_en="Tomato", category="vegetables", emoji="🍅",
        planting_months=[6, 7, 10, 11], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=15, temp_max_c=30,
        duration_days=90,
        risks=["fruit borer", "leaf curl", "blossom end rot"],
        precautions=["Stake plants; avoid waterlogging; rotate crops."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="potato", name_en="Potato", category="vegetables", emoji="🥔",
        planting_months=[10, 11], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=15, temp_max_c=25,
        duration_days=100,
        risks=["late blight", "frost damage"],
        precautions=["Use certified seed tubers; earth-up as plants grow."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="onion", name_en="Onion", category="vegetables", emoji="🧅",
        planting_months=[11, 12, 6, 7], water="medium",
        soil_types=["loamy", "sandy loam"],
        temp_min_c=12, temp_max_c=28, duration_days=110,
        risks=["thrips", "purple blotch", "neck rot"],
        precautions=["Well-drained beds; avoid excess nitrogen."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="chilli", name_en="Chilli", category="vegetables", emoji="🌶️",
        planting_months=[6, 7, 9, 10], water="medium",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=32,
        duration_days=120,
        risks=["leaf curl", "anthracnose", "dieback"],
        precautions=["Use disease-free seedlings; avoid water stagnation."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="brinjal", name_en="Brinjal (Eggplant)", category="vegetables", emoji="🍆",
        planting_months=[6, 7, 10, 11], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=22, temp_max_c=32,
        duration_days=110,
        risks=["fruit borer", "little leaf", "phomopsis blight"],
        precautions=["Stake plants; rotate; remove affected fruits."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="okra", name_en="Okra (Lady's Finger)", category="vegetables", emoji="🌿",
        planting_months=[6, 7, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=60,
        risks=["yellow vein mosaic", "aphids"],
        precautions=["Sow in warm soil; harvest pods regularly."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="cucumber", name_en="Cucumber", category="vegetables", emoji="🥒",
        planting_months=[2, 3, 6, 7], water="high",
        soil_types=["loamy"], temp_min_c=20, temp_max_c=30,
        duration_days=60,
        risks=["downy mildew", "powdery mildew", "fruit fly"],
        precautions=["Trellis vines; keep foliage dry; remove infected fruits."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="bitter_gourd", name_en="Bitter Gourd", category="vegetables", emoji="🥒",
        planting_months=[2, 3, 6, 7], water="high",
        soil_types=["loamy", "sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=75,
        risks=["downy mildew", "fruit fly"],
        precautions=["Trellis; remove affected fruits; rotate crops."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="pumpkin", name_en="Pumpkin", category="vegetables", emoji="🎃",
        planting_months=[6, 7, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=20, temp_max_c=32,
        duration_days=90,
        risks=["powdery mildew", "vine borer"],
        precautions=["Allow vines to spread; avoid waterlogging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="beans", name_en="Beans (French)", category="vegetables", emoji="🫘",
        planting_months=[10, 11, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=18, temp_max_c=28,
        duration_days=70,
        risks=["rust", "angular leaf spot", "bean fly"],
        precautions=["Use trellis for pole varieties; avoid overhead watering."],
        last_updated="2024-11-01",
    ),
    # ---- Fruits ----
    CropSuitability(
        id="mango", name_en="Mango", category="fruits", emoji="🥭",
        planting_months=[7, 8], water="medium",
        soil_types=["loamy", "lateritic"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["powdery mildew", "fruit fly", "dieback"],
        precautions=["Plant in well-drained site; avoid frost pockets."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="banana", name_en="Banana", category="fruits", emoji="🍌",
        planting_months=[6, 7, 9, 10], water="high",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["panama wilt", "sigatoka", "nematodes"],
        precautions=["Use tissue-culture suckers; ensure good drainage."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="apple", name_en="Apple", category="fruits", emoji="🍎",
        planting_months=[12, 1, 2], water="medium",
        soil_types=["loamy"], temp_min_c=10, temp_max_c=25,
        duration_days=None,
        risks=["scab", "powdery mildew", "canker"],
        precautions=["Requires chill hours; plant on slopes for drainage."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="pomegranate", name_en="Pomegranate", category="fruits", emoji="🍎",
        planting_months=[7, 8, 2, 3], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=15, temp_max_c=35,
        duration_days=None,
        risks=["bacterial blight", "fruit spot"],
        precautions=["Drought-tolerant; avoid waterlogging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="papaya", name_en="Papaya", category="fruits", emoji="🍈",
        planting_months=[6, 7, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=22, temp_max_c=35,
        duration_days=None,
        risks=["papaya ringspot", "powdery mildew", "anthracnose"],
        precautions=["Well-drained soil; protect from wind."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="guava", name_en="Guava", category="fruits", emoji="🍈",
        planting_months=[7, 8, 2, 3], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=18, temp_max_c=35,
        duration_days=None,
        risks=["fruit fly", "wilt", "anthracnose"],
        precautions=["Hardy; minimal irrigation once established."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="watermelon", name_en="Watermelon", category="fruits", emoji="🍉",
        planting_months=[2, 3, 6, 7], water="high",
        soil_types=["sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=80,
        risks=["powdery mildew", "anthracnose", "fruit fly"],
        precautions=["Needs warm weather; reduce watering as fruit matures."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="muskmelon", name_en="Muskmelon", category="fruits", emoji="🍈",
        planting_months=[2, 3, 6, 7], water="high",
        soil_types=["sandy loam"], temp_min_c=22, temp_max_c=35,
        duration_days=75,
        risks=["powdery mildew", "downy mildew"],
        precautions=["Well-drained soil; avoid overhead irrigation."],
        last_updated="2024-11-01",
    ),
    # ---- Flowers ----
    CropSuitability(
        id="marigold", name_en="Marigold", category="medicinal_aromatic", emoji="🌸",
        planting_months=[6, 7, 9, 10], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=18, temp_max_c=30,
        duration_days=70,
        risks=["powdery mildew", "stem rot"],
        precautions=["Deadhead regularly; well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="jasmine", name_en="Jasmine", category="medicinal_aromatic", emoji="🌸",
        planting_months=[6, 7, 8, 9], water="medium",
        soil_types=["loamy"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["budworm", "leaf web"],
        precautions=["Prune after flowering; regular watering."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="rose", name_en="Rose", category="medicinal_aromatic", emoji="🌹",
        planting_months=[10, 11, 12, 1], water="medium",
        soil_types=["loamy"], temp_min_c=15, temp_max_c=30,
        duration_days=None,
        risks=["black spot", "powdery mildew", "aphids"],
        precautions=["Prune in winter; good air circulation."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="hibiscus", name_en="Hibiscus", category="medicinal_aromatic", emoji="🌺",
        planting_months=[6, 7, 8, 9], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["mealybug", "aphids", "leaf spot"],
        precautions=["Prune regularly; full sun."],
        last_updated="2024-11-01",
    ),
    # ---- Dry fruits and nuts ----
    CropSuitability(
        id="cashew", name_en="Cashew", category="plantation_beverage", emoji="🥥",
        planting_months=[6, 7, 8, 9], water="low",
        soil_types=["sandy loam", "lateritic"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["powdery mildew", "dieback", "stem borer"],
        precautions=["Drought-tolerant; avoid waterlogged sites."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="almond", name_en="Almond", category="fruits", emoji="🌰",
        planting_months=[12, 1, 2], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=10, temp_max_c=30,
        duration_days=None,
        risks=["fungal diseases", "frost"],
        precautions=["Needs well-drained soil; winter chill."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="walnut", name_en="Walnut", category="fruits", emoji="🌰",
        planting_months=[12, 1, 2], water="medium",
        soil_types=["loamy"], temp_min_c=5, temp_max_c=28,
        duration_days=None,
        risks=["blight", "canker", "frost"],
        precautions=["Needs chill hours; deep well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="coconut", name_en="Coconut", category="plantation_beverage", emoji="🥥",
        planting_months=[6, 7, 8, 9], water="medium",
        soil_types=["sandy loam", "loamy"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["bud rot", "stem bleeding", "rhinoceros beetle"],
        precautions=["Coastal/tropical; good drainage; regular irrigation in dry spells."],
        last_updated="2024-11-01",
    ),
    # ---- Cereals and millets ----
    CropSuitability(
        id="rice", name_en="Rice", category="cereals_millets", emoji="🌾",
        planting_months=[6, 7, 8], water="high",
        soil_types=["clay", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=120,
        risks=["blast", "brown spot", "stem borer"],
        precautions=["Flooded fields; transplant seedlings; timely nitrogen."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="maize", name_en="Maize", category="cereals_millets", emoji="🌽",
        planting_months=[6, 7, 10, 11], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=18, temp_max_c=32,
        duration_days=90,
        risks=["stem borer", "fall armyworm", "leaf blight"],
        precautions=["Well-drained soil; avoid waterlogging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="wheat", name_en="Wheat", category="cereals_millets", emoji="🌾",
        planting_months=[10, 11, 12], water="medium",
        soil_types=["loamy", "clay loam"], temp_min_c=10, temp_max_c=25,
        duration_days=120,
        risks=["rust", "powdery mildew", "termite"],
        precautions=["Cool season crop; avoid late sowing."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="bajra", name_en="Pearl Millet (Bajra)", category="cereals_millets", emoji="🌾",
        planting_months=[6, 7, 8], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=25, temp_max_c=35,
        duration_days=75,
        risks=["downy mildew", "ergot", "stem borer"],
        precautions=["Drought-tolerant; light soils."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="jowar", name_en="Sorghum (Jowar)", category="cereals_millets", emoji="🌾",
        planting_months=[6, 7, 10, 11], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=95,
        risks=["anthracnose", "grain mold", "shoot fly"],
        precautions=["Drought-tolerant; well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="ragi", name_en="Finger Millet (Ragi)", category="cereals_millets", emoji="🌾",
        planting_months=[6, 7, 8], water="low",
        soil_types=["loamy", "red loam"], temp_min_c=20, temp_max_c=30,
        duration_days=100,
        risks=["blast", "leaf spot"],
        precautions=["Millets suit dryland farming."],
        last_updated="2024-11-01",
    ),
    # ---- Pulses and legumes ----
    CropSuitability(
        id="chickpea", name_en="Chickpea (Bengal Gram)", category="pulses_legumes", emoji="🫘",
        planting_months=[10, 11], water="low",
        soil_types=["loamy", "clay loam"], temp_min_c=15, temp_max_c=30,
        duration_days=100,
        risks=["wilt", "root rot", "pod borer"],
        precautions=["Rabi crop; minimal irrigation; well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="blackgram", name_en="Blackgram (Urad)", category="pulses_legumes", emoji="🫘",
        planting_months=[6, 7, 10, 11], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=75,
        risks=["yellow mosaic", "leaf spot", "pod borer"],
        precautions=["Short-duration; fits rice fallows."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="greengram", name_en="Greengram (Mungbean)", category="pulses_legumes", emoji="🫘",
        planting_months=[6, 7, 2, 3], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=25, temp_max_c=35,
        duration_days=65,
        risks=["yellow mosaic", "powdery mildew", "thrips"],
        precautions=["Short-duration; drought-tolerant."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="redgram", name_en="Redgram (Pigeonpea/Arhar)", category="pulses_legumes", emoji="🫘",
        planting_months=[6, 7], water="low",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=150,
        risks=["wilt", "sterility mosaic", "pod borer"],
        precautions=["Long-duration; deep soils."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="cowpea", name_en="Cowpea", category="pulses_legumes", emoji="🫘",
        planting_months=[6, 7, 2, 3], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=20, temp_max_c=35,
        duration_days=70,
        risks=["aphids", "mosaic virus", "pod borer"],
        precautions=["Drought-tolerant; short-duration."],
        last_updated="2024-11-01",
    ),
    # ---- Spices ----
    CropSuitability(
        id="turmeric", name_en="Turmeric", category="spices_condiments", emoji="🌿",
        planting_months=[6, 7], water="medium",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=240,
        risks=["rhizome rot", "leaf spot", "shoot borer"],
        precautions=["Well-drained soil; shade nets in summer."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="coriander", name_en="Coriander", category="spices_condiments", emoji="🌿",
        planting_months=[10, 11, 12], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=15, temp_max_c=28,
        duration_days=90,
        risks=["powdery mildew", "wilt", "aphids"],
        precautions=["Cool season; avoid waterlogging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="cumin", name_en="Cumin", category="spices_condiments", emoji="🌿",
        planting_months=[11, 12], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=15, temp_max_c=30,
        duration_days=110,
        risks=["wilt", "blight", "aphids"],
        precautions=["Dry weather at maturity; light soils."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="fenugreek", name_en="Fenugreek (Methi)", category="spices_condiments", emoji="🌿",
        planting_months=[10, 11], water="medium",
        soil_types=["loamy"], temp_min_c=15, temp_max_c=30,
        duration_days=75,
        risks=["root rot", "powdery mildew"],
        precautions=["Cool season; multiple cuts for leaves."],
        last_updated="2024-11-01",
    ),
    # ---- Oilseeds ----
    CropSuitability(
        id="groundnut", name_en="Groundnut (Peanut)", category="oilseeds", emoji="🥜",
        planting_months=[6, 7, 10, 11], water="medium",
        soil_types=["sandy loam", "loamy"], temp_min_c=25, temp_max_c=35,
        duration_days=110,
        risks=["leaf spot", "rust", "aflatoxin"],
        precautions=["Light well-drained soil; calcium at pegging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="sunflower", name_en="Sunflower", category="oilseeds", emoji="🌻",
        planting_months=[10, 11, 6, 7], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=20, temp_max_c=32,
        duration_days=90,
        risks=["downy mildew", "rust", "head rot"],
        precautions=["Avoid waterlogging; bird protection at maturity."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="sesame", name_en="Sesame (Til)", category="oilseeds", emoji="🌱",
        planting_months=[6, 7], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=25, temp_max_c=35,
        duration_days=85,
        risks=["leaf spot", "phyllody", "leaf roller"],
        precautions=["Drought-tolerant; sensitive to waterlogging."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="mustard", name_en="Mustard", category="oilseeds", emoji="🌱",
        planting_months=[10, 11], water="low",
        soil_types=["loamy", "sandy loam"], temp_min_c=10, temp_max_c=28,
        duration_days=100,
        risks=["aphids", "white rust", "alternaria blight"],
        precautions=["Rabi oilseed; cool weather."],
        last_updated="2024-11-01",
    ),
    # ---- Commercial crops ----
    CropSuitability(
        id="cotton", name_en="Cotton", category="fibre_sugar_commercial", emoji="🧵",
        planting_months=[6, 7, 8], water="medium",
        soil_types=["clay", "loamy"], temp_min_c=20, temp_max_c=35,
        duration_days=160,
        risks=["bollworm", "leaf curl", "whitefly"],
        precautions=["Long-duration; balanced fertilizer; pest scouting."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="sugarcane", name_en="Sugarcane", category="fibre_sugar_commercial", emoji="🍯",
        planting_months=[6, 7, 10, 11], water="high",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=300,
        risks=["red rot", "smut", "borer"],
        precautions=["Long-duration; heavy irrigation; well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="tobacco", name_en="Tobacco", category="fibre_sugar_commercial", emoji="🌿",
        planting_months=[10, 11], water="medium",
        soil_types=["sandy loam"],
        temp_min_c=20, temp_max_c=30, duration_days=120,
        risks=["mosaic virus", "leaf spot", "root rot"],
        precautions=["Light sandy soil; careful curing."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="jute", name_en="Jute", category="fibre_sugar_commercial", emoji="🌿",
        planting_months=[5, 6], water="high",
        soil_types=["loamy", "clay loam"], temp_min_c=25, temp_max_c=35,
        duration_days=120,
        risks=["stem rot", "leaf spot", "stem borer"],
        precautions=["Warm humid climate; retting needs water."],
        last_updated="2024-11-01",
    ),
    # ---- Plantation crops ----
    CropSuitability(
        id="coffee", name_en="Coffee", category="plantation_beverage", emoji="☕",
        planting_months=[6, 7, 8], water="medium",
        soil_types=["loamy", "lateritic"], temp_min_c=15, temp_max_c=28,
        duration_days=None,
        risks=["leaf rust", "berry borer", "root rot"],
        precautions=["Shade-grown; hill slopes; well-distributed rainfall."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="tea", name_en="Tea", category="plantation_beverage", emoji="☕",
        planting_months=[6, 7, 8], water="high",
        soil_types=["loamy", "lateritic"], temp_min_c=15, temp_max_c=28,
        duration_days=None,
        risks=["blister blight", "red spider mite"],
        precautions=["High rainfall; acidic soil; hill slopes."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="rubber", name_en="Rubber", category="plantation_beverage", emoji="🌳",
        planting_months=[6, 7, 8], water="high",
        soil_types=["loamy", "lateritic"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["leaf disease", "root rot"],
        precautions=["Tropical high-rainfall areas."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="arecanut", name_en="Arecanut (Betel Nut)", category="plantation_beverage", emoji="🌴",
        planting_months=[6, 7], water="high",
        soil_types=["loamy", "lateritic"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["bud rot", "koleroga", "spindle bug"],
        precautions=["High humidity; well-drained soil."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="blackpepper", name_en="Black Pepper", category="plantation_beverage", emoji="🌿",
        planting_months=[6, 7], water="high",
        soil_types=["loamy", "lateritic"], temp_min_c=20, temp_max_c=30,
        duration_days=None,
        risks=["quick wilt", "pollu disease"],
        precautions=["Needs support tree; shade; high humidity."],
        last_updated="2024-11-01",
    ),
    # ---- Fodder and forage ----
    CropSuitability(
        id="berseem", name_en="Berseem", category="fodder_forage", emoji="☘️",
        planting_months=[10, 11], water="medium",
        soil_types=["loamy", "clay loam"], temp_min_c=15, temp_max_c=30,
        duration_days=None,
        risks=["stem rot", "leaf spot"],
        precautions=["Rabi legume fodder with multiple cuts."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="napier", name_en="Napier Grass", category="fodder_forage", emoji="🌿",
        planting_months=[6, 7, 8], water="medium",
        soil_types=["loamy", "clay loam"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["leaf spot", "stem rot"],
        precautions=["Tall perennial grass; cut at waist height."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="clover", name_en="Clover", category="fodder_forage", emoji="☘️",
        planting_months=[10, 11], water="medium",
        soil_types=["loamy"], temp_min_c=10, temp_max_c=25,
        duration_days=None,
        risks=["root rot", "powdery mildew"],
        precautions=["Legume fodder and cover; suits cool moist areas."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="alfalfa", name_en="Alfalfa (Lucerne)", category="fodder_forage", emoji="🌿",
        planting_months=[10, 11], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=10, temp_max_c=30,
        duration_days=None,
        risks=["leaf spot", "root rot"],
        precautions=["Perennial legume fodder; cut at early flowering."],
        last_updated="2024-11-01",
    ),
    # ---- Medicinal and aromatic ----
    CropSuitability(
        id="tulsi", name_en="Tulsi (Holy Basil)", category="medicinal_aromatic", emoji="🌿",
        planting_months=[6, 7, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["leaf spot", "aphids"],
        precautions=["Homestead medicinal; pinch flowers for leaf."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="ashwagandha", name_en="Ashwagandha", category="medicinal_aromatic", emoji="🌱",
        planting_months=[6, 7, 10, 11], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["root rot", "leaf spot"],
        precautions=["Dryland medicinal root; harvest at maturity."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="aloevera", name_en="Aloe Vera", category="medicinal_aromatic", emoji="🌵",
        planting_months=[6, 7, 2, 3], water="low",
        soil_types=["sandy loam", "loamy"], temp_min_c=15, temp_max_c=35,
        duration_days=None,
        risks=["root rot", "leaf spot"],
        precautions=["Succulent for dry borders; harvest outer leaves."],
        last_updated="2024-11-01",
    ),
    CropSuitability(
        id="lemongrass", name_en="Lemongrass", category="medicinal_aromatic", emoji="🌱",
        planting_months=[6, 7, 2, 3], water="medium",
        soil_types=["loamy", "sandy loam"], temp_min_c=20, temp_max_c=35,
        duration_days=None,
        risks=["leaf blight", "aphids"],
        precautions=["Aromatic border grass; cut leaves for oil."],
        last_updated="2024-11-01",
    ),
]


# ---------------------------------------------------------------------------
# Season helpers
# ---------------------------------------------------------------------------

_SEASON_MONTHS = {
    "kharif": {6, 7, 8, 9},
    "rabi": {10, 11, 12, 1, 2, 3},
    "zaid": {3, 4, 5, 6},
}


def season_for(date_or_month: date | int) -> str:
    """Return the agricultural season name for a date or month number (1-12).

    Andhra Pradesh / Telangana convention:
      Kharif: June–September  |  Rabi: October–March  |  Zaid: March–June
    March and June overlap two seasons; both are returned as a set.
    """
    month = date_or_month.month if isinstance(date_or_month, date) else int(date_or_month)
    matched = [s for s, months in _SEASON_MONTHS.items() if month in months]
    if not matched:
        return "rabi"
    return matched[0] if len(matched) == 1 else "kharif/zaid overlap"


def seasons_for_month(month: int) -> list[str]:
    """Return all seasons a month belongs to (handles overlaps)."""
    return [s for s, months in _SEASON_MONTHS.items() if month in months] or ["rabi"]


_VALID_CATEGORIES = {
    "vegetables", "fruits", "cereals_millets", "pulses_legumes", "oilseeds",
    "fibre_sugar_commercial", "spices_condiments", "plantation_beverage",
    "fodder_forage", "medicinal_aromatic",
}


def category_is_valid(category: str) -> bool:
    """Return True if ``category`` is one of the 10 catalogue-approved IDs."""
    return category in _VALID_CATEGORIES


def crops_by_category(category: str) -> list:
    """All suitability entries for a catalogue-approved category."""
    return [c for c in SUITABILITY_TABLE if c.category == category]


# ---------------------------------------------------------------------------
# Ranking / scoring
# ---------------------------------------------------------------------------

_WEIGHT_SEASON = 40
_WEIGHT_WEATHER = 30
_WEIGHT_SOIL = 20
_WEIGHT_WATER = 10


def _season_match_score(crop: CropSuitability, season: str) -> int:
    """Season alignment: how well the crop's planting months match the season."""
    season_months = _SEASON_MONTHS.get(season, set())
    overlap = sum(1 for m in crop.planting_months if m in season_months)
    if overlap == 0:
        return 0
    if overlap >= len(crop.planting_months) // 2:
        return _WEIGHT_SEASON
    return _WEIGHT_SEASON // 2


def _weather_match_score(crop: CropSuitability, temperature_c: Optional[float],
                          condition: Optional[str]) -> int:
    """Temperature-band fit against current weather (when available)."""
    if temperature_c is None:
        return _WEIGHT_WEATHER // 2  # neutral when no weather
    tmin = crop.temp_min_c or 0
    tmax = crop.temp_max_c or 50
    if tmin <= temperature_c <= tmax:
        return _WEIGHT_WEATHER
    if (tmin - 5) <= temperature_c <= (tmax + 5):
        return _WEIGHT_WEATHER // 2
    return 0


def _soil_match_score(crop: CropSuitability, farmer_soil: Optional[str]) -> int:
    """Soil match only when the farmer actually provided soil data.

    Never guesses soil from weather. Missing soil input => neutral score.
    """
    if not farmer_soil:
        return _WEIGHT_SOIL // 2  # neutral: no soil data, no penalty
    soil_lower = farmer_soil.lower()
    for st in crop.soil_types:
        if soil_lower in st or st in soil_lower:
            return _WEIGHT_SOIL
    return 0


def _water_match_score(crop: CropSuitability, water_available: Optional[str]) -> int:
    """Water-availability fit (low/medium/high) when farmer supplies it."""
    if not water_available:
        return _WEIGHT_WATER // 2  # neutral
    order = {"low": 0, "medium": 1, "high": 2}
    crop_level = order.get(crop.water, 1)
    farmer_level = order.get(water_available.lower(), 1)
    if abs(crop_level - farmer_level) <= 0:
        return _WEIGHT_WATER
    if abs(crop_level - farmer_level) == 1:
        return _WEIGHT_WATER // 2
    return 0


def rank_crops(crops: list[CropSuitability], season: str,
               temperature_c: Optional[float] = None,
               condition: Optional[str] = None,
               farmer_soil: Optional[str] = None,
               water_available: Optional[str] = None) -> list[CropSuitability]:
    """Rank crops by suitability score. Stable sort preserves table order for ties."""

    def score(c: CropSuitability) -> int:
        return (
            _season_match_score(c, season)
            + _weather_match_score(c, temperature_c, condition)
            + _soil_match_score(c, farmer_soil)
            + _water_match_score(c, water_available)
        )

    return sorted(crops, key=score, reverse=True)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_by_id: dict[str, CropSuitability] = {c.id: c for c in SUITABILITY_TABLE}


def get_suitability(crop_id: str) -> Optional[CropSuitability]:
    return _by_id.get(crop_id)


def all_suitability() -> list[CropSuitability]:
    return list(SUITABILITY_TABLE)


def planting_months_for(month: int) -> list[CropSuitability]:
    """Crops suitable for planting in a given calendar month (1-12)."""
    return [c for c in SUITABILITY_TABLE if month in c.planting_months]