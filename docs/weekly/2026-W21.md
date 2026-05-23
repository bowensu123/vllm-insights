# vLLM weekly digest — 2026-05-23 (W21)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

## TL;DR
This week saw significant performance optimizations, particularly in FlashAttention and quantization methods, alongside enhancements in model support for various architectures. Notably, the introduction of multi-stream capabilities and improvements in the handling of MoE (Mixture of Experts) models were highlighted. Additionally, several bug fixes and refactoring efforts aimed at streamlining the codebase were merged.

## Kernels & attention
- Added `head_dim=512` support for FlashInfer's trtllm attention backend, enhancing its capability for larger models ([#38822](https://github.com/vllm-project/vllm/pull/38822)).
- Optimized hidden state extraction logic, which is expected to improve performance during inference ([#37374](https://github.com/vllm-project/vllm/pull/37374)).
- Introduced multiple key kernels for sparse attention on XPU, improving efficiency for specific workloads ([#37888](https://github.com/vllm-project/vllm/pull/37888)).

## Quantization
- Implemented W4A16 NVFP4 fused MoE with mixed-precision dispatch, enhancing quantization performance ([#42566](https://github.com/vllm-project/vllm/pull/42566)).
- Fixed a bug that cleared error messages for FP8 quantization on unsupported GPUs, improving user experience during model deployment ([#36854](https://github.com/vllm-project/vllm/pull/36854)).

## Parallelism & scheduling
- Enhanced the elastic_ep stage for committing MoE quantization methods, allowing for more dynamic model configurations ([#40881](https://github.com/vllm-project/vllm/pull/40881)).
- Added support for sharing KV cache layers in Model Runner V2, improving memory efficiency during inference ([#35045](https://github.com/vllm-project/vllm/pull/35045)).

## Model support
- Added support for OpenVLA architecture, expanding the range of models that can be utilized within the framework ([#42654](https://github.com/vllm-project/vllm/pull/42654)).
- Introduced support for post-norm architecture in EAGLE-3 speculators, enhancing model capabilities for specific tasks ([#42764](https://github.com/vllm-project/vllm/pull/42764)).

## Hardware
- Added MXFP4 W4A16 MoE support for CPU, broadening the hardware compatibility for advanced quantization techniques ([#41922](https://github.com/vllm-project/vllm/pull/41922)).
- Improved CPU thread utilization, optimizing performance on multi-core systems ([#42666](https://github.com/vllm-project/vllm/pull/42666)).

## API & serving
- Simplified the authentication middleware path extraction, streamlining API interactions ([#43426](https://github.com/vllm-project/vllm/pull/43426)).
- Added truncation options to OpenAI-compatible endpoints, enhancing flexibility in response handling ([#43260](https://github.com/vllm-project/vllm/pull/43260)).

## Watch list
- Ongoing discussions around the removal of dead code and potential impacts on future releases ([#40733](https://github.com/vllm-project/vllm/pull/40733)).
- Monitoring the integration of Rust frontend features, which may introduce breaking changes in the API ([#40848](https://github.com/vllm-project/vllm/pull/40848)).

## PRs merged this window (210)

<details><summary>Click to expand the raw list</summary>

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
- _…and 150 more_

</details>
