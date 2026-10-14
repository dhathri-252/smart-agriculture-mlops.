"""General crop information for the 22 supported crops.

Numeric ranges are derived from the training dataset
(data/raw/crop_recommendation.csv, 5th-95th percentile per crop), so every
number shown to the user is grounded in real data rather than assumptions.

Guidance text is intentionally general and informational. It must not be
presented as a guarantee, and it does not replace local expert advice
for pesticide, chemical or serious disease decisions.

All human-readable text is bilingual: {"en": ..., "te": ...}.
"""

from typing import Optional

# Per-crop value ranges observed in the dataset (5th-95th percentile).
_DATASET_RANGES = {
    "apple": {"temperature": [21.2, 23.8], "humidity": [90.2, 94.7], "rainfall": [102.2, 123.6], "ph": [5.6, 6.4], "N": [2, 37], "P": [121, 144], "K": [195, 205]},
    "banana": {"temperature": [25.1, 29.4], "humidity": [76.1, 84.5], "rainfall": [90.8, 119.0], "ph": [5.6, 6.4], "N": [82, 117], "P": [71, 94], "K": [45, 55]},
    "blackgram": {"temperature": [25.7, 34.1], "humidity": [60.4, 69.1], "rainfall": [61.7, 74.2], "ph": [6.5, 7.7], "N": [21, 58], "P": [57, 79], "K": [15, 25]},
    "chickpea": {"temperature": [17.2, 20.7], "humidity": [14.4, 19.7], "rainfall": [68.5, 93.4], "ph": [6.2, 8.7], "N": [22, 59], "P": [56, 79], "K": [75, 85]},
    "coconut": {"temperature": [25.1, 29.5], "humidity": [91.0, 99.6], "rainfall": [134.0, 224.3], "ph": [5.6, 6.4], "N": [1, 39], "P": [6, 30], "K": [26, 35]},
    "coffee": {"temperature": [23.2, 27.6], "humidity": [51.1, 68.5], "rainfall": [120.6, 194.9], "ph": [6.1, 7.5], "N": [82, 118], "P": [17, 40], "K": [25, 35]},
    "cotton": {"temperature": [22.1, 25.7], "humidity": [75.6, 84.6], "rainfall": [62.6, 97.8], "ph": [6.0, 7.9], "N": [101, 136], "P": [36, 60], "K": [15, 25]},
    "grapes": {"temperature": [9.9, 40.7], "humidity": [80.1, 83.7], "rainfall": [65.5, 74.4], "ph": [5.6, 6.5], "N": [4, 39], "P": [120, 144], "K": [195, 205]},
    "jute": {"temperature": [23.2, 26.8], "humidity": [71.3, 88.4], "rainfall": [151.9, 196.7], "ph": [6.1, 7.4], "N": [61, 96], "P": [37, 58], "K": [35, 45]},
    "kidneybeans": {"temperature": [15.8, 24.3], "humidity": [18.3, 24.9], "rainfall": [63.3, 143.9], "ph": [5.5, 6.0], "N": [3, 37], "P": [56, 80], "K": [15, 25]},
    "lentil": {"temperature": [18.4, 29.2], "humidity": [60.5, 69.4], "rainfall": [36.1, 53.3], "ph": [6.1, 7.7], "N": [2, 38], "P": [57, 79], "K": [15, 24]},
    "maize": {"temperature": [18.3, 26.0], "humidity": [56.5, 73.6], "rainfall": [63.0, 108.5], "ph": [5.6, 6.9], "N": [61, 99], "P": [35, 60], "K": [15, 25]},
    "mango": {"temperature": [27.4, 35.5], "humidity": [45.6, 54.4], "rainfall": [90.0, 100.2], "ph": [4.7, 6.8], "N": [1, 39], "P": [16, 38], "K": [25, 35]},
    "mothbeans": {"temperature": [24.5, 31.2], "humidity": [41.8, 63.1], "rainfall": [32.7, 72.2], "ph": [3.7, 9.4], "N": [3, 39], "P": [36, 59], "K": [15, 25]},
    "mungbean": {"temperature": [27.1, 29.9], "humidity": [80.4, 89.7], "rainfall": [37.2, 58.5], "ph": [6.3, 7.2], "N": [2, 37], "P": [36, 59], "K": [15, 25]},
    "muskmelon": {"temperature": [27.1, 29.9], "humidity": [90.3, 94.8], "rainfall": [20.8, 29.0], "ph": [6.0, 6.7], "N": [82, 118], "P": [6, 28], "K": [45, 55]},
    "orange": {"temperature": [11.0, 34.1], "humidity": [90.2, 94.6], "rainfall": [101.1, 119.0], "ph": [6.1, 7.9], "N": [1, 39], "P": [6, 29], "K": [5, 15]},
    "papaya": {"temperature": [23.7, 42.9], "humidity": [90.2, 94.6], "rainfall": [51.0, 240.5], "ph": [6.5, 7.0], "N": [32, 69], "P": [47, 68], "K": [45, 55]},
    "pigeonpeas": {"temperature": [19.0, 36.2], "humidity": [32.5, 66.7], "rainfall": [94.4, 195.6], "ph": [4.7, 7.2], "N": [3, 39], "P": [56, 77], "K": [16, 25]},
    "pomegranate": {"temperature": [18.4, 24.8], "humidity": [85.6, 94.6], "rainfall": [102.9, 112.0], "ph": [5.7, 7.1], "N": [2, 40], "P": [6, 29], "K": [36, 45]},
    "rice": {"temperature": [20.3, 26.7], "humidity": [80.3, 84.6], "rainfall": [185.2, 290.7], "ph": [5.1, 7.6], "N": [60, 98], "P": [35, 59], "K": [35, 45]},
    "watermelon": {"temperature": [24.3, 26.8], "humidity": [80.5, 89.6], "rainfall": [41.1, 59.0], "ph": [6.1, 6.9], "N": [81, 119], "P": [6, 29], "K": [45, 55]},
}

