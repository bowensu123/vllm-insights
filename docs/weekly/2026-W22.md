# vLLM weekly digest — 2026-05-26 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (182)

<details><summary>Click to expand the raw list</summary>

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
- [#43414](https://github.com/vllm-project/vllm/pull/43414) [Bugfix][Frontend] Fix input_audio parsing when uuid is present  — @ffggs → `nan`
- [#41669](https://github.com/vllm-project/vllm/pull/41669) [ROCm][CI] Remove benchmarks test group and shard long test groups — @AndreasKaratzas → `nan`
- [#39912](https://github.com/vllm-project/vllm/pull/39912) [Kernel] Batch invariant NVFP4 linear using cutlass — @jzakrzew → `nan`
- [#42143](https://github.com/vllm-project/vllm/pull/42143) fix(eagle3): read norm_before_fc from eagle_config for NVIDIA checkpoint — @FERRARIZHENG → `nan`
- [#43433](https://github.com/vllm-project/vllm/pull/43433) Keep scheduler alive for delayed KV connector frees — @lucifer1004 → `nan`
- [#42546](https://github.com/vllm-project/vllm/pull/42546) [ModelOpt] Support Qwen3.5/3.6 VLM quantized prefix mapping — @meenchen → `nan`
- [#42739](https://github.com/vllm-project/vllm/pull/42739) [Bugfix] Fix native Triton top-k/top-p kernel assumes contiguous logi… — @zhougit86 → `nan`
- [#43383](https://github.com/vllm-project/vllm/pull/43383) [Misc] Added missing return type annotations to improve mypy and IDE tooling — @taneem-ibrahim → `nan`
- [#43209](https://github.com/vllm-project/vllm/pull/43209) [7/n] Migrate pos_encoding and norm kernels to libtorch stable ABI (continued) — @cleonard530 → `nan`
- [#42915](https://github.com/vllm-project/vllm/pull/42915) [XPU] reudce host overhead of XPU MOE — @mayuyuace → `nan`
- [#42952](https://github.com/vllm-project/vllm/pull/42952) [XPU]feat: enable FP8 block-scaled quantization on XPU — @majian4work → `nan`
- [#41577](https://github.com/vllm-project/vllm/pull/41577) [ROCm][CI] Fix ROCm LoRA Transformers fallback with full CUDA graphs — @AndreasKaratzas → `nan`
- [#43051](https://github.com/vllm-project/vllm/pull/43051) [Bugfix] Auto-raise max_num_batched_tokens for prefix-LM multimodal models — @ashwing → `nan`
- [#43017](https://github.com/vllm-project/vllm/pull/43017) [ROCm][CI] Stabilize Granite tool-use and test URL construction — @AndreasKaratzas → `nan`
- [#43023](https://github.com/vllm-project/vllm/pull/43023) [ROCm][CI] Stabilize runner teardown between sampler tests — @AndreasKaratzas → `nan`
- [#42925](https://github.com/vllm-project/vllm/pull/42925) [DSV4] More multi-stream enablement for c4a — @zyongye → `nan`
- [#42922](https://github.com/vllm-project/vllm/pull/42922) Add `model` to `WeightTransferEngine.__init__` — @SumanthRH → `nan`
- [#38822](https://github.com/vllm-project/vllm/pull/38822) [Attention] Add head_dim=512 support for FlashInfer trtllm attention backend — @djmmoss → `nan`
- [#40881](https://github.com/vllm-project/vllm/pull/40881) elastic_ep: stage/commit MoE quant method on reconfigure — @itayalroy → `nan`
- [#42950](https://github.com/vllm-project/vllm/pull/42950) [XPU]fix: add XPU platform guards to DeepSeek-V4 ops — @majian4work → `nan`
- [#37374](https://github.com/vllm-project/vllm/pull/37374) [Perf] Optimize hidden state extraction logic — @benchislett → `nan`
- _…and 122 more_

</details>
