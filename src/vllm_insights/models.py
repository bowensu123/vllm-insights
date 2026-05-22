"""Vendor classification + vLLM tech profile for models mentioned in release notes.

Given a free-text string like "Llama 3.2 vision (#1234)" we figure out which
vendor it belongs to (Meta) and what Hugging Face org page best links to
the family. We also keep a curated tech profile per *focus* vendor
(vLLM architecture class names, modalities, key engine features) used by the
homepage to render a vLLM-compatibility view.

Focus vendors (the "Supported models" section foregrounds these and only these):
  - Alibaba (Qwen), DeepSeek, MiniMax, Zhipu (GLM)
  - Meta (Llama), Google (Gemma), Microsoft (Phi)   ← US top-3 open-source

Everything else is still classified, but collapsed into a single fallback group.
"""
import re
from urllib.parse import quote


# (regex on item text, vendor display name, HF org slug)
# Order matters: more specific patterns first.
VENDOR_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bllama", re.I),           "Meta",         "meta-llama"),
    (re.compile(r"\b(qwen|qwq)", re.I),      "Alibaba (Qwen)", "Qwen"),
    (re.compile(r"\bdeepseek", re.I),        "DeepSeek",     "deepseek-ai"),
    (re.compile(r"\b(mistral|mixtral|codestral|pixtral|magistral|devstral)", re.I),
                                             "Mistral AI",   "mistralai"),
    (re.compile(r"\bgemma", re.I),           "Google",       "google"),
    (re.compile(r"\bgemini", re.I),          "Google",       "google"),
    (re.compile(r"\b(phi-?\d|phimoe)", re.I), "Microsoft",   "microsoft"),
    (re.compile(r"\byi[- ]", re.I),          "01.AI",        "01-ai"),
    (re.compile(r"\bbaichuan", re.I),        "Baichuan",     "baichuan-inc"),
    (re.compile(r"\b(chatglm|glm-?\d)", re.I), "Zhipu (GLM)", "zai-org"),
    (re.compile(r"\binternlm", re.I),        "Shanghai AI Lab (InternLM)", "internlm"),
    (re.compile(r"\bminimax", re.I),         "MiniMax",      "MiniMaxAI"),
    (re.compile(r"\b(stablelm|stable[- ]diffusion|sdxl)\b", re.I), "Stability AI", "stabilityai"),
    (re.compile(r"\bfalcon\b", re.I),        "TII (Falcon)", "tiiuae"),
    (re.compile(r"\b(command[- ]?r|c4ai|aya)\b", re.I), "Cohere", "CohereForAI"),
    (re.compile(r"\bgranite\b", re.I),       "IBM",          "ibm-granite"),
    (re.compile(r"\bnemotron\b", re.I),      "NVIDIA",       "nvidia"),
    (re.compile(r"\b(olmo|molmo)\b", re.I),  "AllenAI",      "allenai"),
    (re.compile(r"\bsmaug\b", re.I),         "Abacus AI",    "abacusai"),
    (re.compile(r"\bdbrx\b", re.I),          "Databricks",   "databricks"),
    (re.compile(r"\bjamba\b", re.I),         "AI21 Labs",    "ai21labs"),
    (re.compile(r"\b(starcoder|starchat|bigcode)\b", re.I), "BigCode",      "bigcode"),
    (re.compile(r"\b(deci(?:lm|coder)?)\b", re.I), "Deci AI",      "Deci"),
    (re.compile(r"\b(grok)\b", re.I),        "xAI",          "xai-org"),
    (re.compile(r"\b(kimi)\b", re.I),        "Moonshot AI",  "moonshotai"),
    (re.compile(r"\b(hunyuan)\b", re.I),     "Tencent",      "tencent"),
    (re.compile(r"\b(ernie)\b", re.I),       "Baidu",        "baidu"),
    (re.compile(r"\b(seed[- ]?oss|seedoss|dou[bw]ao)\b", re.I), "ByteDance",    "ByteDance-Seed"),
    (re.compile(r"\b(whisper)\b", re.I),     "OpenAI",       "openai"),
]


def classify(item_text: str) -> tuple[str, str] | None:
    """Return (vendor_display, hf_org_slug) or None if no rule matched."""
    for pat, vendor, org in VENDOR_RULES:
        if pat.search(item_text):
            return vendor, org
    return None