# Display metadata + a short, crop-specific cultivation note (bilingual).
_META = {
    "apple": {"display": "Apple", "emoji": "\U0001F34E", "cultivation": {
        "en": "Train trees on a suitable rootstock; regular pruning and fruit thinning may improve quality.",
        "te": "మొక్కలకు తగిన వేర్ల రకం ఎంచుకోండి; క్రమం తప్పకుండా కత్తిరింపులు, పండ్ల తగ్గింపు నాణ్యత పెంచవచ్చు."}},
    "banana": {"display": "Banana", "emoji": "\U0001F34C", "cultivation": {
        "en": "Plant healthy suckers in well-drained pits; stake plants to support heavy bunches.",
        "te": "ఆరోగ్యకరమైన మొగ్గలను నీరు పోయే గుంతలలో నాటండి; పెద్ద దళ్ళకు మద్దతు ఇవ్వండి."}},
    "blackgram": {"display": "Black Gram", "emoji": "\U0001FAD8", "cultivation": {
        "en": "Sow after the recommended rains; keep the field weed-free in the first few weeks.",
        "te": "వర్షాల తర్వాత విత్తనాలు వేయండి; మొదటి కొన్ని వారాల్లో పొలం కలుపు లేకుండా చూడండి."}},
    "chickpea": {"display": "Chickpea", "emoji": "\U0001F33E", "cultivation": {
        "en": "Sow in the recommended season on well-drained loam; avoid waterlogging.",
        "te": "సూచించిన కాలంలో నీరు పోయే గొలుసు నేలలో విత్తండి; నీరు చేరకుండా జాగ్రత్త పడండి."}},
    "coconut": {"display": "Coconut", "emoji": "\U0001F965", "cultivation": {
        "en": "Allow adequate spacing between palms and mulch to conserve soil moisture.",
        "te": "చెట్ల మధ్య తగినంత ఖాళీ ఉంచి, నేల తేమను కాపాడటానికి మల్చండి."}},
    "coffee": {"display": "Coffee", "emoji": "☕", "cultivation": {
        "en": "Provide shade where needed and prune to keep an open, healthy canopy.",
        "te": "అవసరమైనచోట నీడ కల్పించి, చెట్టు ఎగువ భాగం తెరిచి ఉండేలా కత్తిరించండి."}},
    "cotton": {"display": "Cotton", "emoji": "\U0001F33F", "cultivation": {
        "en": "Maintain field hygiene and monitor for pests regularly so problems can be caught early.",
        "te": "పొలం శుభ్రత పాటించి, తెగుళ్ల కోసం క్రమం తప్పకుండా పరిశీలించండి."}},
    "grapes": {"display": "Grapes", "emoji": "\U0001F347", "cultivation": {
        "en": "Provide trellis support; prune and thin clusters for better airflow.",
        "te": "తీగ ఆధారం కల్పించండి; గాలి ప్రవాహం కోసం కత్తిరించి, గుత్తులు తగ్గించండి."}},
    "jute": {"display": "Jute", "emoji": "\U0001F33E", "cultivation": {
        "en": "Harvest at the right maturity and ret stems in clean water for better fibre.",
        "te": "సరైన పక్వానికి చేరినప్పుడు కోసి, మంచి నీటిలో నానబెట్టి గుజ్జు మెరుగుపరచండి."}},
    "kidneybeans": {"display": "Kidney Beans", "emoji": "\U0001FAD8", "cultivation": {
        "en": "Give support for climbing types and avoid waterlogging during flowering.",
        "te": "ఎగబాకే రకాలకు ఆధారం ఇవ్వండి; పుష్పించే సమయంలో నీరు చేరకుండా చూడండి."}},
    "lentil": {"display": "Lentil", "emoji": "\U0001FAD8", "cultivation": {
        "en": "Sow as a dry-season crop and avoid excess moisture during flowering.",
        "te": "పొడి కాలం పంటగా విత్తి, పుష్పించేటప్పుడు అధిక తేమ తగ్గించండి."}},
    "maize": {"display": "Maize", "emoji": "\U0001F33D", "cultivation": {
        "en": "Ensure even spacing; early weeding and earthing-up usually help.",
        "te": "సమాన దూరం పాటించండి; మొదట్లో కలుపు తీయడం, మట్టి ఎక్కించడం ఉపయోగపడతాయి."}},
    "mango": {"display": "Mango", "emoji": "\U0001F96D", "cultivation": {
        "en": "Prune to an open canopy and avoid damaging flowers during the hot season.",
        "te": "చెట్టు ఎగువ భాగం తెరిచి ఉండేలా కత్తిరించి, వేడికాలంలో పువ్వులకు దెబ్బ తగలకుండా చూడండి."}},
    "mothbeans": {"display": "Moth Beans", "emoji": "\U0001F331", "cultivation": {
        "en": "A hardy pulse suited to poorer soils; light irrigation may help at flowering.",
        "te": "సారం తక్కువ నేలలోనూ పెరిగే పప్పు పంట; పుష్పించేటప్పుడు తేలికపాటి నీటిపారుదల ఉపయోగపడుతుంది."}},
    "mungbean": {"display": "Mung Bean", "emoji": "\U0001F331", "cultivation": {
        "en": "A short-duration crop; harvest when pods begin to change colour.",
        "te": "తక్కువ కాలం పంట; కాయలు రంగు మారడం మొదలైనప్పుడు పంట కోయండి."}},
    "muskmelon": {"display": "Muskmelon", "emoji": "\U0001F348", "cultivation": {
        "en": "Give vines space to run and keep fruit off wet soil to reduce rot.",
        "te": "తీగలకు విస్తరించే ఖాళీ ఇవ్వండి; పండ్లు తడి నేలపై పడకుండా చూడండి."}},
    "orange": {"display": "Orange", "emoji": "\U0001F34A", "cultivation": {
        "en": "Prune for light and airflow, and thin fruit to keep the tree healthy.",
        "te": "వెలుతురు, గాలి కోసం కత్తిరించి, చెట్టు ఆరోగ్యానికి పండ్లు తగ్గించండి."}},
    "papaya": {"display": "Papaya", "emoji": "\U0001F96D", "cultivation": {
        "en": "Ensure good drainage around roots and protect plants from strong winds.",
        "te": "వేర్ల చుట్టూ నీరు పోయే ఏర్పాటు చేసి, గాలి నుంచి మొక్కలను కాపాడండి."}},
    "pigeonpeas": {"display": "Pigeon Peas", "emoji": "\U0001F331", "cultivation": {
        "en": "Provide good drainage and avoid waterlogging, especially after heavy rain.",
        "te": "మంచి నీరు పోయే ఏర్పాటు చేసి, ముఖ్యంగా భారీ వర్షం తర్వాత నీరు చేరకుండా చూడండి."}},
    "pomegranate": {"display": "Pomegranate", "emoji": "\U0001F345", "cultivation": {
        "en": "Prune to an open bush shape and thin fruit for better size and quality.",
        "te": "బుష్ ఆకారంలో కత్తిరించి, పరిమాణం, నాణ్యత కోసం పండ్లు తగ్గించండి."}},
    "rice": {"display": "Rice", "emoji": "\U0001F33E", "cultivation": {
        "en": "Transplant seedlings into puddled soil and keep weed control regular.",
        "te": "నారు మొక్కలను బంక నేలలో నాటి, క్రమం తప్పకుండా కలుపు నియంత్రణ చేయండి."}},
    "watermelon": {"display": "Watermelon", "emoji": "\U0001F349", "cultivation": {
        "en": "Give vines room to spread and turn fruit gently for even colour.",
        "te": "తీగలకు విస్తరించే ఖాళీ ఇవ్వండి; సమాన రంగు రావడానికి పండ్లను మెల్లగా తిప్పండి."}},
}

