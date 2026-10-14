"""Agriculture assistant service with a provider abstraction.

Providers (selected via environment, see api/config):
- ``openai``: any OpenAI-compatible chat completions endpoint. The API key is
  read server-side from OPENAI_API_KEY and is NEVER sent to the frontend.
- ``knowledge_base``: built-in bilingual (en/te) answers for common farming
  questions. Used automatically when no AI provider/key is configured, and as
  a fallback if the external provider fails.

Every response carries an informational disclaimer — this assistant does not
replace expert agricultural advice for serious crop disease, pesticide or
chemical decisions.
"""

import json
import logging
import re
import urllib.error
import urllib.request

from api.config import (
    get_ai_provider,
    get_openai_api_key,
    get_openai_base_url,
    get_openai_model,
    get_openai_timeout_seconds,
)
from api.services.weather import SSL_CONTEXT

logger = logging.getLogger("api.assistant")

DISCLAIMER = {
    "en": (
        "This assistant provides general information only. For serious crop "
        "disease, pesticide or chemical decisions, please consult a qualified "
        "agricultural expert or local extension service."
    ),
    "te": (
        "ఈ సహాయకుడు సాధారణ సమాచారం మాత్రమే ఇస్తాడు. తీవ్రమైన పంట వ్యాధులు, "
        "పురుగు మందులు, రసాయనాల విషయాల్లో అర్హత కలిగిన వ్యవసాయ నిపుణుడిని "
        "లేదా స్థానిక వ్యవసాయ విస్తరణ అధికారిని సంప్రదించండి."
    ),
}

