# vLLM weekly digest — 2026-05-29 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## Releases this window

- [`v0.22.0`](https://github.com/vllm-project/vllm/releases/tag/v0.22.0) — 2026-05-29 10:28 UTC

## PRs merged this window (214)

<details><summary>Click to expand the raw list</summary>

- [#37622](https://github.com/vllm-project/vllm/pull/37622) [Bugfix] Fix Step3 pipeline parallel KeyError for residual tensor — @JMonde → `nan`
- [#43871](https://github.com/vllm-project/vllm/pull/43871) [CI] Nixl+SimpleCPUOffloadingConnector unit tests — @NickLucche → `nan`
- [#43565](https://github.com/vllm-project/vllm/pull/43565) [XPU] support MTP of gdn attention — @mayuyuace → `nan`
- [#43703](https://github.com/vllm-project/vllm/pull/43703) [CI][ROCm] Don't skip MoRI-IO Connector tests — @simondanielsson → `nan`
- [#43947](https://github.com/vllm-project/vllm/pull/43947) [XPU] fix xpu install document triton-xpu version — @jikunshang → `nan`
- [#43945](https://github.com/vllm-project/vllm/pull/43945) [ROCm][CI] Fix AITER unified attention for encoder-decoder cross-attention — @AndreasKaratzas → `nan`
- [#43761](https://github.com/vllm-project/vllm/pull/43761) [Frontend]Responses API supports chat_template_kwargs — @chaunceyjiang → `nan`
- [#43898](https://github.com/vllm-project/vllm/pull/43898) [ROCm][DSv4] Remove device pipeline stall in sparse attention — @kliuae → `nan`
- [#43633](https://github.com/vllm-project/vllm/pull/43633) [CPU Backend] CPU top-k and top-p sampling kernels using Triton — @tianmu-li → `nan`
- [#42822](https://github.com/vllm-project/vllm/pull/42822) add gelu_tanh to xpu moe backend supported activations — @yintong-lu → `nan`
- [#43712](https://github.com/vllm-project/vllm/pull/43712) [CI] Separate non-root smoke tests from image build step — @khluu → `nan`
- [#43717](https://github.com/vllm-project/vllm/pull/43717) [9/n] Migrate attention and cache kernels to torch stable ABI (continued)  — @cleonard530 → `nan`
- [#43234](https://github.com/vllm-project/vllm/pull/43234) [Refactor] Remove dead code — @yewentao256 → `nan`
- [#43797](https://github.com/vllm-project/vllm/pull/43797) [kv_offload] Skip decode-phase blocks in CPU offload — @Etelis → `nan`
- [#43277](https://github.com/vllm-project/vllm/pull/43277) [XPU] add scale transpose to prepare_fp8_moe_layer_for_xpu and bump up kernels — @mayuyuace → `nan`
- [#42288](https://github.com/vllm-project/vllm/pull/42288) Adjust design around encoder_cudagraph_forward — @wdhongtw → `nan`
- [#43575](https://github.com/vllm-project/vllm/pull/43575) [feat] add GlmgaProcessor specific logits in `glm4_1v.py` — @JaredforReal → `nan`
- [#43905](https://github.com/vllm-project/vllm/pull/43905) [DSv4] Move mHC tilelang kernels & Don't use CustomOP in dsv4/nvidia — @WoosukKwon → `nan`
- [#43270](https://github.com/vllm-project/vllm/pull/43270) [Misc][NUMA] Auto-bind to PCT priority cores on DGX B300 + widen EngineCore across shard NUMA nodes — @vadiklyutiy → `nan`
- [#43854](https://github.com/vllm-project/vllm/pull/43854) [Rust Frontend] Add `/version` endpoint using engine-reported value — @BugenZhao → `nan`
- [#43859](https://github.com/vllm-project/vllm/pull/43859) [Model]Support Step-3.7-Flash — @ltd0924 → `nan`
- [#43925](https://github.com/vllm-project/vllm/pull/43925) [CI] Enable prefix caching in BFCL benchmark — @yzong-rh → `nan`
- [#41459](https://github.com/vllm-project/vllm/pull/41459) fix(frontend): Add multimodal placeholders to Gemma4 tool message template — @harshaljanjani → `nan`
- [#43120](https://github.com/vllm-project/vllm/pull/43120) [AMD][CI][BugFix] Fix  Distributed Compile Unit Tests (2xH100-2xMI300) group — @rasmith → `nan`
- [#43901](https://github.com/vllm-project/vllm/pull/43901) Refactor output filename handling in ci-fetch-log.sh — @mgoin → `nan`
- [#43445](https://github.com/vllm-project/vllm/pull/43445) [Spec Decode] Allow causal DFlash — @benchislett → `nan`
- [#43891](https://github.com/vllm-project/vllm/pull/43891) [Model Refactoring] Remove unncessary torch op registration for DSv4 — @WoosukKwon → `nan`
- [#43205](https://github.com/vllm-project/vllm/pull/43205) [KV Offload] Add per-request offloading policy via `on_new_request` lifecycle hook — @ronensc → `nan`
- [#43732](https://github.com/vllm-project/vllm/pull/43732) [Core] Cleanup KVConnector handling with PP + fix MRV2  — @njhill → `nan`
- [#42083](https://github.com/vllm-project/vllm/pull/42083) [Feat] Add support for per GPU worker RDMA NIC selection — @rajkiranjoshi → `nan`
- [#43784](https://github.com/vllm-project/vllm/pull/43784) Deprecate `JAISLMHeadModel` — @hmellor → `nan`
- [#42796](https://github.com/vllm-project/vllm/pull/42796) [MM][CG] Avoid over-padding Qwen2.5-VL encoder cudagraph window metadata — @huanghua1994 → `nan`
- [#43331](https://github.com/vllm-project/vllm/pull/43331) [ROCm] Enable the aiter top-k/top-p sampler by default — @JohnQinAMD → `nan`
- [#43660](https://github.com/vllm-project/vllm/pull/43660) [Attention][AMD] Standardize kv layout to blocks first for AMD — @NickLucche → `nan`
- [#43330](https://github.com/vllm-project/vllm/pull/43330) Allow native KV cache dtype in Triton cache update — @mikekg → `nan`
- [#43670](https://github.com/vllm-project/vllm/pull/43670) [Rust Frontend] Optimize multimodal prompt expansion — @ricky-chaoju → `nan`
- [#43356](https://github.com/vllm-project/vllm/pull/43356) Add Cosmos3 Reasoner model — @MaciejBalaNV → `nan`
- [#43136](https://github.com/vllm-project/vllm/pull/43136) [ROCm] Bump ROCm to 7.2.3 — @micah-wil → `nan`
- [#41426](https://github.com/vllm-project/vllm/pull/41426) [XPU][MoE] Add WNA16 oracle backend for GPTQ sym-int4 (xpu_fused_moe) — @jasonboukheir → `nan`
- [#40687](https://github.com/vllm-project/vllm/pull/40687) [ROCm][Perf] Support N=5 in wvSplitK skinny GEMM kernels for speculative decoding — @mgehre-amd → `nan`
- [#43870](https://github.com/vllm-project/vllm/pull/43870) [KV Offload] Rename `SecondaryTierManager.get_finished()` to `get_finished_jobs()` — @ronensc → `nan`
- [#43864](https://github.com/vllm-project/vllm/pull/43864) [Bugfix] Exclude Ray DP from #42585's deferred port allocation — @vadiklyutiy → `nan`
- [#43803](https://github.com/vllm-project/vllm/pull/43803) [Perf] remove seqlen from Mamba SSD chunk kernels — @Majid-Taheri → `nan`
- [#43813](https://github.com/vllm-project/vllm/pull/43813) [Bug] Fix `tests/distributed/test_elastic_ep.py  - assert False` — @yewentao256 → `nan`
- [#43429](https://github.com/vllm-project/vllm/pull/43429) [rust] fix: aggregate `is_sleeping` and `reset_prefix_cache` across DP engines — @willamhou → `nan`
- [#43850](https://github.com/vllm-project/vllm/pull/43850) [Rust Frontend] Reduce Gemma4 tool parser args scan complexity — @BugenZhao → `nan`
- [#43872](https://github.com/vllm-project/vllm/pull/43872) [Rust Frontend] Add `hy_v3` tool parser — @BugenZhao → `nan`
- [#43841](https://github.com/vllm-project/vllm/pull/43841) [CPU] Migrate cpu_awq into awq_marlin — @bigPYJ1151 → `nan`
- [#40344](https://github.com/vllm-project/vllm/pull/40344) [Bugfix][ROCm] Resolve MoRI connector hangs at high concurrency — @simondanielsson → `nan`
- [#43746](https://github.com/vllm-project/vllm/pull/43746) [Model Refactoring] Remove torch compile dependency in DSv4 — @WoosukKwon → `nan`
- [#39983](https://github.com/vllm-project/vllm/pull/39983) Add token-offset based selective offload in OffloadConnector — @ruocco → `nan`
- [#43667](https://github.com/vllm-project/vllm/pull/43667) [Perf][KDA] Fuse gate softplus, chunk-local cumsum, and RCP_LN2 scaling — @zexplorerhj → `nan`
- [#43014](https://github.com/vllm-project/vllm/pull/43014) [Perf] Optimize moe permute by pre-allocate buffer, 9~14% kernel performance improvement — @yewentao256 → `nan`
- [#42965](https://github.com/vllm-project/vllm/pull/42965) [BUGFIX] Multimodal benchmark with MistralTokenizer — @juliendenize → `nan`
- [#43846](https://github.com/vllm-project/vllm/pull/43846) Fix `OlmoHybridForCausalLM` not initialising — @hmellor → `nan`
- [#42423](https://github.com/vllm-project/vllm/pull/42423) [EC Connector] Add shutdown API to EC Connector. — @omerpaz95 → `nan`
- [#41406](https://github.com/vllm-project/vllm/pull/41406) Log dummy DP step in iteration details — @vadiklyutiy → `nan`
- [#42396](https://github.com/vllm-project/vllm/pull/42396) [Feature] Add structured output and effort support to Anthropic Messages API — @chaunceyjiang → `nan`
- [#43866](https://github.com/vllm-project/vllm/pull/43866) [CI] Auto-apply `rust` label to relevant PRs — @BugenZhao → `nan`
- [#43860](https://github.com/vllm-project/vllm/pull/43860) [Bugfix] Fix HyperCLOVAX CI failure after upstream removed remote code — @khluu → `nan`
- _…and 154 more_

</details>
