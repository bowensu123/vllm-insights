"""Vendor classification for model names mentioned in release notes.

Given a free-text string like "Llama 3.2 vision (#1234)" we try to figure out
which vendor it belongs to (Meta) and what Hugging Face org page best links to
the family. Falls back to a HF full-text search if no rule matches.
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