# Curated bilingual knowledge-base entries. Questions are normalised (lowercased,
# punctuation turned into spaces) and matched word-wise for ASCII keywords so
# synonyms/plurals can be listed safely; Telugu keys match as substrings so
# grammatical suffixes (e.g. పురుగులను for "pests") still hit. The topic with
# the most keyword hits wins; genuine non-matches keep the honest fallback.
_TOPICS = [
    {
        "keys": ["hello", "hi", "namaste", "namaskar", "greetings", "good morning",
                 "good evening"],
        "en": "Hello! Ask me anything about crops, soil, irrigation, fertilizers, "
              "cultivation, basic pest awareness or farming practices.",
        "te": "నమస్కారం! పంటలు, నేల, నీటిపారుదల, ఎరువులు, సాగు, తెగుళ్ల గురించి "
              "ఏదైనా అడగండి.",
    },
    {
        "keys": ["soil", "ph", "acidity", "alkaline", "manure", "compost", "composting",
                 "organic", "fertility", "fertile", "mulch", "mulching", "నేల", "కంపోస్ట్"],
        "en": "Soil health basics: most crops prefer slightly acidic to neutral soil "
              "(pH about 6–7.5). Add well-decomposed compost or farmyard manure to "
              "improve soil structure and moisture retention. Get a local soil test "
              "before applying fertiliser — it saves money and protects the land.",
        "te": "నేల ఆరోగ్యం: చాలా పంటలకు కొద్దిగా ఆమ్లం నుంచి తటస్థ నేల "
              "(pH 6–7.5) అనుకూలం. బాగా కుళ్లిన కంపోస్ట్ లేదా పశువుల ఎరువు "
              "వేస్తే నేల నాణ్యత, తేమ పెరుగుతాయి. ఎరువులు వేసే ముందు నేల "
              "పరీక్ష చేయించుకోండి.",
    },
    {
        "keys": ["irrigation", "irrigate", "irrigating", "water", "watering", "drip",
                 "sprinkler", "moisture", "canal", "borewell", "నీటిపారుదల", "పారుదల",
                 "నీరు", "నీళ్లు", "సేద్యం"],
        "en": "Irrigation tips: water early morning or late evening to reduce "
              "evaporation. Drip or sprinkler systems usually save water compared to "
              "flood irrigation. Check soil moisture a few cm below the surface "
              "before watering — most crops prefer evenly moist, not waterlogged, soil.",
        "te": "నీటిపారుదల సూచనలు: ఆవిరి తగ్గడానికి ఉదయం లేదా సాయంత్రం నీరు "
              "పెట్టండి. చిరుత పారుదల/స్ప్రింక్లర్ విధానాలు నీటిని ఆదా చేస్తాయి. "
              "నీరు పెట్టే ముందు కొన్ని సెంటీమీటర్ల లోతులో తేమ చూడండి.",
    },
    {
        "keys": ["fertilizer", "fertilizers", "fertiliser", "fertilisers", "urea", "npk",
                 "nutrient", "nutrients", "potash", "nitrogen", "phosphorus", "potassium",
                 "dap", "ఎరువు", "యూరియా"],
        "en": "Fertiliser basics: nitrogen (N) supports leaf growth, phosphorus (P) "
              "supports roots and grains, potassium (K) supports overall plant health. "
              "Apply based on a soil test and the crop's growth stage rather than a "
              "fixed schedule, and follow local extension guidance for rates.",
        "te": "ఎరువులు: నత్రజని (N) ఆకుల పెరుగుదలకు, భాస్వరం (P) వేర్లు, గింజలకు, "
              "పొటాష్ (K) మొక్క ఆరోగ్యానికి తోడ్పడతాయి. స్థిరమైన షెడ్యూల్ కంటే "
              "నేల పరీక్ష, పంట దశ ఆధారంగా వేయండి.",
    },
    {
        "keys": ["pest", "pests", "insect", "insects", "bug", "bugs", "disease",
                 "diseases", "fungus", "blight", "pesticide", "spray", "spraying",
                 "mites", "wilting", "wilt", "worm", "worms", "caterpillar", "aphid",
                 "aphids", "rust", "పురుగు", "తెగులు", "వ్యాధి"],
        "en": "Pest & disease awareness: inspect crops regularly, remove affected "
              "leaves or plants early, and keep the field clean. Identify the pest "
              "before spraying — many insects are harmless or beneficial. Please "
              "consult a qualified expert before using any pesticide or chemical.",
        "te": "తెగుళ్లు & వ్యాధులు: పంటలను క్రమం తప్పకుండా పరిశీలించి, దెబ్బతిన్న "
              "ఆకులు/మొక్కలను తొలగించండి. పురుగును గుర్తించకుండా పిచికారీ చేయవద్దు. "
              "పురుగు మందులు వాడే ముందు అర్హత కలిగిన నిపుణుడిని సంప్రదించండి.",
    },
    {
        "keys": ["weather", "rain", "rainfall", "raining", "climate", "season",
                 "monsoon", "heat", "drought", "flood", "storm", "temperature",
                 "వర్ష", "ఎండ", "వాతావరణ", "కరువు", "ఉష్ణోగ్రత"],
        "en": "Weather & farming: plan sowing around your local rainfall and "
              "temperature patterns. Check the Weather section of this app for current "
              "conditions when a weather provider is configured. During extreme heat "
              "or unseasonal rain, consider protective irrigation and delay field "
              "operations until conditions improve.",
        "te": "వాతావరణం & వ్యవసాయం: స్థానిక వర్షాలు, ఉష్ణోగ్రత ఆధారంగా విత్తన "
              "సమయం ప్లాన్ చేయండి. వాతావరణ సేవ కాన్ఫిగర్ చేసి ఉంటే ఈ యాప్‌లో "
              "వాతావరణ విభాగం చూడండి. తీవ్ర వేడికి లేదా అకాల వర్షానికి రక్షణ "
              "నీటిపారుదల గురించి ఆలోచించండి.",
    },
    {
        "keys": ["which crop", "what crop", "suggest a crop", "best crop", "best crops",
                 "crop to grow", "what to grow", "grow", "suitable crop", "which variety",
                 "best variety", "recommend", "recommendation", "recommendations",
                 "prediction", "predict", "ఏ పంట"],
        "en": "Use the Crop Prediction form on the home page: enter N, P, K, "
              "temperature, humidity, pH and rainfall, and the Random Forest model will "
              "suggest suitable crops with confidence values. The suggestion is a "
              "starting point — combine it with your local experience and market demand.",
        "te": "హోమ్ పేజీలోని పంట అంచనా ఫారం ఉపయోగించండి: N, P, K, ఉష్ణోగ్రత, తేమ, "
              "pH, వర్షపాతం నమోదు చేయండి — మోడల్ విశ్వాస విలువలతో సరైన పంటలను "
              "సూచిస్తుంది. ఇది ప్రారంభ సూచన — స్థానిక అనుభవం, మార్కెట్ డిమాండ్‌తో "
              "కలిపి చూడండి.",
    },
    {
        "keys": ["sow", "sowing", "sown", "planting", "plant", "plants", "seed", "seeds",
                 "seedling", "seedlings", "germination", "germinate", "nursery",
                 "transplant", "transplanting", "spacing", "when to grow", "crop rotation",
                 "rotation", "intercropping", "mixed cropping", "పైరు", "విత్తన",
                 "నాట", "మొలక"],
        "en": "Sowing basics: choose certified/quality seed, sow at the recommended "
              "time for your region, and maintain proper spacing for airflow. Keep the "
              "seedbed moist until germination. Local agricultural universities publish "
              "region-specific sowing calendars worth following.",
        "te": "విత్తనాలు: ధృవీకరించిన మంచి విత్తనాలు ఎంచుకోండి, మీ ప్రాంతానికి తగిన "
              "సమయంలో విత్తండి, గాలి ప్రవాహం కోసం సరైన దూరం పాటించండి. మొలకెత్తే "
              "వరకు నేల తేమగా ఉండేలా చూడండి.",
    },
    {
        "keys": ["harvest", "harvesting", "storage", "store", "post harvest", "postharvest",
                 "yield", "maturity", "threshing", "thresh", "drying", "కోత", "కోయ",
                 "దిగుబడి", "నిల్వ"],
        "en": "Harvest tips: harvest at the right maturity for best quality, handle "
              "produce gently, and dry grains/produce properly before storage to "
              "prevent spoilage. Keep stored produce dry, cool and away from pests.",
        "te": "కోత సూచనలు: మంచి నాణ్యత కోసం సరైన పక్వానికి చేరినప్పుడు కోయండి, "
              "పంటను జాగ్రత్తగా నిర్వహించండి, నిల్వ ముందు బియ్యం/పంటను బాగా "
              "ఆరబెట్టండి. నిల్వ ప్రదేశం పొడిగా, చల్లగా, తెగుళ్లు లేకుండా ఉంచండి.",
    },
    {
        "keys": ["how does", "model", "accuracy", "random forest", "mlflow", "dvc",
                 "machine learning", "ai"],
        "en": "How this app works: a Random Forest model (about 99.5% accuracy on the "
              "test set) is trained on 2,200 labelled soil/climate samples covering 22 "
              "crops. Experiments are tracked with MLflow and the dataset is versioned "
              "with DVC. Predictions are guidance — not a guarantee of yield.",
        "te": "ఈ యాప్ ఎలా పనిచేస్తుంది: 22 పంటల 2,200 నమూనాలపై Random Forest "
              "మోడల్ (పరీక్ష డేటాలో ~99.5% ఖచ్చితత్వం) శిక్షణ పొందింది. MLflowతో "
              "ప్రయోగాలు, DVCతో డేటా వెర్షనింగ్ జరుగుతాయి. అంచనాలు సూచన — దిగుబడి "
              "హామీ కాదు.",
    },
    {
        "keys": ["market", "markets", "price", "prices", "sell", "selling", "profit",
                 "scheme", "schemes", "subsidy", "subsidies", "loan", "loans", "mandi",
                 "మార్కెట్", "ధర", "అమ్మక", "పథక"],
        "en": "Market & schemes: check current prices at your nearest mandi or "
              "official agriculture market boards before selling. Government scheme and "
              "subsidy details change by state and season — please verify with your "
              "local agriculture department or extension officer.",
        "te": "మార్కెట్ & పథకాలు: అమ్మకానికి ముందు సమీపంలోని మండి లేదా అధికారిక "
              "వ్యవసాయ మార్కెట్ ధరలు చూడండి. ప్రభుత్వ పథకాలు, సబ్సిడీ వివరాలు "
              "రాష్ట్రాన్ని బట్టి మారతాయి — స్థానిక వ్యవసాయ శాఖను సంప్రదించండి.",
    },
    {
        "keys": ["greenhouse", "polyhouse", "shade net", "net house", "protected cultivation",
                 "గ్రీన్ హౌస్", "పాలీ హౌస్"],
        "en": "Greenhouse / polyhouse basics: protected cultivation controls climate "
              "(temperature, humidity) and reduces pest and weather damage — useful "
              "for high-value vegetables, flowers and herbs. Plan shade/net type, "
              "ventilation and drip irrigation for your crop and budget; a "
              "detailed project report from your district horticulture officer "
              "or a KVK helps before investing.",
        "te": "గ్రీన్ హౌస్ / పాలీ హౌస్: రక్షిత సాగులో ఉష్ణోగ్రత, తేమ నియంత్రణలో "
              "ఉంటాయి, తుఫాను, తెగుళ్ల నష్టం తగ్గుతుంది. విలువైన కూరగాయలు, "
              "పువ్వులకు అనుకూలం. పెట్టుబడికి ముందు జిల్లా హార్టికల్చర్ అధికారి "
              "లేదా KVK నుండి సమగ్ర నివేదిక తీసుకోండి.",
    },
    {
        "keys": ["organic farming", "organic farming", "bio pesticide", "biofertilizer",
                 "vermicompost", "sustainable", "సేంద్రియ", "సేంద్రీయ"],
        "en": "Organic & sustainable farming: build soil health with compost, "
              "vermicompost and green manures; rotate crops and use bio-pesticides "
              "where suitable. Conversion takes 2–3 years and certification matters "
              "for premium markets — discuss plans with your district organic "
              "farming body or KVK before switching fully.",
        "te": "సేంద్రీయ వ్యవసాయం: కంపోస్ట్, వర్మీకంపోస్ట్, పచ్చ ఎరువులతో నేల "
              "ఆరోగ్యం పెంచండి; పంట మార్పిడి చేయండి. మార్కెట్ ధరల కోసం ధృవీకరణ "
              "అవసరం — పూర్తిగా మారే ముందు జిల్లా సేంద్రీయ సంస్థ లేదా KVK తో "
              "చర్చించండి.",
    },
    {
        "keys": ["livestock", "dairy", "cattle", "cow", "buffalo", "goat", "poultry",
                 "chicken", "sheep", "fodder", "పశువు", "ఆవు", "మేక", "గొర్రె"],
        "en": "Livestock basics: balanced fodder, clean drinking water and routine "
              "vaccination are the foundation of dairy, sheep, goat and poultry "
              "work. For feed planning, breed advice or disease treatment, contact "
              "your local veterinary officer — dosages and medicines must come "
              "from a qualified veterinarian, not from general advice.",
        "te": "పశు సంవర్థకం: సమతుల్య మేత, శుభ్రమైన తాగునీరు, సకాలంలో టీకాలు "
              "పశువుల పెంపకానికి పునాది. మేత ప్రణాళిక, వ్యాధుల చికిత్సకు "
              "స్థానిక పశువైద్యుడిని సంప్రదించండి — మందుల వివరాలు వైద్యుడే "
              "ఇవ్వాలి.",
    },
    {
        "keys": ["tractor", "machinery", "machine", "plough", "plow", "harvester",
                 "thresher", "ట్రాక్టర్", "యంత్రం"],
        "en": "Farm machinery: match implement size to your acreage, soil and crop "
              "before buying or renting. Custom-hiring centres and FPOs often rent "
              "equipment at lower cost than purchasing — compare total cost per "
              "acre with a local dealer and other farmers first.",
        "te": "వ్యవసాయ యంత్రాలు: కొనే ముందు మీ విస్తీర్ణం, నేల, పంటకు తగిన "
              "పరికరం ఎంచుకోండి. కస్టమ్ హైరింగ్ కేంద్రాలు, FPOలు తక్కువ "
              "ఖర్చులో యంత్రాలు అద్దెకు ఇస్తాయి — బేరిట్ల ధర పోల్చండి.",
    },
]

