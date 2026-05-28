# vLLM weekly digest — 2026-05-28 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## PRs merged this window (190)

<details><summary>Click to expand the raw list</summary>

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
- [#43546](https://github.com/vllm-project/vllm/pull/43546) [Docs] Fix the duplicate doc icon issue — @chunyang-wen → `nan`
- [#39155](https://github.com/vllm-project/vllm/pull/39155) [BugFix] HFValidationError with cloud storage URIs when HF_HUB_OFFLINE=1 — @sts07142 → `nan`
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
- _…and 130 more_

</details>
