# vLLM weekly digest — 2026-05-26 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (190)

<details><summary>Click to expand the raw list</summary>

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
- [#42296](https://github.com/vllm-project/vllm/pull/42296) [Feat][KVConnector] Support DSV4 in SimpleCPUOffloadBackend — @ivanium → `nan`
- [#40275](https://github.com/vllm-project/vllm/pull/40275) [Docker] Non-root support for vllm-openai; add opt-in vllm-openai-nonroot target — @TheDuyIT → `nan`
- [#43552](https://github.com/vllm-project/vllm/pull/43552) [Docs] Reorganize offline inference docs.  — @noooop → `nan`
- [#42373](https://github.com/vllm-project/vllm/pull/42373) fix: MoE model using shared routed experts crashes on AMD GPUs — @weizhoublue → `nan`
- [#43474](https://github.com/vllm-project/vllm/pull/43474) [Kernel] Add mhc_pre_big_fuse_with_norm_tilelang  — @jeejeelee → `nan`
- [#41735](https://github.com/vllm-project/vllm/pull/41735) File system secondary tier implemented in python — @rshavitt → `nan`
- [#43083](https://github.com/vllm-project/vllm/pull/43083) Tuning script and configs for Triton Mamba SSU kernel — @danisereb → `nan`
- [#43385](https://github.com/vllm-project/vllm/pull/43385) [ROCm] [DSv4] [Perf] Support DeepSeek v4 MTP — @tjtanaa → `nan`
- [#43016](https://github.com/vllm-project/vllm/pull/43016) [ROCm][CI] Stabilize 400 error return code for invalid schema inputs — @AndreasKaratzas → `nan`
- [#43142](https://github.com/vllm-project/vllm/pull/43142) [kv_offload]: Add DSv4 support — @orozery → `nan`
- [#43494](https://github.com/vllm-project/vllm/pull/43494) [KV Connector] Keep MooncakeStore full hits block-aligned — @Dao007forever → `nan`
- [#43233](https://github.com/vllm-project/vllm/pull/43233) [Model Runner v2] Force v1 runner for tests — @yewentao256 → `nan`
- [#42691](https://github.com/vllm-project/vllm/pull/42691) [Bugfix] Fix reasoning dropped on streaming boundary deltas — @sfeng33 → `nan`
- [#43492](https://github.com/vllm-project/vllm/pull/43492) Revert "[Misc] add humming to dependencies" — @mgoin → `nan`
- [#43486](https://github.com/vllm-project/vllm/pull/43486) [ROCm][Critical] Fix the GDN import bug — @tjtanaa → `nan`
- [#43392](https://github.com/vllm-project/vllm/pull/43392) [Mooncake] Add metrics for MooncakeStoreConnector operations — @Dao007forever → `nan`
- [#42680](https://github.com/vllm-project/vllm/pull/42680) [MoE] Migrate W4A8 CT to oracle kernel setup — @bedeks → `nan`
- [#43489](https://github.com/vllm-project/vllm/pull/43489) [Docs] Fix stale version number in token_classify.md — @fuergaosi233 → `nan`
- [#43488](https://github.com/vllm-project/vllm/pull/43488) [Docs] Fix stale version number in token_embed.md — @fuergaosi233 → `nan`
- [#42787](https://github.com/vllm-project/vllm/pull/42787) [MM] Enable FlashInfer metadata support for Qwen2.5-VL vision attention — @huanghua1994 → `nan`
- _…and 130 more_

</details>
