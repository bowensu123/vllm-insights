# vLLM weekly digest — 2026-05-22 (W21)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

## TL;DR
This week saw significant improvements in model support and performance optimizations, particularly for the DeepSeek V4 and FlashInfer systems. Notable bug fixes were implemented across various components, enhancing stability and functionality. The introduction of new features and enhancements in the API and serving aspects also indicates a focus on usability and performance.

## Kernels & attention
- Improved FlashInfer GDN prefill kernel for Blackwell architecture ([#40717](https://github.com/vllm-project/vllm/pull/40717)).
- Enhanced Mamba attention module with a refactor for better performance ([#41126](https://github.com/vllm-project/vllm/pull/41126)).
- Added support for multiple key kernels for sparse attention on XPU ([#37888](https://github.com/vllm-project/vllm/pull/37888)).

## Quantization
- Introduced FP8 per-tensor Q scale support for Triton attention backend ([#42080](https://github.com/vllm-project/vllm/pull/42080)).
- Optimized `CutlassFP8ScaledMMLinearKernel` for better performance, achieving a 13.5% improvement ([#42651](https://github.com/vllm-project/vllm/pull/42651)).
- Added support for FP8 MoE with the humming backend ([#42540](https://github.com/vllm-project/vllm/pull/42540)).

## Parallelism & scheduling
- Enabled full cudagraph capture for Triton MLA decode, improving performance ([#42885](https://github.com/vllm-project/vllm/pull/42885)).
- Added a persistent cache for FlashInfer autotuning to enhance efficiency ([#42527](https://github.com/vllm-project/vllm/pull/42527)).

## Model support
- Added support for OpenVLA, enhancing multimodal capabilities ([#42654](https://github.com/vllm-project/vllm/pull/42654)).
- Improved DeepSeek V4 functionality and accuracy with several bug fixes ([#42810](https://github.com/vllm-project/vllm/pull/42810)).
- Introduced support for post-norm architecture in EAGLE-3 speculators ([#42764](https://github.com/vllm-project/vllm/pull/42764)).

## API & serving
- Forwarded `X-data-parallel-rank` header on inference endpoint to improve parallel processing ([#42347](https://github.com/vllm-project/vllm/pull/42347)).
- Added CLI options for `--spec-method`, `--spec-model`, and `--spec-tokens` for better user control ([#42476](https://github.com/vllm-project/vllm/pull/42476)).

## Watch list
- Ongoing discussions about the removal of dead code and its implications on future development ([#43144](https://github.com/vllm-project/vllm/pull/43144)).
- Monitoring the integration of the Rust frontend and its impact on existing workflows ([#40848](https://github.com/vllm-project/vllm/pull/40848)).

## PRs merged this window (209)

<details><summary>Click to expand the raw list</summary>

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
- _…and 149 more_

</details>
