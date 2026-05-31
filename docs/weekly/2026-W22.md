# vLLM weekly digest — 2026-05-31 (W22)

_Window: last 7 days · upstream: [vllm-project/vllm](https://github.com/vllm-project/vllm)_

_LLM digest skipped: RuntimeError: ANTHROPIC_API_KEY not set for anthropic backend_

## Releases this window

- [`v0.22.0`](https://github.com/vllm-project/vllm/releases/tag/v0.22.0) — 2026-05-29 10:28 UTC

## PRs merged this window (199)

<details><summary>Click to expand the raw list</summary>

- [#43956](https://github.com/vllm-project/vllm/pull/43956) [CI/Build] Enable Step3p7ForConditionalGeneration testing — @jeejeelee → `nan`
- [#41813](https://github.com/vllm-project/vllm/pull/41813) [CPU][Zen] Route W8A8 and W4A16 linear inference through zentorch on AMD Zen CPUs — @aadwived → `nan`
- [#44050](https://github.com/vllm-project/vllm/pull/44050) [MRV2] Support breakable CUDA graph — @WoosukKwon → `nan`
- [#43909](https://github.com/vllm-project/vllm/pull/43909) [Bug] Fix gemma4 MTP IMA issue when TP>1, `CUDA error: an illegal memory access was encountered` — @yewentao256 → `nan`
- [#44047](https://github.com/vllm-project/vllm/pull/44047) [Governance] Add @BugenZhao as Rust frontend code owner — @BugenZhao → `nan`
- [#43817](https://github.com/vllm-project/vllm/pull/43817) [ROCm] Add attention sink support to AITer flash attention backend — @sphinx07 → `nan`
- [#42379](https://github.com/vllm-project/vllm/pull/42379) [Bugfix] Fix RMSNorm kernels to multiply in weight's native dtype — @liulanze → `nan`
- [#43571](https://github.com/vllm-project/vllm/pull/43571) [BugFix][Platform] Fix import vllm.platforms.rocm error on non-CUDA test_gpt_oss.py — @Liangliang-Ma → `nan`
- [#43881](https://github.com/vllm-project/vllm/pull/43881) [ROCm] cmake: support PYTORCH_FOUND_HIP for torch 2.13 native HIP language support — @nemanjaudovic → `nan`
- [#44028](https://github.com/vllm-project/vllm/pull/44028) [ROCm][CI] Fix failure in the Phi3V pooling test — @AndreasKaratzas → `nan`
- [#43997](https://github.com/vllm-project/vllm/pull/43997) [Refactor] Remove dead current_tool_name_sent assignments from tool parsers — @sfeng33 → `nan`
- [#43792](https://github.com/vllm-project/vllm/pull/43792) offload prompt_embeds decode in render_prompts_async to avoid blocking — @gagandhakrey → `nan`
- [#38445](https://github.com/vllm-project/vllm/pull/38445) [PERF]MiniMax-M2 gate kernel — @jeejeelee → `nan`
- [#44033](https://github.com/vllm-project/vllm/pull/44033) Revert "[MoE Refactor] Migrate MoeWNA16Method quantization to MK orac… — @bnellnm → `nan`
- [#43974](https://github.com/vllm-project/vllm/pull/43974) [CI] Fix smoke test step key to bypass block gate — @khluu → `nan`
- [#44023](https://github.com/vllm-project/vllm/pull/44023) [CI] Remove duplicate Harmony test coverage — @sfeng33 → `nan`
- [#43108](https://github.com/vllm-project/vllm/pull/43108) [MoE Refactor] Remove supports_expert_map — @bnellnm → `nan`
- [#42647](https://github.com/vllm-project/vllm/pull/42647) [MoE Refactor] Migrate MoeWNA16Method quantization to MK oracle — @bnellnm → `nan`
- [#44009](https://github.com/vllm-project/vllm/pull/44009) [Frontend] Clean up stop_token_ids override for Harmony — @yzong-rh → `nan`
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
- _…and 139 more_

</details>
