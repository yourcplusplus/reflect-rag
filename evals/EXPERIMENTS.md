# 消融实验运行手册（2026-10-25）

配套固化数据集 `golden_dataset_30.yaml`（与 V3-conv/20261010_143849 完全同题同序）。
所有配对比较必须同数据集；新增两个延迟优化 flag（默认关）在消融 run 中**保持关闭**。

> 注意：trace.py 已修复 intent 层双重计数（2026-10-25）。新 run 的
> by_layer["intent"] 是真实值；历史 run 的该值 ≈ 真实 × 2。端到端
> latency_ms 不受影响，跨新旧 run 只比端到端延迟和 MRR/幻觉等指标。

## 实验① 生成层消融（补 V2-30 缺失格）

V3-conv（20261010）跑在 10 月 10 日代码上；为保证同代码配对，V3-30 建议一并重跑。

```bash
# ①a 关 Critique（30 题）
DEFAULT_RETRIEVAL_MODE=hybrid ENABLE_RERANKER=true ENABLE_CRITIQUE=false \
CONTEXT_POOL_CONVERGENCE_ENABLED=true TRACE_ENABLED=true \
python evals/run_eval.py --variant V2-30 --dataset evals/golden_dataset_30.yaml

# ①b 开 Critique（同代码基线重跑）
DEFAULT_RETRIEVAL_MODE=hybrid ENABLE_RERANKER=true ENABLE_CRITIQUE=true \
CONTEXT_POOL_CONVERGENCE_ENABLED=true TRACE_ENABLED=true \
python evals/run_eval.py --variant V3-30r --dataset evals/golden_dataset_30.yaml

# RAGAS 回填（每个 run 各跑一次；<stamp> 换成实际时间戳目录）
python evals/ragas_backfill.py --run evals/results/runs/V2-30/<stamp> --dataset evals/golden_dataset_30.yaml
python evals/ragas_backfill.py --run evals/results/runs/V3-30r/<stamp> --dataset evals/golden_dataset_30.yaml
```

产出箭头：无幻觉(用户感知) X%→90%+、失败归因幻觉类 X%→~3%、MRR 预期持平（层间解耦）。

## 实验②a 100 题批 Faithfulness 回填（不重跑管线）

```bash
for v in V0/20261007_112205 V1/20261007_113831 V2/20261007_115349 V3/20261007_121017; do
  python evals/ragas_backfill.py --run evals/results/runs/$v --metrics faithfulness
done
```

成功（V2→V3 提升）则对外报告中加同集 Faithfulness 箭头；持平则用"收益在幻觉率/引用层"预案。

## 实验③ 二源召回复算（已完成，可随时对新 run 重跑）

```bash
python evals/dual_source_recall.py \
  evals/results/runs/V0/20261007_112205 evals/results/runs/V1/20261007_113831 \
  evals/results/runs/V2/20261007_115349 evals/results/runs/V3/20261007_121017 \
  --save evals/results/dual_source_recall.json
```

已有结果（60 道多源题，双源均进 top5）：V0 73.3% → V1 63.3% → V2 71.7% → V3 70.0%。
分题型：cpc 77.8→66.7→74.1；term_ambiguity 仅 20-30%（最弱类目）。

## token -68% 复算（已完成）

```bash
python evals/context_pool_stats.py \
  --before evals/results/runs/V3-ctxA/20261009_204823 \
  --after  evals/results/runs/V3-conv/20261010_143849
```

结果：注入字符 560,226 → 180,598（-67.8%），contexts 中位 13→7、最大 84→20、cpc 中位 46→14。

## 优化后 V4 对照 run（两个 flag 开）

```bash
DEFAULT_RETRIEVAL_MODE=hybrid ENABLE_RERANKER=true ENABLE_CRITIQUE=true \
CONTEXT_POOL_CONVERGENCE_ENABLED=true TRACE_ENABLED=true \
SKIP_SINGLE_ANSWER_SYNTHESIS=true MERGED_QUERY_UNDERSTANDING=true \
python evals/run_eval.py --variant V4-opt --dataset evals/golden_dataset_30.yaml
```

产出箭头：入口两次 LLM 合一（understanding 层延迟 vs intent+rewrite 之和）、
单答案跳过合成（generation 层调用数 -1/轮）。与 ①b 对比得延迟收益。

## 实验④ 33s→19s 出处考证（待做）

在 `evals/results/traces/` 的 20261006-1007 多跳 trace 中找两个端点；
找不到则在 cpm 子集（`--query-type cross_paper_multi_hop`）用压缩阈值
开关各跑一轮取端点。