def hf_org_url(org_slug: str) -> str:
    return f"https://huggingface.co/{org_slug}"


def hf_search_url(query: str) -> str:
    return "https://huggingface.co/models?search=" + quote(query)


def looks_like_model_section(section_name: str) -> bool:
    s = section_name.lower()
    # Match "Models", "New Models", "Model Support", "Models Supported",
    # "New model support", but NOT generic "Highlights" or unrelated bullets.
    return ("model" in s) and any(
        kw in s for kw in ("model", "support", "added", "new")
    )


# -----------------------------------------------------------------------------
# Focus vendors and their vLLM tech profile
# -----------------------------------------------------------------------------
# Ordered list of the vendors we foreground on the homepage. The four leading
# entries are the Chinese open-weight labs the project is tracking closely; the
# three trailing entries are the US top-3 open-source families. Edit here to
# change which vendors get the rich tech card treatment.
FOCUS_VENDORS: list[str] = [
    "Alibaba (Qwen)",
    "DeepSeek",
    "MiniMax",
    "Zhipu (GLM)",
    "Meta",
    "Google",
    "Microsoft",
]


# Per-vendor metadata. We used to keep curated taglines, feature lists and
# series here — that was opinion masquerading as fact. The only field we
# still allow is `hf_org`, because the HF org page is the canonical home for
# the vendor's weights and there's nothing to make up. Everything else (arch
# count, modalities, recent activity) is now derived in build_site.py from
# the live registry + PR cache.
VENDOR_META: dict[str, dict] = {
    "Alibaba (Qwen)":   {"hf_org": "Qwen"},
    "DeepSeek":         {"hf_org": "deepseek-ai"},
    "MiniMax":          {"hf_org": "MiniMaxAI"},
    "Zhipu (GLM)":      {"hf_org": "zai-org"},
    "Meta":             {"hf_org": "meta-llama"},
    "Google":           {"hf_org": "google"},
    "Microsoft":        {"hf_org": "microsoft"},
}


def is_focus_vendor(vendor: str) -> bool:
    return vendor in VENDOR_META


def vendor_meta(vendor: str) -> dict | None:
    return VENDOR_META.get(vendor)


# Old name kept as an alias so external callers don't break during the
# rollout. New code should use `vendor_meta`.
def vendor_tech(vendor: str) -> dict | None:  # pragma: no cover - thin shim
    return vendor_meta(vendor)


_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

# Architecture class names that the CamelCase-split heuristic can't classify
# because the vendor name is glued to or split across other tokens (e.g.
# `Mllama` has no word boundary before "llama"; `MiniMax` splits into two
# tokens). Keep this list tight — prefer extending the regex rules in
# VENDOR_RULES when a generic pattern is possible.
_ARCH_VENDOR_OVERRIDES: dict[str, str] = {
    "Mllama": "Meta",
    "MiniMax": "MiniMax",
}


def classify_arch(arch_class: str) -> tuple[str, str] | None:
    """Classify a vLLM architecture class name (e.g. 'Qwen3MoeForCausalLM') back
    to its vendor. We try several normalisations because CamelCase split alone
    misses cases like `Mllama*` (no boundary before "llama") and `MiniMax*`
    (vendor name straddles a capital-letter boundary)."""
    forms = [
        _CAMEL_SPLIT_RE.sub(" ", arch_class),       # 'Qwen 3 Moe For Causal LM'
        arch_class,                                  # 'Qwen3MoeForCausalLM'
        arch_class.lower(),                          # 'qwen3moeforcausallm'
    ]
    for form in forms:
        hit = classify(form)
        if hit:
            return hit
    # Hard-coded overrides for class names that don't carry the vendor
    # spelling we match on.
    for needle, vendor in _ARCH_VENDOR_OVERRIDES.items():
        if arch_class.startswith(needle):
            tech = VENDOR_TECH.get(vendor)
            if tech is None:
                # Best-effort HF org slug from the rule table
                for _pat, vname, oslug in VENDOR_RULES:
                    if vname == vendor:
                        return vendor, oslug
                return vendor, ""
            for _pat, vname, oslug in VENDOR_RULES:
                if vname == vendor:
                    return vendor, oslug
            return vendor, ""
    return None
