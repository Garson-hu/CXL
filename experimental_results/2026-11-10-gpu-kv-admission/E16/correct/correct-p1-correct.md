## Output correctness, `correct-p1` (48 prompts of 1k-8k + 100 tokens, 32 output tokens, temperature 0)

| path | requests | HTTP 200 | cached tokens / prompt tokens | text identical to the computed reference | TTFT p50 (s) |
|---|---|---|---|---|---|
| compute | 48 | 48 | 0 / 189120 | – | 0.67 |
| host | 48 | 48 | 184320 / 189120 | 47 / 48 | 0.05 |
| gpu | 48 | 48 | 188928 / 189120 | 45 / 48 | 0.03 |
| host+load | 48 | 48 | 184320 / 189120 | 47 / 48 | 1.13 |
| cold+load | 48 | 48 | 0 / 189120 | 45 / 48 | 8.20 |
