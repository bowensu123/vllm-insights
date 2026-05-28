# vLLM weekly digest — 2026-05-28 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (212)

<details><summary>Click to expand the raw list</summary>

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
- [#43781](https://github.com/vllm-project/vllm/pull/43781) [Bugfix][ROCm] Fix Accuracy Drop in Sparse Indexer on gfx950 — @kliuae → `nan`
- [#43581](https://github.com/vllm-project/vllm/pull/43581) [Model][Bugfix] Rename weight_mapper to hf_to_vllm_mapper in LlamaNemotronVL pooling models — @jzakrzew → `nan`
- [#42343](https://github.com/vllm-project/vllm/pull/42343) [UX] Increase DP Coordinator startup timeout from 30s to 120s — @wzhao18 → `nan`
- [#39795](https://github.com/vllm-project/vllm/pull/39795) [Feature] Add support for timed trace replay in `vllm bench serve` to replay Moonshot and Alibaba workload traces — @animeshtrivedi → `nan`
- [#43824](https://github.com/vllm-project/vllm/pull/43824) [ROCm][CI] Move workload from MI300 to MI325 — @AndreasKaratzas → `nan`
- [#42879](https://github.com/vllm-project/vllm/pull/42879) [Bugfix] Stream DeepSeek DSML tool-call argument deltas incrementally — @QwertyJack → `nan`
- [#43183](https://github.com/vllm-project/vllm/pull/43183) Restore `Literal` for `WeightTransferConfig.backend` — @hmellor → `nan`
- [#43829](https://github.com/vllm-project/vllm/pull/43829) [DSV4] Remove AMD/XPU path in deepseek_v4/nvidia — @WoosukKwon → `nan`
- [#40923](https://github.com/vllm-project/vllm/pull/40923) [Kernel] Marlin MoE: include SM 12.x in default arch list — @tonyliu312 → `nan`
- [#43768](https://github.com/vllm-project/vllm/pull/43768) [BugFix] Fix hard-coded timeout for multi-API-server startup — @vadiklyutiy → `nan`
- [#43600](https://github.com/vllm-project/vllm/pull/43600) change name of fs_python secondary tier to fs. — @rshavitt → `nan`
- [#43679](https://github.com/vllm-project/vllm/pull/43679) [ROCm][DSV4] Enable Tilelang MHC replacing torch/triton mhc — @tjtanaa → `nan`
- [#43830](https://github.com/vllm-project/vllm/pull/43830) minor docs: fix incorrect example path — @JINO-ROHIT → `nan`
- [#42683](https://github.com/vllm-project/vllm/pull/42683) [Bugfix][Frontend] streaming tool-call serializer drops first args chunk when name and args share a DeltaMessage  — @ignaciosica → `nan`
- [#43808](https://github.com/vllm-project/vllm/pull/43808) [BugFix] Fix blocked reasoning parsing with MRV2 — @njhill → `nan`
- [#43769](https://github.com/vllm-project/vllm/pull/43769) [Bugfix] Pass `routed_scaling_factor` to FlashInfer TRTLLM BF16 MoE — @gau-nernst → `nan`
- [#43243](https://github.com/vllm-project/vllm/pull/43243) fix: parse Qwen3 XML JSON arguments first — @he-yufeng → `nan`
- [#43815](https://github.com/vllm-project/vllm/pull/43815) [ROCm][CI] Stabilize Cargo cache and pre-test image checks — @AndreasKaratzas → `nan`
- [#43664](https://github.com/vllm-project/vllm/pull/43664) [Misc][Rocm] Remove redundant `AiterUnifiedAttentionBackend` block size log — @NickLucche → `nan`
- [#43727](https://github.com/vllm-project/vllm/pull/43727) [MoE] Remove inplace fused experts mechanism — @zyongye → `nan`
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
- _…and 152 more_

</details>
