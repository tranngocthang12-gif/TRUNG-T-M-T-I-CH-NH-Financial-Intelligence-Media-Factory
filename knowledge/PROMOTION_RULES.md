# Knowledge Promotion

```text
OBSERVATION → UNVERIFIED → WEAK → SUPPORTED → STRONG → REGIME_SPECIFIC
                                  bằng chứng phủ định ⇒ INVALIDATED
```

- `knowledge/candidates/` — nơi AI được ghi.
- `knowledge/canonical/` — chỉ nhận mục `SUPPORTED` trở lên, đã qua validation, có evidence_refs và `valid_regimes`.
- `AI OUTPUT → VALIDATION → CANONICAL KNOWLEDGE`. Không bao giờ ghi thẳng.
- Mục bị `INVALIDATED` không xóa; chuyển trạng thái và ghi lý do.
