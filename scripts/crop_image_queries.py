"""Per-crop Wikimedia Commons search queries + title keywords.

Each entry: (stable crop id, search query, [title keywords]).
A candidate file is accepted only if its Commons title contains at least one
keyword AND its API-reported license is freely licensed. Queries are written
to return the actual crop (not a product, dish, or unrelated homonym).
"""

QUERIES = [
    # ---- Vegetables (30) ----
    ("tomato", "tomato fruit plant", ["tomato"]),
    ("potato", "potato tuber harvest", ["potato"]),
    ("onion", "onion bulbs harvest", ["onion"]),
    ("garlic", "garlic bulbs", ["garlic"]),
    ("brinjal", "eggplant brinjal fruit plant", ["eggplant", "brinjal", "aubergine", "solanum melongena"]),
    ("chilli", "chili peppers plant", ["chili", "chilli", "hot pepper"]),
    ("capsicum", "bell pepper sweet pepper plant", ["bell pepper", "sweet pepper"]),
    ("okra", "okra ladyfinger plant pods", ["okra", "ladyfinger", "abelmoschus"]),
    ("cabbage", "cabbage head field", ["cabbage"]),
    ("cauliflower", "cauliflower curd field", ["cauliflower"]),
    ("broccoli", "broccoli field", ["broccoli"]),
    ("carrot", "carrots roots harvest", ["carrot"]),
    ("radish", "radish roots field", ["radish"]),
    ("beetroot", "beetroot red beet roots", ["beetroot", "red beet", "garden beet", "beta vulgaris"]),
    ("spinach", "spinach leaves field", ["spinach"]),
    ("amaranth", "amaranth leaves vegetable", ["amaranth", "chaulai", "thotakura"]),
    ("cucumber", "cucumber vine fruit", ["cucumber"]),
    ("pumpkin", "pumpkin fruit field", ["pumpkin"]),
    ("bottle_gourd", "bottle gourd calabash vine", ["bottle gourd", "calabash", "lagenaria"]),
    ("bitter_gourd", "bitter gourd bitter melon vine", ["bitter gourd", "bitter melon", "momordica"]),
    ("ridge_gourd", "ridge gourd luffa vine", ["ridge gourd", "luffa", "angled gourd"]),
    ("snake_gourd", "snake gourd trichosanthes vine", ["snake gourd", "trichosanthes", "padwal"]),
    ("ash_gourd", "ash gourd winter melon vine", ["ash gourd", "winter melon", "benincasa", "petha"]),
    ("beans", "green beans french beans plant", ["green bean", "french bean", "string bean"]),
    ("peas", "green peas garden pea pods", ["garden pea", "green pea", "pisum sativum"]),
    ("sweet_potato", "sweet potato roots harvest", ["sweet potato", "ipomoea batatas"]),
    ("yam", "yam tubers dioscorea harvest", ["yam", "dioscorea", "elephant foot"]),
    ("colocasia", "taro colocasia corms field", ["taro", "colocasia", "arbi"]),
    ("drumstick", "moringa drumstick tree pods", ["moringa", "drumstick", "sahjan"]),
    ("sweet_corn", "sweet corn cob harvest", ["sweet corn", "corn cob", "baby corn"]),
]
