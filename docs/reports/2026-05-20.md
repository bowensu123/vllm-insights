# vLLM activity report — 2026-05-20

## Summary

- **Releases (all-time):** 94
- **Latest release:** [`v0.21.0`](https://github.com/vllm-project/vllm/releases/tag/v0.21.0) on 2026-05-15
- **Median release interval:** 9.5 days
- **PRs (all-time):** 26888
- **PRs merged in last 7d:** 217
- **Median merge time (all-time):** 23.0 h
- **Commits (cached):** 16780

## Releases in last 7 days

- [`v0.21.0`](https://github.com/vllm-project/vllm/releases/tag/v0.21.0) — 2026-05-15

## PR activity by tech area (last 7 days)

| Area | PRs |
|---|---:|
| Other | 207 |
| Bugfix | 123 |
| Model Support | 60 |
| Hardware-ROCm | 31 |
| Performance | 28 |
| CI/Build | 24 |
| Attention/Kernel | 22 |
| Scheduling/Engine | 20 |
| Quantization | 11 |
| Hardware-CPU | 10 |
| API/Serving | 10 |
| Docs | 6 |
| Tests | 3 |

## Recently merged PRs (last 7 days, top 30)

- [#43160](https://github.com/vllm-project/vllm/pull/43160) [MRV2][BugFix] Fix default-stream CG capture in P/W LoRA case — @njhill → `nan`
- [#43121](https://github.com/vllm-project/vllm/pull/43121) [bug] fix WeightTransferConfig.backend to allow for all strings — @hao-aaron → `nan`
- [#43115](https://github.com/vllm-project/vllm/pull/43115) [CPU][DOC] Fix installation commands for Arm CPUs — @fadara01 → `nan`
- [#41277](https://github.com/vllm-project/vllm/pull/41277) Fix error in Dynamic NTK scaling — @maxdebayser → `nan`
- [#42764](https://github.com/vllm-project/vllm/pull/42764) [Model] Support post-norm architecture for EAGLE-3 supeculators — @Dogacel → `nan`
- [#43129](https://github.com/vllm-project/vllm/pull/43129) [ci] Move language models tests (hybrid) back to L4 — @khluu → `nan`
- [#43119](https://github.com/vllm-project/vllm/pull/43119) [CI failure] Temporarily disable using persistent cache for flashinfer autotune — @wzhao18 → `nan`
- [#42976](https://github.com/vllm-project/vllm/pull/42976) [Bugfix][MoE] FlashInfer one-sided: workspace union across heterogeneous layers — @tomeras91 → `nan`
- [#42994](https://github.com/vllm-project/vllm/pull/42994) [Docs] Fix MooncakeStoreConnector role in disaggregated example — @Dao007forever → `nan`
- [#42080](https://github.com/vllm-project/vllm/pull/42080) [feat] Add FP8 per-tensor Q scale support to Triton attention backend — @DomBrown → `nan`
- [#42540](https://github.com/vllm-project/vllm/pull/42540) [Misc] add humming to dependencies — @jinzhen-lin → `nan`
- [#43025](https://github.com/vllm-project/vllm/pull/43025) [Refactor] Extract extract_types_from_schema utility from Minimax M2 tool parser — @sfeng33 → `nan`
- [#42654](https://github.com/vllm-project/vllm/pull/42654) [Model] Openvla support — @yiwen101 → `nan`
- [#43043](https://github.com/vllm-project/vllm/pull/43043) [XPU] update xpu graph usage — @xinyu-intel → `nan`
- [#42347](https://github.com/vllm-project/vllm/pull/42347) [Perf][4/n] Eliminate various GPU<->CPU syncs — @njhill → `nan`
- [#42887](https://github.com/vllm-project/vllm/pull/42887) [Bugfix] Fix top logprobs token placeholders in `/inference/v1/generate` — @sagearc → `nan`
- [#42677](https://github.com/vllm-project/vllm/pull/42677) [CI] Add MTP + PD disagg test for Qwen3.5 — @ZhanqiuHu → `nan`
- [#43046](https://github.com/vllm-project/vllm/pull/43046) [Misc][MM] Remove redundant code in CLIPAttention — @shen-shanshan → `nan`
- [#43077](https://github.com/vllm-project/vllm/pull/43077) [Model Refactoring] Rename deepseek_v4.py to model.py [4/N] — @WoosukKwon → `nan`
- [#42828](https://github.com/vllm-project/vllm/pull/42828) [KVConnector][DSV4] HMA support for Mooncake store connector — @ivanium → `nan`
- [#42117](https://github.com/vllm-project/vllm/pull/42117) [bug] AsyncScheduler drops first post-resume token after pause_generation + clear_cache — @hao-aaron → `nan`
- [#43073](https://github.com/vllm-project/vllm/pull/43073) [Model Refactoring] Move deepseek_v4_ops to models/deepseek_v4 [3/N] — @WoosukKwon → `nan`
- [#42946](https://github.com/vllm-project/vllm/pull/42946) [Frontend] Consolidate beam search by BeamSearchMixin. — @noooop → `nan`
- [#41907](https://github.com/vllm-project/vllm/pull/41907) [Docs] Reorganize online serving docs. — @noooop → `nan`
- [#43041](https://github.com/vllm-project/vllm/pull/43041) [Misc] Aligning tokwise pooler heads for consistency — @taneem-ibrahim → `nan`
- [#41354](https://github.com/vllm-project/vllm/pull/41354) [XPU] Use custom op collective behavior  — @chaojun-zhang → `nan`
- [#42626](https://github.com/vllm-project/vllm/pull/42626) [Docs] Add SVG images for pooling models. — @gracie-guo → `nan`
- [#42671](https://github.com/vllm-project/vllm/pull/42671) fix: use keyword arguments for shard_id and expert_id in weight_loade… — @junyanxu → `nan`
- [#43030](https://github.com/vllm-project/vllm/pull/43030) [ci] Route 28 gpu_1_queue tests to h200_35gb queue — @khluu → `nan`
- [#42289](https://github.com/vllm-project/vllm/pull/42289) [Bugfix][KV Connector] Fix SimpleCPUOffloadScheduler TOCTOU between Phase A and Phase B — @qyYue1389 → `nan`

## Top committers (last 7 days)

| Author | Commits |
|---|---:|
| yewentao256 | 12 |
| mgoin | 7 |
| mmangkad | 5 |
| AndreasKaratzas | 4 |
| WoosukKwon | 4 |
| jeejeelee | 4 |
| ivanium | 4 |
| taneem-ibrahim | 4 |
| NickLucche | 3 |
| DarkLight1337 | 3 |

## Merge time trend (last 12 months)

| Month | Median (h) | PRs merged |
|---|---:|---:|
| 2025-06 | 27.2 | 504 |
| 2025-07 | 20.1 | 800 |
| 2025-08 | 20.8 | 878 |
| 2025-09 | 22.5 | 975 |
| 2025-10 | 22.8 | 872 |
| 2025-11 | 27.3 | 902 |
| 2025-12 | 30.7 | 799 |
| 2026-01 | 28.5 | 887 |
| 2026-02 | 27.9 | 864 |
| 2026-03 | 38.2 | 1075 |
| 2026-04 | 69.3 | 809 |
| 2026-05 | 72.7 | 553 |