_FALLBACK = {
    "en": "I don't have a specific answer for that yet. Try asking about: crops, "
          "soil, irrigation, fertilizers, sowing, pests, harvesting, weather or "
          "market guidance. You can also use the Crop Prediction form for a "
          "data-based crop suggestion.",
    "te": "దీనికి ప్రత్యేకమైన సమాధానం ఇంకా లేదు. ఇవి అడగవచ్చు: పంటలు, నేల, "
          "నీటిపారుదల, ఎరువులు, విత్తనాలు, తెగుళ్లు, కోత, వాతావరణం, మార్కెట్. "
          "డేటా ఆధారంగా పంట సూచన కోసం పంట అంచనా ఫారం కూడా ఉపయోగించవచ్చు.",
}


def _normalize_question(question: str) -> str:
    """Lowercase and turn punctuation into spaces, keeping unicode words intact.

    The Telugu block (U+0C00–U+0C7F) is preserved explicitly because Python's
    ``\\w`` excludes combining vowel signs (ు, ే, …), which would otherwise
    shatter Telugu words into single letters.
    """
    text = (question or "").lower()
    text = re.sub(r"[^\w\s\u0C00-\u0C7F]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _key_matches(key: str, padded: str, normalized: str) -> bool:
    """Whole-word match for ASCII keys; substring match for non-ASCII keys so
    agglutinative Telugu suffixes (e.g. పురుగులను) still hit their stem."""
    if f" {key} " in padded:
        return True
    if not key.isascii() and key in normalized:
        return True
    return False


def _find_answer(question: str) -> dict | None:
    normalized = _normalize_question(question)
    if not normalized:
        return None
    padded = f" {normalized} "
    best, best_score = None, 0
    for topic in _TOPICS:
        # Multi-word phrases are more specific than single words, so they weigh
        # more when topics tie (e.g. "when to grow" beats bare "grow").
        score = sum(
            (2 if " " in key else 1)
            for key in topic["keys"]
            if _key_matches(key, padded, normalized)
        )
        if score > best_score:
            best, best_score = topic, score
    if best is None or best_score == 0:
        return None
    return {"en": best["en"], "te": best["te"]}


class KnowledgeBaseProvider:
    """Built-in rule-based answers. Always available, no external service."""

    name = "knowledge_base"

    def answer(self, question: str, language: str = "en") -> dict:
        found = _find_answer(question)
        if found:
            return found
        return dict(_FALLBACK)


class OpenAIProvider:
    """OpenAI-compatible chat completions provider (server-side key only)."""

    name = "openai"

    SYSTEM_PROMPT = (
        "You are a helpful smart-farming assistant for rural farmers, used inside "
        "a crop recommendation app. Answer questions about crop selection, crop "
        "rotation, sowing, seeds, spacing, growth stages and harvesting; soil "
        "types, soil testing, pH, nutrient deficiencies, fertilizers, manure and "
        "compost; irrigation, drainage, water conservation, drought, floods, "
        "rainfall and heat stress; plant diseases, pest symptoms, prevention and "
        "treatment options; rice/paddy, cotton, chilli, maize, wheat, pulses, "
        "vegetables, fruits and other crops; greenhouse/polyhouse cultivation, "
        "horticulture, organic and sustainable farming; yield, farm expenses, "
        "storage, post-harvest losses and market guidance; basic livestock "
        "questions; farm machinery and management; and government agricultural "
        "schemes and subsidies. Style: clear, practical, farmer-friendly "
        "language; give short step-by-step guidance when useful. If key details "
        "are missing, ask for them (e.g. crop, location/district, acreage, soil "
        "type, crop growth stage, symptoms, recent weather) — one or two focused "
        "questions, then build on the answers using the conversation history. "
        "Safety and honesty rules: never invent exact fertilizer dosages, "
        "pesticide names or application rates — for pesticides and dosages, tell "
        "the farmer to follow the product's label and consult a local "
        "agricultural expert or extension officer. For possible plant diseases, "
        "explain the uncertainty, list likely causes, and ask for more symptoms "
        "or a photo rather than diagnosing with certainty. Never invent market "
        "prices, government-scheme eligibility or live weather; for anything "
        "that changes over time, clearly say the farmer must verify it with "
        "official current sources. Never guarantee a yield. Questions outside "
        "agriculture should be answered briefly and politely redirected to "
        "farming topics. Language rule: when the user requests Telugu (or mixes "
        "Telugu with English), answer in Telugu script; otherwise answer in English. If "
        "current weather observations are provided below, they are real readings "
        "just reported by the user's weather provider — they are NOT a forecast. "
        "You may relate your answer to those observations, but you must never "
        "predict future weather, claim certainty about coming conditions, or "
        "present weather alone as the basis for crop or irrigation decisions."
    )

    def answer(self, question: str, language: str = "en", weather: dict = None,
               history: list = None) -> dict | None:
        api_key = get_openai_api_key()
        if not api_key:
            return None
        system_prompt = self.SYSTEM_PROMPT
        if weather:
            # Optional, user-initiated live weather context (name + metrics only
            # — no coordinates). Hedged so it never becomes a guarantee.
            bits = []
            if weather.get("location"):
                bits.append(f"location: {weather['location']}")
            if weather.get("temperature") is not None:
                bits.append(f"temperature: {weather['temperature']}°C")
            if weather.get("humidity") is not None:
                bits.append(f"humidity: {weather['humidity']}%")
            if weather.get("condition"):
                bits.append(f"condition: {weather['condition']}")
            if weather.get("rainfall_mm") is not None:
                bits.append(f"rainfall in the last hour: {weather['rainfall_mm']} mm")
            if bits:
                system_prompt += (
                    " Current weather observations from the user's weather page: "
                    + "; ".join(bits)
                    + ". These are present readings, not a forecast — relate them "
                    "hedged and never as guaranteed outcomes or the sole basis for "
                    "crop or irrigation decisions."
                )
        messages = [{"role": "system", "content": system_prompt}]
        # Prior turns so follow-up questions keep their context (sanitised:
        # capped length, only known roles, never any credentials).
        for turn in (history or [])[-8:]:
            role = turn.get("role")
            text = (turn.get("text") or "").strip()
            if role in ("user", "assistant") and text:
                messages.append({"role": role, "content": text[:600]})
        messages.append({"role": "user", "content": question})
        payload = {
            "model": get_openai_model(),
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500,
        }
        request = urllib.request.Request(
            f"{get_openai_base_url()}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=get_openai_timeout_seconds(), context=SSL_CONTEXT
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"].strip()
            if not text:
                return None
            return {language: text}
        except urllib.error.HTTPError as exc:
            # Log only the status and the provider's credential-free body
            # snippet — never the request URL or headers, which carry the key.
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:
                detail = ""
            if exc.code in (401, 403):
                logger.warning(
                    "OpenAI provider rejected the configured key (HTTP %s): %s — "
                    "falling back to knowledge base",
                    exc.code,
                    detail or exc.reason,
                )
            elif exc.code == 429:
                logger.warning(
                    "OpenAI provider rate limit exceeded (HTTP 429) — "
                    "falling back to knowledge base"
                )
            else:
                logger.warning(
                    "OpenAI provider HTTP error %s: %s — falling back to knowledge base",
                    exc.code,
                    detail or exc,
                )
            return None
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            KeyError,
            IndexError,
            ValueError,
        ) as exc:
            # Log only the failure type/message — never the request (its headers
            # carry the API key).
            logger.warning(
                "OpenAI provider failed (%s), falling back to knowledge base",
                type(exc).__name__,
            )
            return None


def answer_question(question: str, language: str = "en", weather=None,
                    history=None) -> tuple[dict, str]:
    """Return ``(answer_text_by_language, provider_name)``.

    Uses the configured AI provider when available; silently degrades to the
    built-in knowledge base on any failure so the app never breaks. ``weather``
    is an optional live-weather hint and ``history`` optional prior conversation
    turns (pydantic models or plain dicts) supplied by the client.
    """
    question = (question or "").strip()
    weather_ctx = None
    if weather is not None:
        weather_ctx = (
            weather.model_dump(exclude_none=True)
            if hasattr(weather, "model_dump")
            else {k: v for k, v in dict(weather).items() if v is not None}
        )
        if not weather_ctx:
            weather_ctx = None
    history_ctx = []
    for turn in (history or [])[-8:]:
        if hasattr(turn, "model_dump"):
            turn = turn.model_dump()
        role = turn.get("role") if isinstance(turn, dict) else None
        text = (turn.get("text") if isinstance(turn, dict) else None) or ""
        if role in ("user", "assistant") and str(text).strip():
            history_ctx.append({"role": role, "text": str(text).strip()})
    if get_ai_provider() == "openai":
        result = OpenAIProvider().answer(question, language, weather_ctx, history_ctx)
        if result:
            return result, "openai"
    return KnowledgeBaseProvider().answer(question, language), "knowledge_base"