SUPPORTED_CROPS = sorted(_DATASET_RANGES.keys())

def _soil_text(ranges: dict) -> dict:
    ph_lo, ph_hi = ranges["ph"]
    return {
        "en": (
            f"Generally suits soil with pH around {ph_lo}–{ph_hi}. "
            "Use a fine, well-drained seedbed; consider a local soil test before applying fertiliser."
        ),
        "te": (
            f"నేల ఆమ్లత్వం {ph_lo}–{ph_hi} మధ్య ఉండేలా చూడండి. "
            "మెత్తని, నీరు పోయే నేల అనుకూలం; ఎరువులు వేసే ముందు స్థానికంగా నేల పరీక్ష చేయించుకోండి."
        ),
    }


def _irrigation_text(ranges: dict) -> dict:
    lo, hi = ranges["rainfall"]
    mid = (lo + hi) / 2
    if mid >= 150:
        en = (
            f"Typically grown with fairly high rainfall ({lo}–{hi} mm in the dataset). "
            "Fields may need good drainage, and light supplementary irrigation can still help in dry spells."
        )
        te = (
            f"ఈ పంట సాధారణంగా ఎక్కువ వర్షపాతం ({lo}–{hi} mm) ఉన్న ప్రాంతాల్లో పండిస్తారు. "
            "పొలానికి మంచి నీరు పోయే ఏర్పాటు అవసరం; తడి తక్కువగా ఉన్నప్పుడు తేలికపాటి అదనపు నీరు ఉపయోగపడవచ్చు."
        )
    elif mid >= 70:
        en = (
            f"Seen with moderate rainfall ({lo}–{hi} mm in the dataset). "
            "Supplementary irrigation may be considered during long dry spells."
        )
        te = (
            f"ఈ పంట మధ్యస్థ వర్షపాతం ({lo}–{hi} mm) తో కనిపిస్తుంది. "
            "పొడి రోజులు ఎక్కువగా ఉంటే అదనపు నీటిపారుదలను పరిగణించవచ్చు."
        )
    else:
        en = (
            f"Seen with lower rainfall ({lo}–{hi} mm in the dataset). "
            "Regular supplementary irrigation is often needed; avoid waterlogging."
        )
        te = (
            f"ఈ పంట తక్కువ వర్షపాతం ({lo}–{hi} mm) తో కనిపిస్తుంది. "
            "తరచుగా అదనపు నీటిపారుదల అవసరం కావచ్చు; నీరు చేరకుండా జాగ్రత్త పడండి."
        )
    return {"en": en, "te": te}


