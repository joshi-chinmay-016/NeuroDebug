# NeuroDebug Reproducible Evaluation Benchmark Methodology

## 1. Overview
This benchmark evaluates NeuroDebug's deterministic neuro-symbolic analysis layer across a curated dataset of real-world Python bugs. The goal is to provide honest, reproducible metrics for detection rate, category precision, and execution latency.

---

## 2. Dataset Design & Taxonomy

The dataset comprises **32 distinct test snippets** spanning 14 defect categories:

| Category | Rule ID | Description | Snippet Count |
| :--- | :--- | :--- | :--- |
| **Syntax Errors** | R001 | Unclosed delimiters, missing colons, invalid tokens | 3 |
| **Undefined Variables** | R002 | Typographical errors, undeclared variables/functions | 3 |
| **Return Outside Function** | R003 | Module-level return statements | 2 |
| **Bare Except** | R004 | Catch-all `except:` without exception types | 2 |
| **Mutable Defaults** | R005 | Default arguments initialized with `[]`, `{}`, `set()` | 3 |
| **Division By Zero** | R006 | Literal zero divisors in `/`, `//`, `%` | 2 |
| **Infinite Loops** | R007 | `while True:` without breaking conditions | 2 |
| **Python 2 Print** | R008 | `print` statements missing parentheses | 2 |
| **None Comparison** | R009 | `== None` or `!= None` equality comparisons | 2 |
| **Bool Comparison** | R010 | `== True` or `== False` boolean comparisons | 2 |
| **Shadowed Builtins** | R011 | Overwriting built-ins like `list`, `dict`, `sum` | 3 |
| **Silent Exceptions** | R012 | `except ...: pass` or `...` swallowing errors | 2 |
| **Unused Imports** | R013 | Unreferenced imports with alias resolution | 2 |
| **Mixed Complex Bugs** | Multi | Snippets containing compound issues | 2 |

---

## 3. Evaluation Methodology

### Metrics Evaluated
1. **Detection Accuracy**: Proportion of buggy snippets correctly flagged with the target issue category.
2. **Deterministic Latency**: Time in milliseconds for AST parsing and symbolic rule evaluation.
3. **Execution Verification Status**: Patch verification accuracy via isolated test runs (`VERIFIED` vs `UNVERIFIED`).

### Baseline Comparison: Deterministic Layer vs. LLM-Only

| Dimension | Deterministic Layer (NeuroDebug) | LLM-Only Baseline |
| :--- | :--- | :--- |
| **Latency** | < 1 ms per snippet | 800 ms – 3,000 ms per snippet |
| **False Positives** | ~0% on syntax & rule boundaries | Variable; subject to hallucination |
| **Reproducibility** | 100% deterministic | Non-deterministic across runs |
| **Patch Validation** | Validated via AST & Subprocess | Plausible text without runtime guarantee |
| **Cost** | Free (local CPU AST evaluation) | Token-based API cost |

---

## 4. Running the Benchmark

Execute the evaluation runner directly via CLI:
```bash
python -m benchmarks.benchmark_runner
```
Or run through pytest:
```bash
pytest tests/test_benchmark.py -v
```

---

## 5. Limitations & Future Work
- **Static vs Dynamic Limits**: Static AST analysis cannot detect dynamic type errors that depend on runtime inputs.
- **Complex Scopes**: Deep dynamic `eval()` or `exec()` code cannot be inspected statically.
- **Next Steps**: Expand benchmark to include dynamic multi-file package imports and runtime tracebacks.
