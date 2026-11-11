## Output correctness, `correct-smoke` (8 prompts of 1k-8k + 100 tokens, 32 output tokens, temperature 0)

| path | requests | HTTP 200 | cached tokens / prompt tokens | text identical to the computed reference | TTFT p50 (s) |
|---|---|---|---|---|---|
| compute | 8 | 8 | 0 / 31520 | – | 0.67 |
| host | 8 | 8 | 30720 / 31520 | 8 / 8 | 0.05 |
| gpu | 8 | 8 | 31488 / 31520 | 8 / 8 | 0.03 |
| host+load | 8 | 8 | 30720 / 31520 | 8 / 8 | 6.78 |
| cold+load | 8 | 8 | 0 / 31520 | 8 / 8 | 7.96 |
