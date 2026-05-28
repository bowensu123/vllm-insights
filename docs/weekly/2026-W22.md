# vLLM weekly digest — 2026-05-28 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (189)

<details><summary>Click to expand the raw list</summary>

- [#43464](https://github.com/vllm-project/vllm/pull/43464) Fix RunAI streamer tensor buffer reuse during weight loading — @bbartels → `nan`
- [#43469](https://github.com/vllm-project/vllm/pull/43469) [Rust Frontend] Introduce mock engine for benchmark baseline — @BugenZhao → `nan`
- [#38831](https://github.com/vllm-project/vllm/pull/38831) [ModelRunnerV2][Hybrid model] Support kernel block size in hybrid model — @MengqingCao → `nan`
- [#43599](https://github.com/vllm-project/vllm/pull/43599) [Bugfix][Kernel] TRTLLM NVFP4 MoE chunking — @amitz-nv → `nan`
- [#43740](https://github.com/vllm-project/vllm/pull/43740) Add @AndreasKaratzas to CODEOWNERS — @AndreasKaratzas → `nan`
- [#43617](https://github.com/vllm-project/vllm/pull/43617) Fix Qwen3-VL and Qwen3-omni-thinker accuracy degradation from deepstack inputs under torch.compile — @andakai → `nan`
- [#43733](https://github.com/vllm-project/vllm/pull/43733) [Bugfix][DFlash]allocate the proper number of lookahead slots — @benchislett → `nan`
- [#43794](https://github.com/vllm-project/vllm/pull/43794) Validate against some config fields being set to 0 — @hmellor → `nan`
- [#43785](https://github.com/vllm-project/vllm/pull/43785) Remove Transformers forward/backward compatibility tests — @hmellor → `nan`
- [#43540](https://github.com/vllm-project/vllm/pull/43540) [Quantization] Fix Humming RoutedExperts import — @fallintoplace → `nan`
- [#43361](https://github.com/vllm-project/vllm/pull/43361) [8/n] Migrate merge_attn_states, mamba, sampler to torch stable ABI (continued) — @cleonard530 → `nan`
- [#41751](https://github.com/vllm-project/vllm/pull/41751) [ROCm] mori: add InterNodeV1LL inter-node kernel selection via VLLM_MORI_INTERNODE_KERNEL — @jatseng-ai → `nan`
- [#43791](https://github.com/vllm-project/vllm/pull/43791) Fix early CUDA init — @hmellor → `nan`
- [#43546](https://github.com/vllm-project/vllm/pull/43546) [Docs] Fix the duplicate doc icon issue — @chunyang-wen → `nan`
- [#39155](https://github.com/vllm-project/vllm/pull/39155) [BugFix] HFValidationError with cloud storage URIs when HF_HUB_OFFLINE=1 — @sts07142 → `nan`
- [#43745](https://github.com/vllm-project/vllm/pull/43745) [misc] Bump cutedsl version to 4.5.2 — @zyongye → `nan`
- [#43401](https://github.com/vllm-project/vllm/pull/43401) [Bugfix] Map reasoning_effort to enable_thinking in chat template kwargs — @ashwing → `nan`
- [#43731](https://github.com/vllm-project/vllm/pull/43731) [Kernel] Enable TritonW4A16LinearKernel as CUDA fallback for non-Marlin-aligned W4A16 shapes — @lucianommartins → `nan`
- [#43697](https://github.com/vllm-project/vllm/pull/43697) [Docs] Fix MLA prefill backend default docs — @mmangkad → `nan`
- [#43662](https://github.com/vllm-project/vllm/pull/43662) [Rust Frontend] Align tool parser fallback behavior between streaming & non-streaming paths — @BugenZhao → `nan`
- [#43550](https://github.com/vllm-project/vllm/pull/43550) [Doc] Add Ascend NPU tab to the quickstart installation guide — @adityasingh2400 → `nan`
- [#42833](https://github.com/vllm-project/vllm/pull/42833) [ROCm][GPT-OSS] Avoid repeated compile-time `cos_sin_cache.to(bf16)` casts in rotary path — @akii96 → `nan`
- [#43175](https://github.com/vllm-project/vllm/pull/43175) [Frontend] Add MiniCPM5 XML tool call parser — @zhangtao2-1 → `nan`
- [#43719](https://github.com/vllm-project/vllm/pull/43719) [MRV2][BugFix] Fix KV connector handling in spec decode case — @njhill → `nan`
- [#39177](https://github.com/vllm-project/vllm/pull/39177) [ROCm][Perf] Expose AITER MoE sorting dispatch policy via env var — @nholmber → `nan`
- [#42694](https://github.com/vllm-project/vllm/pull/42694) [KVConnector][Mooncake] Wire reset_cache cascade end-to-end — @aoshen02 → `nan`
- [#43695](https://github.com/vllm-project/vllm/pull/43695) Fix test_aot_compile for torch 2.12 — @angelayi → `nan`
- [#43710](https://github.com/vllm-project/vllm/pull/43710) [DSv4] Refactor compressor & Fix ROCm compatibility — @WoosukKwon → `nan`
- [#43358](https://github.com/vllm-project/vllm/pull/43358) [Deprecation] Deprecate functions as scheduled for v0.21.0 — @yewentao256 → `nan`
- [#43325](https://github.com/vllm-project/vllm/pull/43325) [MLA][Attention] Add OOT MLA prefill backend registration mechanism — @MatthewBonanni → `nan`
- [#42095](https://github.com/vllm-project/vllm/pull/42095) [Attention] Make FlexAttention and FlashAttention use num-blocks first layouts — @LucasWilkinson → `nan`
- [#43677](https://github.com/vllm-project/vllm/pull/43677) [Perf] Optimize Fp8BlockScaledMMLinearKernel input_scale tensor using new_empty() — @xyang16 → `nan`
- [#43647](https://github.com/vllm-project/vllm/pull/43647) [ROCm][CI] Fix ROCm multimodal Qwen2.5-VL activation compile and Phi4MM ragged image mask handling — @AndreasKaratzas → `nan`
- [#43582](https://github.com/vllm-project/vllm/pull/43582) [Rust Frontend] Add reasoning/tool parser & renderer roundtrip tests — @BugenZhao → `nan`
- [#43543](https://github.com/vllm-project/vllm/pull/43543) [Bugfix] Split attention groups by num_heads_q for spec-decode drafts — @lucianommartins → `nan`
- [#41303](https://github.com/vllm-project/vllm/pull/41303) [ci] Add arm64 ci image — @khluu → `nan`
- [#42585](https://github.com/vllm-project/vllm/pull/42585) [Bugfix][V1] Fix TOCTOU race causing intermittent `EADDRINUSE` on multi-API-server DP startup — @vadiklyutiy → `nan`
- [#43627](https://github.com/vllm-project/vllm/pull/43627) [KV Connector] MooncakeStore: drop dead discard_partial_chunks parameter — @zhewenl → `nan`
- [#43410](https://github.com/vllm-project/vllm/pull/43410) [Kernel] Porting  fuse_minimax_qk_norm  to manual fusion — @jeejeelee → `nan`
- [#43709](https://github.com/vllm-project/vllm/pull/43709) [CI] Soft-fail AMD entrypoints mirror tests — @khluu → `nan`
- [#43690](https://github.com/vllm-project/vllm/pull/43690) [DSv4] Drop _get_compressed_kv_buffer in DeepseekCompressor — @WoosukKwon → `nan`
- [#43635](https://github.com/vllm-project/vllm/pull/43635) [Doc] Add line limit to AGENTS.md — @WoosukKwon → `nan`
- [#42124](https://github.com/vllm-project/vllm/pull/42124) Add LM head quantization support for ModelOpt — @meenchen → `nan`
- [#43629](https://github.com/vllm-project/vllm/pull/43629) [ROCm] Remove MegaMoE integration in deepseek v4 — @WoosukKwon → `nan`
- [#42789](https://github.com/vllm-project/vllm/pull/42789) [MoE Refactor] W4a8 int8 oracle — @bnellnm → `nan`
- [#42768](https://github.com/vllm-project/vllm/pull/42768) [MoE Refactor] Migrate ModelOptMxFp8FusedMoE to oracle — @bnellnm → `nan`
- [#43162](https://github.com/vllm-project/vllm/pull/43162) [Feat][DSV4] Fuse q pad into deepseek v4 fused kernel — @zyongye → `nan`
- [#40990](https://github.com/vllm-project/vllm/pull/40990) [ROCm][CI] Extend ROCm quick reduce coverage — @AndreasKaratzas → `nan`
- [#43603](https://github.com/vllm-project/vllm/pull/43603) [Docs][ROCm] MoRI-IO Connector Usage Guide — @simondanielsson → `nan`
- [#43530](https://github.com/vllm-project/vllm/pull/43530) Fix CuPy runtime deps and restore humming — @mmangkad → `nan`
- [#43646](https://github.com/vllm-project/vllm/pull/43646) [XPU] Fix fused MoE LoRA kernel crash on XPU by using platform-agnos num_compute_units — @chaojun-zhang → `nan`
- [#38278](https://github.com/vllm-project/vllm/pull/38278) [Model] Use AutoWeightsLoader for InternLM2 — @javierdejesusda → `nan`
- [#43402](https://github.com/vllm-project/vllm/pull/43402) [Reasoning] [Bugfix] Reject invalid thinking_token_budget values — @linzm1007 → `nan`
- [#43636](https://github.com/vllm-project/vllm/pull/43636) [Misc] Support interleaved custom image benchmark datasets — @ThibaultCastells → `nan`
- [#43303](https://github.com/vllm-project/vllm/pull/43303) [Misc][Refactor][ROCm] Convert MoRI-related envvars to extra config args — @simondanielsson → `nan`
- [#41847](https://github.com/vllm-project/vllm/pull/41847) [KV Transfer] Enable HMA by default for connectors that support it — @chfeng-cs → `nan`
- [#43482](https://github.com/vllm-project/vllm/pull/43482) [Bugfix] Apply fc_norm in Eagle3DeepseekV2 combine_hidden_states — @yubofredwang → `nan`
- [#43045](https://github.com/vllm-project/vllm/pull/43045) [chores][log] change registry log from `warning` to `debug` — @ILikeIneine → `nan`
- [#43584](https://github.com/vllm-project/vllm/pull/43584) Add CuTe DSL sparse compressor support — @Jie-Fang → `nan`
- [#43394](https://github.com/vllm-project/vllm/pull/43394) Upgrade tpu-inference to v0.20.0 — @CienetStingLin → `nan`
- _…and 129 more_

</details>