def _fertilizer_text(ranges: dict) -> dict:
    n, p, k = ranges["N"], ranges["P"], ranges["K"]
    return {
        "en": (
            f"Typical N–P–K levels seen for this crop in the dataset: N {n[0]}–{n[1]}, "
            f"P {p[0]}–{p[1]}, K {k[0]}–{k[1]}. Use these as a general guide only — "
            "a soil-test-based plan is usually better than fixed doses."
        ),
        "te": (
            f"డేటాలో ఈ పంటకు కనిపించిన సగటు N–P–K స్థాయిలు: N {n[0]}–{n[1]}, "
            f"P {p[0]}–{p[1]}, K {k[0]}–{k[1]}. ఇవి సాధారణ సూచన మాత్రమే — "
            "నేల పరీక్ష ఆధారంగా ఎరువులు వేయడం మేలు."
        ),
    }


def get_crop_info(crop: str) -> Optional[dict]:
    """Return full bilingual info card data for a crop, or None if unknown."""
    key = str(crop).strip().lower()
    if key not in _DATASET_RANGES or key not in _META:
        return None
    ranges = _DATASET_RANGES[key]
    meta = _META[key]
    return {
        "crop": key,
        "name": meta["display"],
        "emoji": meta["emoji"],
        "ranges": ranges,
        "soil": _soil_text(ranges),
        "irrigation": _irrigation_text(ranges),
        "fertilizer": _fertilizer_text(ranges),
        "cultivation": meta["cultivation"],
        "disclaimer": {
            "en": "General guidance only — conditions vary by location and season. Consult a local agricultural expert for pesticide or chemical decisions.",
            "te": "ఇది సాధారణ సూచన మాత్రమే — ప్రాంతం, కాలాన్ని బట్టి మారవచ్చు. పురుగు మందులు, రసాయనాల విషయంలో స్థానిక వ్యవసాయ నిపుణుడిని సంప్రదించండి.",
        },
    }
