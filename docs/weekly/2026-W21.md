# vLLM weekly digest — 2026-05-22 (W21)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

## TL;DR
This week saw significant enhancements in model support and performance optimizations, particularly with the introduction of new features for DeepSeek V4 and improvements in FlashAttention. Notable bug fixes were also implemented across various components, ensuring better stability and functionality.

## Kernels & attention
- Added NVFP4 MoE support for DeepSeek V4, enhancing its performance capabilities ([#42209](https://github.com/vllm-project/vllm/pull/42209)).
- Optimized `CutlassFP8ScaledMMLinearKernel` for padding, achieving a 13.5% TTFT improvement ([#42651](https://github.com/vllm-project/vllm/pull/42651)).
- Enabled FULL cudagraph capture for TRITON_MLA decode, improving efficiency in model inference ([#42885](https://github.com/vllm-project/vllm/pull/42885)).

## Quantization
- Introduced FP8 per-tensor Q scale support to the Triton attention backend, enhancing quantization capabilities ([#42080](https://github.com/vllm-project/vllm/pull/42080)).
- Fixed swiglu limit issue for humming backend and DeepSeek V4 in FP8 path, addressing quantization-related bugs ([#42541](https://github.com/vllm-project/vllm/pull/42541)).

## Parallelism & scheduling
- Improved KV cache handling with the addition of a persistent cache for FlashInfer autotuning, optimizing resource management ([#42527](https://github.com/vllm-project/vllm/pull/42527)).
- Enhanced support for PP (Pipeline Parallelism) in the Cohere vision model, allowing for better parallel processing ([#42819](https://github.com/vllm-project/vllm/pull/42819)).

## Model support
- Added support for OpenVLA, expanding the range of architectures supported by vLLM ([#42654](https://github.com/vllm-project/vllm/pull/42654)).
- Introduced post-norm architecture support for EAGLE-3 speculators, enhancing model capabilities ([#42764](https://github.com/vllm-project/vllm/pull/42764)).
- Fixed loading issues for Qwen3.5-MTP and Qwen3-VL models, ensuring smoother operation ([#42716](https://github.com/vllm-project/vllm/pull/42716)).

## API & serving
- Added API key authorization to /v2 endpoints, improving security for API interactions ([#42594](https://github.com/vllm-project/vllm/pull/42594)).
- Updated MooncakeStoreConnector to support disk offloading, enhancing data management capabilities ([#42889](https://github.com/vllm-project/vllm/pull/42889)).

## Watch list
- Monitor ongoing discussions regarding the integration of Rust front-end features and potential impacts on existing workflows ([#40848](https://github.com/vllm-project/vllm/pull/40848)).

## PRs merged this window (208)

<details><summary>Click to expand the raw list</summary>

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
- [#40841](https://github.com/vllm-project/vllm/pull/40841) [Frontend] DP Supervisor — @yewentao256 → `nan`
- [#43260](https://github.com/vllm-project/vllm/pull/43260) [Frontend] Add truncation side to OpenAI endpoints — @ruizhang99 → `nan`
- [#43236](https://github.com/vllm-project/vllm/pull/43236) [ROCm][CI] add warmup to mem_util test before measurement — @divakar-amd → `nan`
- [#41753](https://github.com/vllm-project/vllm/pull/41753) [ROCm] Add XGMI backend for MoRI Connector — @simondanielsson → `nan`
- [#42855](https://github.com/vllm-project/vllm/pull/42855) [Bugfix] Fix DSV4 Base model swiglu limit issue in FP8 path  — @zx3xyy → `nan`
- [#43378](https://github.com/vllm-project/vllm/pull/43378) [CI] Fix dockerfile dependency graph failure for pre-commit — @Isotr0py → `nan`
- [#43283](https://github.com/vllm-project/vllm/pull/43283) [Rust Frontend] Move code from `vllm-frontend-rs` — @BugenZhao → `nan`
- [#41873](https://github.com/vllm-project/vllm/pull/41873) [Bugfix] Zero stale is_prefilling in padded CUDA graph rows for Mamba — @liulanze → `nan`
- [#43125](https://github.com/vllm-project/vllm/pull/43125) [BugFix] Use correct logprobs for `logprob_token_ids` — @njhill → `nan`
- [#42968](https://github.com/vllm-project/vllm/pull/42968) [Feature] Add `--cpu-distributed-timeout-seconds` CLI Option for CPU Process Group Timeout — @fangyuchu → `nan`
- [#43168](https://github.com/vllm-project/vllm/pull/43168) [Frontend] Rework fastokens integration — @njhill → `nan`
- [#43038](https://github.com/vllm-project/vllm/pull/43038) Disable build isolation to bypass CUDA related deps for vllm-tpu — @ylangtsou → `nan`
- [#43105](https://github.com/vllm-project/vllm/pull/43105) [Core] Add native ModelExpress load format — @zhengluo-nv → `nan`
- [#42988](https://github.com/vllm-project/vllm/pull/42988) [Perf] `zeros` -> `empty` to remove additional fill — @yewentao256 → `nan`
- [#43148](https://github.com/vllm-project/vllm/pull/43148) [Deprecation] Mark env vars covered by --moe-backend / --linear-backend — @mgoin → `nan`
- [#43079](https://github.com/vllm-project/vllm/pull/43079) [Bugfix] Add early validation to reject incompatible runner types for embedding models — @anishesg → `nan`
- [#43311](https://github.com/vllm-project/vllm/pull/43311) [CI] Fix CPU tests failing on `tl.exp2` import — @haosdent → `nan`
- [#40172](https://github.com/vllm-project/vllm/pull/40172) [Perf] [Hybrid] Fused Triton kernel for GPU-side Mamba state postprocessing — @fuscof-ibm → `nan`
- [#42943](https://github.com/vllm-project/vllm/pull/42943) [CPU][RISC-V] Add VLEN=256 support to RVV attention kernels — @velonica0 → `nan`
- [#43266](https://github.com/vllm-project/vllm/pull/43266) [XPU][CI]Fix Docker image pull-to-run race in Intel GPU CI — @zxd1997066 → `nan`
- [#43292](https://github.com/vllm-project/vllm/pull/43292) [CI] Pin protoc binary in rust-build stages — @haosdent → `nan`
- [#43261](https://github.com/vllm-project/vllm/pull/43261) [Bug] Fix ci issue `assert output_size is not None` AssertionError — @yewentao256 → `nan`
- [#43085](https://github.com/vllm-project/vllm/pull/43085) [Test] Replace zephyr-7b-beta (7B) with SmolLM2-135M in tokenization test — @khluu → `nan`
- [#43223](https://github.com/vllm-project/vllm/pull/43223) Fix FlashInfer TRTLLM NvFP4 monolithic MoE routing — @zhangxin81 → `nan`
- [#43195](https://github.com/vllm-project/vllm/pull/43195) Update KDA chunk prefill decay to use exp2 semantics — @zexplorerhj → `nan`
- [#43287](https://github.com/vllm-project/vllm/pull/43287) [XPU] add setuptools-rust for xpu dependency — @jikunshang → `nan`
- [#43197](https://github.com/vllm-project/vllm/pull/43197) [CI] De-flake test_models for bigscience/bloom-560m — @haosdent → `nan`
- [#39601](https://github.com/vllm-project/vllm/pull/39601) [Bugfix] Fix glm4_moe_tool_parser._is_string_type for /v1/responses FunctionTool format — @ianliuy → `nan`
- [#43245](https://github.com/vllm-project/vllm/pull/43245) [Benchmark] Add num-warmup to vllm bench throughput — @yzong-rh → `nan`
- [#42905](https://github.com/vllm-project/vllm/pull/42905) [Bugfix] Warn when renderer_num_workers has no effect on offline LLM — @DaoyuanLi2816 → `nan`
- [#40848](https://github.com/vllm-project/vllm/pull/40848) [Frontend][RFC] Rust front-end integration — @njhill → `nan`
- [#38973](https://github.com/vllm-project/vllm/pull/38973) [ToolParser][Bugfix] Re-land: Fix anyOf/oneOf/$ref type resolution in Qwen3CoderToolParser (#37831) — @AAISSJ → `nan`
- [#43140](https://github.com/vllm-project/vllm/pull/43140) [Refactor] Use shared coerce_to_schema_type in Seed-OSS tool parser — @sfeng33 → `nan`
- [#42664](https://github.com/vllm-project/vllm/pull/42664) [Frontend] Normalize reasoning_content to reasoning for client compatibility — @bbrowning → `nan`
- _…and 148 more_

</details>
