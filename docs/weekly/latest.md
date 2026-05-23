# vLLM weekly digest — 2026-05-23 (W21)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (224)

<details><summary>Click to expand the raw list</summary>

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
- [#42353](https://github.com/vllm-project/vllm/pull/42353) DSv4 fused Q-norm kernel grid refactor — @gnovack → `nan`
- [#35045](https://github.com/vllm-project/vllm/pull/35045) [Model Runner V2] Support sharing kv cache layers — @njhill → `nan`
- [#42566](https://github.com/vllm-project/vllm/pull/42566) [Quantization][ModelOpt] W4A16 NVFP4 fused MoE + mixed-precision dispatch — @juhi10071998 → `nan`
- [#43437](https://github.com/vllm-project/vllm/pull/43437) mhc_post - remove sts & add vectorized copies — @gnovack → `nan`
- [#36854](https://github.com/vllm-project/vllm/pull/36854) [Bugfix] Clear error message for FP8 torchao quantization on unsupported GPUs — @haosdent → `nan`
- [#43427](https://github.com/vllm-project/vllm/pull/43427) [Bugfix] Detect wrong libcute_dsl_runtime.so variant in FlashInfer GDN — @arpera → `nan`
- [#40733](https://github.com/vllm-project/vllm/pull/40733) [RFC][EPLB][#32028] Remove dead torch.accelerator.synchronize() from sync path — @SandishKumarHN → `nan`
- [#43426](https://github.com/vllm-project/vllm/pull/43426) [Frontend] Simplify AuthenticationMiddleware path extraction — @russellb → `nan`
- [#43149](https://github.com/vllm-project/vllm/pull/43149) [Refactor] Extract DeepSeek V4 sparse MLA impl into model folder — @zyongye → `nan`
- [#43371](https://github.com/vllm-project/vllm/pull/43371) [KV Connector] MooncakeStore: don't co-queue save with load to avoid double delayed-free — @Dao007forever → `nan`
- [#42650](https://github.com/vllm-project/vllm/pull/42650) [Bugfix] Source num_qo_heads from Attention layers in Flashinfer/Triton metadata builders — @zhandaz → `nan`
- [#43405](https://github.com/vllm-project/vllm/pull/43405) [Rust Frontend] [Refactor] Extract a newtype for utility call ID — @BugenZhao → `nan`
- [#41234](https://github.com/vllm-project/vllm/pull/41234) [Multimodal] Simplify ViT CUDA graph interfaces — @Isotr0py → `nan`
- [#42209](https://github.com/vllm-project/vllm/pull/42209) Add NVFP4 MOE support for Deepseek V4. — @sychen52 → `nan`
- [#43329](https://github.com/vllm-project/vllm/pull/43329) [CI] Fix AMD docker build tests — @haosdent → `nan`
- [#43110](https://github.com/vllm-project/vllm/pull/43110) [EPLB] Change default EPLB communicator — @ilmarkov → `nan`
- [#42737](https://github.com/vllm-project/vllm/pull/42737) [LoRA] Reduce memory of 2D weights when EP is set — @jeejeelee → `nan`
- [#43118](https://github.com/vllm-project/vllm/pull/43118) [BugFix] wire make_empty_intermediate_tensors on AyaVision and Voxtral — @JasonKeyiL → `nan`
- [#43001](https://github.com/vllm-project/vllm/pull/43001) [Bugfix] Clear P0 mm sender cache on sleep/pause to fix mm_hash desync — @wasnertobias → `nan`
- [#43286](https://github.com/vllm-project/vllm/pull/43286) [Misc] Replace assert with proper exceptions for security and validation in pooling — @taneem-ibrahim → `nan`
- [#42951](https://github.com/vllm-project/vllm/pull/42951) [XPU]feat: add XPU fallback for MoE topk routing and MXFP4 backend — @majian4work → `nan`
- [#41126](https://github.com/vllm-project/vllm/pull/41126) [Attention] Mamba attention module refactor — @wangxiyuan → `nan`
- [#43225](https://github.com/vllm-project/vllm/pull/43225) [CPU] Experimentally enable Triton and MRV2 — @bigPYJ1151 → `nan`
- [#43393](https://github.com/vllm-project/vllm/pull/43393) [Docs] Note image preprocessing difference between qwen_vl_utils and vllm. — @noooop → `nan`
- [#43360](https://github.com/vllm-project/vllm/pull/43360) Fix the docker build failure in tpu-inference — @mrjunwan-lang → `nan`
- [#43377](https://github.com/vllm-project/vllm/pull/43377) [BugFix] Fix setuptools-rust dep in requirements files — @njhill → `nan`
- [#43321](https://github.com/vllm-project/vllm/pull/43321) Correcting the mock classes for MM GC tests — @wdhongtw → `nan`
- [#43296](https://github.com/vllm-project/vllm/pull/43296) [CI] Fix "test_awq_load[gemma4-moe-*]" failure — @haosdent → `nan`
- [#43314](https://github.com/vllm-project/vllm/pull/43314) [CI] Fix test_lora_with_spec_decode on V2 model runner — @haosdent → `nan`
- [#43213](https://github.com/vllm-project/vllm/pull/43213) [Model] Fix MiniCPM-V 4.6 vit_merger qkv weight loading — @tc-mb → `nan`
- [#42972](https://github.com/vllm-project/vllm/pull/42972) [Model] Use `AutoWeightsLoader` for Voyage — @yufufi → `nan`
- [#43064](https://github.com/vllm-project/vllm/pull/43064) [CI] De-flake renderers/test_hf.py::test_resolve_content_format_fallbacks[Qwen/Qwen-VL-string] — @haosdent → `nan`
- [#37888](https://github.com/vllm-project/vllm/pull/37888) [XPU] Enable multiple key kernels for sparse attention — @xwu-intel → `nan`
- [#43020](https://github.com/vllm-project/vllm/pull/43020) [Bugfix] Make CuMemAllocator free callback stream-aware — @zixi-qi → `nan`
- _…and 164 more_

</details>
