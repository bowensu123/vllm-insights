# vLLM weekly digest — 2026-05-29 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## Releases this window

- [`v0.22.0`](https://github.com/vllm-project/vllm/releases/tag/v0.22.0) — 2026-05-29 10:28 UTC

## PRs merged this window (220)

<details><summary>Click to expand the raw list</summary>

- [#43346](https://github.com/vllm-project/vllm/pull/43346) [Metrics] Exclude KV transfer tokens from iteration_tokens_total — @tlrmchlsmth → `nan`
- [#43688](https://github.com/vllm-project/vllm/pull/43688) [Feature] SSL support for dp supervisor — @yewentao256 → `nan`
- [#44019](https://github.com/vllm-project/vllm/pull/44019) Add @khluu to CODEOWNERS — @khluu → `nan`
- [#44011](https://github.com/vllm-project/vllm/pull/44011) [CI] Remove redundant test_chat_with_tool_reasoning.py — @sfeng33 → `nan`
- [#43971](https://github.com/vllm-project/vllm/pull/43971) [CI] Make Model Executor test hangs fail fast with a traceback — @khluu → `nan`
- [#44005](https://github.com/vllm-project/vllm/pull/44005) [Bug] Fix torch device issue for MOE permute — @yewentao256 → `nan`
- [#43998](https://github.com/vllm-project/vllm/pull/43998) [Bugfix] Fix Ray placement group allocation with grouped nodes — @czhu-cohere → `nan`
- [#43988](https://github.com/vllm-project/vllm/pull/43988) [Bugfix] Use storage_block_size in KV cache reshape for compressed specs (DeepSeek V4) — @zixi-qi → `nan`
- [#43219](https://github.com/vllm-project/vllm/pull/43219) [EPLB] Make async EPLB default — @ilmarkov → `nan`
- [#42553](https://github.com/vllm-project/vllm/pull/42553) [MoE Refactor] WNA16 MoE backend selection into oracle module — @bnellnm → `nan`
- [#43616](https://github.com/vllm-project/vllm/pull/43616) [Bugfix] Disable allreduce_rms_fusion when pipeline_parallel_size > 1 — @zixi-qi → `nan`
- [#43818](https://github.com/vllm-project/vllm/pull/43818) [Misc] added unit tests for the core pooling methods — @taneem-ibrahim → `nan`
- [#43922](https://github.com/vllm-project/vllm/pull/43922) docs: clarify ITL acronym in optimization docs — @chunyang-wen → `nan`
- [#43857](https://github.com/vllm-project/vllm/pull/43857) Add vLLM library info to Hugging Face Hub requests — @Wauplin → `nan`
- [#43977](https://github.com/vllm-project/vllm/pull/43977) [Bugfix][CPU] Remove invalid extra deps — @bigPYJ1151 → `nan`
- [#43972](https://github.com/vllm-project/vllm/pull/43972) Skip docs build if PR doesn't affect docs — @hmellor → `nan`
- [#43961](https://github.com/vllm-project/vllm/pull/43961) [Bugfix] Corrupted MLA + linear attention — @gau-nernst → `nan`
- [#42982](https://github.com/vllm-project/vllm/pull/42982) [ROCm][Perf] DSv3.2 MI355X TP4 decode-step orchestration cleanup (3 micro-opts) — @frida-andersson → `nan`
- [#42595](https://github.com/vllm-project/vllm/pull/42595) [Bugfix] [ROCm] [DSV4] Fix AITER MXFP4 MoE weight loading and shuffle… — @MHYangAMD → `nan`
- [#41394](https://github.com/vllm-project/vllm/pull/41394) [Kernel][ROCm] Native W4A16 kernel for AMD RDNA3 (gfx1100) — fp16 + bf16 — @JartX → `nan`
- [#37622](https://github.com/vllm-project/vllm/pull/37622) [Bugfix] Fix Step3 pipeline parallel KeyError for residual tensor — @JMonde → `v0.22.0`
- [#43871](https://github.com/vllm-project/vllm/pull/43871) [CI] Nixl+SimpleCPUOffloadingConnector unit tests — @NickLucche → `v0.22.0`
- [#43565](https://github.com/vllm-project/vllm/pull/43565) [XPU] support MTP of gdn attention — @mayuyuace → `v0.22.0`
- [#43703](https://github.com/vllm-project/vllm/pull/43703) [CI][ROCm] Don't skip MoRI-IO Connector tests — @simondanielsson → `v0.22.0`
- [#43947](https://github.com/vllm-project/vllm/pull/43947) [XPU] fix xpu install document triton-xpu version — @jikunshang → `v0.22.0`
- [#43945](https://github.com/vllm-project/vllm/pull/43945) [ROCm][CI] Fix AITER unified attention for encoder-decoder cross-attention — @AndreasKaratzas → `v0.22.0`
- [#43761](https://github.com/vllm-project/vllm/pull/43761) [Frontend]Responses API supports chat_template_kwargs — @chaunceyjiang → `v0.22.0`
- [#43898](https://github.com/vllm-project/vllm/pull/43898) [ROCm][DSv4] Remove device pipeline stall in sparse attention — @kliuae → `v0.22.0`
- [#43633](https://github.com/vllm-project/vllm/pull/43633) [CPU Backend] CPU top-k and top-p sampling kernels using Triton — @tianmu-li → `v0.22.0`
- [#42822](https://github.com/vllm-project/vllm/pull/42822) add gelu_tanh to xpu moe backend supported activations — @yintong-lu → `v0.22.0`
- [#43712](https://github.com/vllm-project/vllm/pull/43712) [CI] Separate non-root smoke tests from image build step — @khluu → `v0.22.0`
- [#43717](https://github.com/vllm-project/vllm/pull/43717) [9/n] Migrate attention and cache kernels to torch stable ABI (continued)  — @cleonard530 → `v0.22.0`
- [#43234](https://github.com/vllm-project/vllm/pull/43234) [Refactor] Remove dead code — @yewentao256 → `v0.22.0`
- [#43797](https://github.com/vllm-project/vllm/pull/43797) [kv_offload] Skip decode-phase blocks in CPU offload — @Etelis → `v0.22.0`
- [#43277](https://github.com/vllm-project/vllm/pull/43277) [XPU] add scale transpose to prepare_fp8_moe_layer_for_xpu and bump up kernels — @mayuyuace → `v0.22.0`
- [#42288](https://github.com/vllm-project/vllm/pull/42288) Adjust design around encoder_cudagraph_forward — @wdhongtw → `v0.22.0`
- [#43575](https://github.com/vllm-project/vllm/pull/43575) [feat] add GlmgaProcessor specific logits in `glm4_1v.py` — @JaredforReal → `v0.22.0`
- [#43905](https://github.com/vllm-project/vllm/pull/43905) [DSv4] Move mHC tilelang kernels & Don't use CustomOP in dsv4/nvidia — @WoosukKwon → `v0.22.0`
- [#43270](https://github.com/vllm-project/vllm/pull/43270) [Misc][NUMA] Auto-bind to PCT priority cores on DGX B300 + widen EngineCore across shard NUMA nodes — @vadiklyutiy → `v0.22.0`
- [#43854](https://github.com/vllm-project/vllm/pull/43854) [Rust Frontend] Add `/version` endpoint using engine-reported value — @BugenZhao → `v0.22.0`
- [#43859](https://github.com/vllm-project/vllm/pull/43859) [Model]Support Step-3.7-Flash — @ltd0924 → `v0.22.0`
- [#43925](https://github.com/vllm-project/vllm/pull/43925) [CI] Enable prefix caching in BFCL benchmark — @yzong-rh → `v0.22.0`
- [#41459](https://github.com/vllm-project/vllm/pull/41459) fix(frontend): Add multimodal placeholders to Gemma4 tool message template — @harshaljanjani → `v0.22.0`
- [#43120](https://github.com/vllm-project/vllm/pull/43120) [AMD][CI][BugFix] Fix  Distributed Compile Unit Tests (2xH100-2xMI300) group — @rasmith → `v0.22.0`
- [#43901](https://github.com/vllm-project/vllm/pull/43901) Refactor output filename handling in ci-fetch-log.sh — @mgoin → `v0.22.0`
- [#43445](https://github.com/vllm-project/vllm/pull/43445) [Spec Decode] Allow causal DFlash — @benchislett → `v0.22.0`
- [#43891](https://github.com/vllm-project/vllm/pull/43891) [Model Refactoring] Remove unncessary torch op registration for DSv4 — @WoosukKwon → `v0.22.0`
- [#43205](https://github.com/vllm-project/vllm/pull/43205) [KV Offload] Add per-request offloading policy via `on_new_request` lifecycle hook — @ronensc → `v0.22.0`
- [#43732](https://github.com/vllm-project/vllm/pull/43732) [Core] Cleanup KVConnector handling with PP + fix MRV2  — @njhill → `v0.22.0`
- [#42083](https://github.com/vllm-project/vllm/pull/42083) [Feat] Add support for per GPU worker RDMA NIC selection — @rajkiranjoshi → `v0.22.0`
- [#43784](https://github.com/vllm-project/vllm/pull/43784) Deprecate `JAISLMHeadModel` — @hmellor → `v0.22.0`
- [#42796](https://github.com/vllm-project/vllm/pull/42796) [MM][CG] Avoid over-padding Qwen2.5-VL encoder cudagraph window metadata — @huanghua1994 → `v0.22.0`
- [#43331](https://github.com/vllm-project/vllm/pull/43331) [ROCm] Enable the aiter top-k/top-p sampler by default — @JohnQinAMD → `v0.22.0`
- [#43660](https://github.com/vllm-project/vllm/pull/43660) [Attention][AMD] Standardize kv layout to blocks first for AMD — @NickLucche → `v0.22.0`
- [#43330](https://github.com/vllm-project/vllm/pull/43330) Allow native KV cache dtype in Triton cache update — @mikekg → `v0.22.0`
- [#43670](https://github.com/vllm-project/vllm/pull/43670) [Rust Frontend] Optimize multimodal prompt expansion — @ricky-chaoju → `v0.22.0`
- [#43356](https://github.com/vllm-project/vllm/pull/43356) Add Cosmos3 Reasoner model — @MaciejBalaNV → `v0.22.0`
- [#43136](https://github.com/vllm-project/vllm/pull/43136) [ROCm] Bump ROCm to 7.2.3 — @micah-wil → `v0.22.0`
- [#41426](https://github.com/vllm-project/vllm/pull/41426) [XPU][MoE] Add WNA16 oracle backend for GPTQ sym-int4 (xpu_fused_moe) — @jasonboukheir → `v0.22.0`
- [#40687](https://github.com/vllm-project/vllm/pull/40687) [ROCm][Perf] Support N=5 in wvSplitK skinny GEMM kernels for speculative decoding — @mgehre-amd → `v0.22.0`
- _…and 160 more_

</details>
