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


# Per-vendor tech profile. Field semantics:
#   tagline   — one-line "why this matters for vLLM"
#   archs     — vLLM model-registry class names users actually pass to --model
#               (or that get auto-selected from HF config.architectures).
#   modal     — modalities exposed via vLLM (text / vision / audio / omni)
#   features  — engine/kernel/quantization features that light up for this family
#   series    — notable model lines under this vendor, for orientation
VENDOR_TECH: dict[str, dict] = {
    "Alibaba (Qwen)": {
        "tagline": "Largest officially-supported family in vLLM; reference for MoE expert "
                   "parallel + multi-modal pipelines.",
        "archs": [
            "Qwen2ForCausalLM", "Qwen3ForCausalLM",
            "Qwen2MoeForCausalLM", "Qwen3MoeForCausalLM",
            "Qwen2VLForConditionalGeneration", "Qwen2_5_VLForConditionalGeneration",
            "Qwen3VLForConditionalGeneration",
            "Qwen2AudioForConditionalGeneration",
            "Qwen3OmniMoeForConditionalGeneration",
        ],
        "modal": ["text", "vision", "audio", "omni"],
        "features": [
            "FP8", "AWQ", "GPTQ", "BnB", "GGUF",
            "MoE + Expert Parallel", "FlashAttention-3",
            "Speculative decoding", "LoRA", "Tool calling",
            "YaRN / Dual-Chunk long context (≥1M)",
        ],
        "series": ["Qwen3", "Qwen3-VL", "Qwen3-Omni", "Qwen2.5-VL", "QwQ"],
    },
    "DeepSeek": {
        "tagline": "Flagship MoE workload — drives vLLM's MLA backend, DeepEP integration "
                   "and MTP speculative decoding.",
        "archs": [
            "DeepseekV2ForCausalLM", "DeepseekV3ForCausalLM",
            "DeepseekVLV2ForConditionalGeneration",
        ],
        "modal": ["text", "vision"],
        "features": [
            "MLA (Multi-head Latent Attention)",
            "MoE + Expert Parallel (DeepEP)",
            "FP8 block-wise quant",
            "MTP speculative decoding",
            "PD disaggregation",
            "Long context",
        ],
        "series": ["DeepSeek-V3.2", "DeepSeek-V3", "DeepSeek-R1", "DeepSeek-VL2"],
    },
    "MiniMax": {
        "tagline": "First production linear-attention hybrid in vLLM; long-context (1M+) "
                   "MoE workhorse.",
        "archs": [
            "MiniMaxText01ForCausalLM",
            "MiniMaxM1ForCausalLM",
        ],
        "modal": ["text"],
        "features": [
            "Lightning Attention (linear/hybrid)",
            "MoE",
            "FP8",
            "Ultra-long context (1M+)",
        ],
        "series": ["MiniMax-Text-01", "MiniMax-M1", "MiniMax-M2"],
    },
    "Zhipu (GLM)": {
        "tagline": "Multi-generation coverage from ChatGLM through GLM-4.x, including text "
                   "and vision MoE variants.",
        "archs": [
            "ChatGLMForCausalLM",
            "GlmForCausalLM", "Glm4ForCausalLM",
            "Glm4MoeForCausalLM",
            "Glm4vForConditionalGeneration", "Glm4vMoeForConditionalGeneration",
        ],
        "modal": ["text", "vision"],
        "features": [
            "MoE", "FP8", "AWQ", "GPTQ",
            "FlashAttention", "LoRA", "Long context",
        ],
        "series": ["GLM-4.6", "GLM-4.5", "GLM-4.5V", "ChatGLM3"],
    },
    "Meta": {
        "tagline": "Reference architecture for vLLM — almost every kernel and scheduler "
                   "optimisation lands here first.",
        "archs": [
            "LlamaForCausalLM",
            "MllamaForConditionalGeneration",
            "Llama4ForConditionalGeneration",
        ],
        "modal": ["text", "vision"],
        "features": [
            "FlashAttention-3", "FP8", "AWQ", "GPTQ", "BnB", "GGUF",
            "Chunked Prefill", "Prefix Caching",
            "Speculative decoding (EAGLE, Medusa, MTP)",
            "LoRA", "TP / PP / EP (Llama 4)",
        ],
        "series": ["Llama 4", "Llama 3.3", "Llama 3.2-Vision", "Code Llama"],
    },
    "Google": {
        "tagline": "Drives vLLM's sliding-window + global hybrid attention path; PaliGemma "
                   "is the reference encoder-decoder VLM.",
        "archs": [
            "GemmaForCausalLM", "Gemma2ForCausalLM", "Gemma3ForCausalLM",
            "Gemma3ForConditionalGeneration",
            "PaliGemmaForConditionalGeneration",
        ],
        "modal": ["text", "vision"],
        "features": [
            "FP8", "AWQ", "BnB",
            "FlashAttention", "Sliding-window attention",
            "Long context", "LoRA",
        ],
        "series": ["Gemma 3", "Gemma 2", "PaliGemma 2"],
    },
    "Microsoft": {
        "tagline": "Phi-4-Multimodal is vLLM's first text + vision + audio omnimodal "
                   "endpoint; Phi-MoE pushes small-MoE serving.",
        "archs": [
            "PhiForCausalLM", "Phi3ForCausalLM", "Phi3SmallForCausalLM",
            "PhiMoEForCausalLM",
            "Phi4MMForCausalLM",
        ],
        "modal": ["text", "vision", "audio"],
        "features": [
            "FP8", "AWQ", "GPTQ", "LoRA",
            "MoE", "Long context",
        ],
        "series": ["Phi-4", "Phi-4-Multimodal", "Phi-3.5-MoE", "Phi-3"],
    },
}


def is_focus_vendor(vendor: str) -> bool:
    return vendor in VENDOR_TECH


def vendor_tech(vendor: str) -> dict | None:
    return VENDOR_TECH.get(vendor)
