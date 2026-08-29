# NeuroDebug AI Evaluation & Benchmark Report

**Evaluation Date/Time:** `2026-08-29T17:10:09.058766+00:00`  
**Dataset Size:** `39 real Python debugging cases`  
**Execution Mode:** `Offline / Deterministic Fallback`  

## Comparative Evaluation Across Architectures

| Architecture Mode | Detection Rate | Patch Validity | Verified Fix Rate | Avg Latency | P95 Latency | LLM Calls/Case |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. AST / Static Analysis Only** | 53.9% (21/39) | 0.0% | 0.0% (0/39) | 0.22 ms | 0.66 ms | 0.0 |
| **3. AST + LLM (Neuro-Symbolic)** | 53.9% (21/39) | 100.0% | 0.0% (0/39) | 0.32 ms | 0.93 ms | 0.0 |
| **4. AST + LLM + Execution Verification** | 53.9% (21/39) | 100.0% | 10.3% (4/39) | 1800.95 ms | 2316.40 ms | 0.0 |

## Category-Level Detection & Verification Breakdown

### Mode: `ast_llm_verify`

| Bug Category | Cases | Detected | Verified Fixes | Detection Rate | Verification Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BareExcept` | 1 | 1 | 0 | 100.0% | 0.0% |
| `BoolComparison` | 1 | 1 | 0 | 100.0% | 0.0% |
| `ComparisonBug` | 2 | 0 | 0 | 0.0% | 0.0% |
| `DivisionByZero` | 3 | 2 | 0 | 66.7% | 0.0% |
| `ExceptionHandling` | 1 | 0 | 0 | 0.0% | 0.0% |
| `InfiniteLoop` | 1 | 0 | 0 | 0.0% | 0.0% |
| `LogicError` | 5 | 0 | 0 | 0.0% | 0.0% |
| `MutabilityBug` | 1 | 0 | 0 | 0.0% | 0.0% |
| `MutableDefaultArgument` | 3 | 3 | 0 | 100.0% | 0.0% |
| `NoneComparison` | 1 | 1 | 0 | 100.0% | 0.0% |
| `ReturnOutsideFunction` | 1 | 1 | 0 | 100.0% | 0.0% |
| `RuntimeError` | 3 | 0 | 0 | 0.0% | 0.0% |
| `ShadowedBuiltin` | 2 | 2 | 0 | 100.0% | 0.0% |
| `SilentException` | 1 | 1 | 0 | 100.0% | 0.0% |
| `SyntaxError` | 4 | 4 | 4 | 100.0% | 100.0% |
| `TypeError` | 2 | 0 | 0 | 0.0% | 0.0% |
| `UndefinedVariable` | 6 | 4 | 0 | 66.7% | 0.0% |
| `UnusedImport` | 1 | 1 | 0 | 100.0% | 0.0% |

## Methodology & Verification Caveats

- **Distinction of Signals:** Detection rate measures whether a defect was surfaced; Patch Validity measures syntax correctness via AST; Verification Rate measures whether the candidate patch executes cleanly and satisfies pytest test assertions.
- **Behavioral Evidence vs Semantic Proof:** Passing a pytest suite constitutes verifiable empirical evidence of defect resolution within tested invariants, not universal semantic proof.
- **Persistence Guarantee:** Results are calculated from actual execution runs without fabrication.