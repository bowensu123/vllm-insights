# vLLM weekly digest — 2026-05-27 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (186)

<details><summary>Click to expand the raw list</summary>

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
- [#43032](https://github.com/vllm-project/vllm/pull/43032) [CPU] Enable non-divisible GQA for decode workitems in mixed batches — @zhejiangxiaomai → `nan`
- [#43273](https://github.com/vllm-project/vllm/pull/43273) [GDN] GDN Prefill kernel for SM100 — @gau-nernst → `nan`
- [#43579](https://github.com/vllm-project/vllm/pull/43579) [Bugfix][Model] Fix GPT2ForSequenceClassification sub-module prefix — @QingZhou-YangHY → `nan`
- [#43553](https://github.com/vllm-project/vllm/pull/43553) [Frontend] Split the offline inference APIs and utils. — @noooop → `nan`
- [#43194](https://github.com/vllm-project/vllm/pull/43194) [Bugfix] fix device mismatch in MiniCPM-o-4_5 resampler — @yma11 → `nan`
- [#42788](https://github.com/vllm-project/vllm/pull/42788) [KV Connector] Propagate MooncakeStore load failures — @Dao007forever → `nan`
- [#43516](https://github.com/vllm-project/vllm/pull/43516) [KV Connector][Bugfix] MooncakeStore: don't double-apply Eagle prune in load_mask — @Dao007forever → `nan`
- [#43632](https://github.com/vllm-project/vllm/pull/43632) [DeepSeek V4] Move MegaMoE input prep kernel to nvidia/ops — @WoosukKwon → `nan`
- [#42290](https://github.com/vllm-project/vllm/pull/42290) [LoRA] Add one shot triton kernel For MoE LoRA — @jeejeelee → `nan`
- [#43028](https://github.com/vllm-project/vllm/pull/43028) [XPU] Ensure RNG offset alignment with PyTorch requirements in XPU sampler — @chaojun-zhang → `nan`
- [#43554](https://github.com/vllm-project/vllm/pull/43554) [Kernel] Remove NormGateLinear — @jeejeelee → `nan`
- [#43583](https://github.com/vllm-project/vllm/pull/43583) [Misc] Print accuracy value for PD tests even on success  — @NickLucche → `nan`
- [#43281](https://github.com/vllm-project/vllm/pull/43281) [KV Connector] Handle Mooncake finish after preemption — @zhewenl → `nan`
- [#42933](https://github.com/vllm-project/vllm/pull/42933) Reduce memory usage for granite_speech. — @Yihuki → `nan`
- [#43568](https://github.com/vllm-project/vllm/pull/43568) [Doc] Add section on escalating stalled contributions — @esmeetu → `nan`
- _…and 126 more_

</details>
