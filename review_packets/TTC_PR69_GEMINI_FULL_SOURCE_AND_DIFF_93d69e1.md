# TTC — Gói kiểm định độc lập PR #69 (L-09) — ĐẦY ĐỦ MÃ NGUỒN + UNIFIED DIFF

> **Đây là gói mã nguồn thực, không phải tóm tắt.** Đã đọc 5 tệp trực tiếp bằng GitHub connector tại HEAD `93d69e141f7e0d4ebc2344d8b452a9e22a0dd997`, lấy 5 patch từ PR #69, đối chiếu 4 tệp thêm mới với nội dung trong diff. Không tự tuyên bố L-09 PASS và không can thiệp PR #69.

## Các mốc bắt buộc

- Repository: https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory
- Pull Request: https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/69
- HEAD kiểm tra cố định: `93d69e141f7e0d4ebc2344d8b452a9e22a0dd997`
- Base main: `1d2f5c58acbeb3155118babc92bbb1bc9e06b382`
- Trạng thái khi đóng gói: DRAFT, merged=false.
- Bộ file của PR: đúng **5 tệp**; không sửa dữ liệu raw / engine / Ledger / SAFETY_STATE trong diff.
- Audit kết luận: `NOT_READY` (dữ liệu chưa đủ cho alpha/backtest PIT). Đây KHÔNG phải một kết luận “GỘP ĐƯỢC”.

## Mục lục và fingerprint Git blob

| Tệp | Git blob SHA-1 (GitHub) | Ký tự | Số dòng |
|---|---|---:|---:|
| `.github/workflows/tests.yml` | `d76147c57a64910b8ef4ddda0a4f675f92759535` | 3087 | 67 |
| `reports/PIT-001_20261121.json` | `f83c6cd97962f1d851c88aa555c0b7352de3bd8a` | 30184 | 1046 |
| `reports/PIT-001_20261121.md` | `32f4cd03d8d203a41b3646e4423cccda3431d87d` | 10536 | 125 |
| `tests/test_pit001_audit.py` | `51c918f60e1192766dc823846fe68b2e33f3d545` | 15383 | 306 |
| `tools/pit001_audit.py` | `a332a90fe4bdd6a350add186e1c5a8ea5fab574c` | 42151 | 945 |

**Lưu ý:** Mã hóa tệp UTF-8; SHA blob ở đây là Git SHA-1 của nội dung blob (không phải SHA-256 nguồn tài chính). Không được tự giả định rằng SHA chứng minh đúng ngữ nghĩa.

## Bằng chứng CI đọc từ GitHub

- `L-09 nguoi cham khac nha cung cap (pull_request)`: `failure` — https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44876634245/job/136762656657
- `Test bat buoc (chan merge)`: `success` — https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44876634219/job/136762656424
- `L-09 nguoi cham khac nha cung cap (pull_request_target)`: `failure` — https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44876631867/job/136762651206

Báo cáo kiểm thử trên HEAD: 319 passed, 68 subtests passed, 79 warnings; audit chạy hai lần cùng đầu ra (theo log workflow). Người chấm phải tự đối chiếu phép thử với mã, không dùng CI xanh làm thay phản biện.

## Yêu cầu cho Gemini (Google)

Đọc đầy đủ 5 tệp bên dưới, đối chiếu unified diff và xem xét: `conclude` fail-closed; cổng READY có thể đạt bằng bằng chứng hợp lệ hay không; `UNKNOWN` có phủ định `READY` đúng; không tin comment/string literals khi AST; `check_engine_mode`, `check_continuity`, `check_price_window_coverage`, `check_unverified_chain` và `check_microstructure`; ngày công bố so với phút quyết định; ranh giới `source_status`; kiểm tính chỉ đọc và tính xác định; audit có tự xưng PIT khi không có vintage không; sự khớp giữa JSON và mã. Phân biệt “bảo thủ an toàn” với “không có lộ trình đạt READY”.

Nếu còn blocker cụ thể: `REQUEST_CHANGES` kèm đường dẫn, dòng, ví dụ/tái lập và test tối thiểu. Nếu chưa có dữ liệu buộc phải đọc thêm thì `BLOCKED` (nêu chính xác). Chỉ khi đủ điều kiện mới `GỘP ĐƯỢC` kèm HEAD SHA. Không sửa mã, không merge, không điền `reviewed_by` và không ký thay Owner.

---

# PHẦN A — NỘI DUNG NGUYÊN VĂN CỦA CẢ 5 TỆP Ở HEAD

## .github/workflows/tests.yml

**Git blob SHA**: `d76147c57a64910b8ef4ddda0a4f675f92759535`  ·  **Số dòng:** 67

~~~~yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  issues: read

jobs:
  gate:
    name: Test bat buoc (chan merge)
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      UNITTEST: "test_laws_validate test_ledger_compat test_ledger_resolution test_knowledge_notes test_governance test_timing_lock test_source_original test_directional_accuracy test_measurement_integration test_scorecard_refresh test_b1_engine_bridge test_verified_adjust test_corporate_action_evidence test_corporate_action_evidence_2026h2 test_vn30_history test_forecast_candidates test_pit001_audit"
      SCRIPTS: "test_no_lookahead test_adjustment test_ingest_errors test_ledger_pipeline test_quality_gate test_llm_review_budget"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # can lich su de kiem so chi-ghi-them so voi commit goc
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Cai thu vien
        run: pip install -r requirements.txt pytest
      - name: Moi tep tests/test_*.py deu nam trong CI (khong bo sot test moi)
        run: |
          for f in tests/test_*.py; do
            n=$(basename "$f" .py)
            echo " $UNITTEST $SCRIPTS " | grep -q " $n " || { echo "Tep $f chua duoc dua vao tests.yml"; exit 1; }
          done
      - name: PIT-001 replay deterministic (read-only)
        run: |
          python tools/pit001_audit.py > /tmp/pit001_a.json
          python tools/pit001_audit.py > /tmp/pit001_b.json
          cmp /tmp/pit001_a.json /tmp/pit001_b.json
          python -c 'import json; x=json.load(open("/tmp/pit001_a.json")); print("PIT-001:",x["conclusion"],"findings=",len(x["findings"]))'
      - name: Test dang unittest (luat, Ledger, phan dinh, so thu L-06)
        run: python -m pytest -q $(for n in $UNITTEST; do printf "tests/%s.py " "$n"; done)
      - name: Test dang script cu cua engine (moi tep mot tien trinh rieng, khong dung chung TTC_HOME)
        run: |
          for n in $SCRIPTS; do
            echo "=== $n"; python -m "tests.$n" || exit 1
          done
      - name: Kiem tra thu tu test (adjustment / governance)
        run: |
          python -m pytest -q tests/test_adjustment.py tests/test_governance.py
          python -m pytest -q tests/test_governance.py tests/test_adjustment.py
      - name: B1 read-only raw price evidence (not official verification)
        run: python tools/b1_price_evidence.py
      - name: Kiem cau truc bo nao
        run: python tools/validate.py
      - name: So chi-ghi-them + doi chieu Issue that tren GitHub (L-05)
        env:
          GITHUB_TOKEN: ${{ github.token }}
          BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}
        run: python tools/ledger_audit.py --base "$BASE_SHA" --github
      - name: Test khong duoc sua tep nao cua kho
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            echo "Test da sua/tao tep trong kho:"; git status --porcelain; exit 1
          fi
~~~~

## reports/PIT-001_20261121.json

**Git blob SHA**: `f83c6cd97962f1d851c88aa555c0b7352de3bd8a`  ·  **Số dòng:** 1046

~~~~json
{
  "alpha_claim": false,
  "conclusion": "NOT_READY",
  "conclusion_reason": "Kiểm tra bắt buộc FAIL/không hợp lệ: ADR0008_SCHEMA, CONFIG_VS_EVIDENCED_BASKET, CORPORATE_ACTION_VERIFICATION, ENGINE_UNIVERSE_MODE, PRICE_WINDOW_COVERAGE, TICKER_PRESENCE, UNIVERSE_COVERAGE, UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
  "eligible_window": null,
  "findings": [
    {
      "evidence": {
        "matched": [
          {
            "bytes": 1045,
            "path": "data/evidence/vn30_reviews/hose-2388633/news.json",
            "sha256": "76d1b776e0fc92199cf9249e0cb1a69e5aa9e7d724db15462d75e0f05ff6956a",
            "source_id": "hose-2388633-news"
          },
          {
            "bytes": 687177,
            "path": "data/evidence/vn30_reviews/hose-2388633/20250716 CBTT-Danh muc thanh phan HOSE-Index thang 7.2025.pdf",
            "sha256": "8573aaed26f2f087ac30567b1c943e4112a85f6c3efc6a57faa80b7b3f020eae",
            "source_id": "hose-2388633"
          },
          {
            "bytes": 1061,
            "path": "data/evidence/vn30_reviews/hose-2432828/news.json",
            "sha256": "90e46883d3b0ef72c0ebba8ba0165ba338cea3c7735ed92ad0b9e832c5558ba3",
            "source_id": "hose-2432828-news"
          },
          {
            "bytes": 710524,
            "path": "data/evidence/vn30_reviews/hose-2432828/21012026 CBTT Danh sach thanh phan HOSE-Index thang 1.2026 update.pdf",
            "sha256": "67f0087e74cd21c1f24b364403bf176db8a39732ef65847d56ea85b316fb6f7f",
            "source_id": "hose-2432828"
          },
          {
            "bytes": 11616,
            "path": "data/evidence/vn30_reviews/hose-2460387/news.json",
            "sha256": "d883018f2f93fc26fec2aa70bff8e9e06338c335ae49ba66fda0cdccad796e90",
            "source_id": "hose-2460387"
          },
          {
            "bytes": 1052,
            "path": "data/evidence/vn30_reviews/hose-2479382/news.json",
            "sha256": "cf574c5e63143d5b74bc062f03bbf91ca276164f9c8d7d5e15f4c242f93f675b",
            "source_id": "hose-2479382-news"
          },
          {
            "bytes": 737357,
            "path": "data/evidence/vn30_reviews/hose-2479382/15072026 CBTT - Danh muc thanh phan HOSE-Index thang 7.2026.pdf",
            "sha256": "441799b3afbc4f29f8b53ce6ef3b500b9121a4d032ca4cfeb1d4aa6e14407879",
            "source_id": "hose-2479382"
          },
          {
            "bytes": 1092,
            "path": "data/evidence/vn30_reviews/hose-2510691/news.json",
            "sha256": "fe6d4d88fd6285f799bedd33f9f31535e5d40051cf283790ed05d8d0e6937ed3",
            "source_id": "hose-2510691-news"
          },
          {
            "bytes": 416988,
            "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
            "sha256": "ca0c5ee6fc20234ea7c0dff93f0b0a5eac4bb16df93f9b36268c0ffadaa567d4",
            "source_id": "hose-2510691"
          }
        ]
      },
      "id": "PROVENANCE_HASH",
      "status": "PASS",
      "summary": "Mọi tệp kê trong manifest VN30 khớp SHA-256 và số byte. Việc này không xác minh nội dung."
    },
    {
      "evidence": {
        "checked": 9
      },
      "id": "PUBLICATION_BEFORE_USE",
      "status": "PASS",
      "summary": "Với mọi tài liệu có đủ hai ngày, ngày công bố theo giờ Việt Nam không sau ngày hiệu lực."
    },
    {
      "evidence": {
        "decision_time_local": null
      },
      "id": "DECISION_TIME_OF_KNOWLEDGE",
      "status": "INCONCLUSIVE",
      "summary": "Chưa đăng ký giờ ra quyết định theo ngày giao dịch (research.decision_time_local). So published_on <= effective_date không chứng minh có thể dùng ngay trong phiên."
    },
    {
      "evidence": {
        "states": [
          {
            "effective_date": "2025-08-04",
            "members": [
              "ACB",
              "BCM",
              "BID",
              "CTG",
              "DGC",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MSN",
              "MWG",
              "PLX",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TPB",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VRE"
            ]
          },
          {
            "effective_date": "2026-02-02",
            "members": [
              "ACB",
              "BID",
              "CTG",
              "DGC",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MSN",
              "MWG",
              "PLX",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TPB",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ]
          },
          {
            "effective_date": "2026-05-13",
            "members": [
              "ACB",
              "BID",
              "BSR",
              "CTG",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MSN",
              "MWG",
              "PLX",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TPB",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ]
          },
          {
            "effective_date": "2026-08-03",
            "members": [
              "ACB",
              "BID",
              "BSR",
              "CTG",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MCH",
              "MSN",
              "MWG",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TCX",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ]
          }
        ]
      },
      "id": "CSV_INTERNAL",
      "status": "PASS",
      "summary": "CSV dựng lại được các mốc, mỗi mốc đúng 30 mã. Không suy ra thành phần trước mốc đầu tiên."
    },
    {
      "evidence": {
        "actual_columns": [
          "effective_date",
          "ticker",
          "action",
          "source_id"
        ],
        "adr0008_columns": [
          "effective_date",
          "ticker",
          "change",
          "source_url",
          "source_status"
        ]
      },
      "id": "ADR0008_SCHEMA",
      "status": "FAIL",
      "summary": "CSV không theo khuôn ADR-0008 (effective_date,ticker,change,source_url,source_status). Không được tự ghi đè CSV trong PIT-001. Khuôn đang khóa bởi test là cột action/source_id."
    },
    {
      "evidence": {
        "first_evidence_date": "2025-08-04",
        "research_start": "2016-01-01",
        "uncovered_until_exclusive": "2025-08-04"
      },
      "id": "UNIVERSE_COVERAGE",
      "status": "FAIL",
      "summary": "Lịch sử thành phần đã ghim không phủ từ ngày đầu cửa sổ nghiên cứu. Không tự điền các kỳ thiếu."
    },
    {
      "evidence": {
        "applies": true,
        "first_evidence_date": "2025-08-04",
        "research_start": "2016-01-01"
      },
      "id": "MEMBERSHIP_BEFORE_FIRST_EVIDENCE",
      "status": "UNKNOWN",
      "summary": "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN."
    },
    {
      "evidence": {
        "gaps": [
          {
            "after": "2025-08-04",
            "before": "2026-02-02",
            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
          },
          {
            "after": "2026-02-02",
            "before": "2026-05-13",
            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
          },
          {
            "after": "2026-05-13",
            "before": "2026-08-03",
            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
          }
        ],
        "names_copied_from_other_document": [
          {
            "effective_date": "2025-08-04",
            "names_copied_from": "hose-2388633",
            "source_id": "hose-2388633-news"
          },
          {
            "effective_date": "2026-02-02",
            "names_copied_from": "hose-2432828",
            "source_id": "hose-2432828-news"
          },
          {
            "effective_date": "2026-05-13",
            "names_copied_from": "hose-2432828",
            "source_id": "hose-2460387"
          },
          {
            "effective_date": "2026-08-03",
            "names_copied_from": "hose-2479382",
            "source_id": "hose-2479382-news"
          },
          {
            "effective_date": "2026-11-16",
            "names_copied_from": "hose-2510691",
            "source_id": "hose-2510691-news"
          }
        ]
      },
      "id": "CONTINUITY_BETWEEN_REVIEWS",
      "status": "UNKNOWN",
      "summary": "Khoảng giữa các mốc đã ghim không được coi là đã chứng minh liên tục. Bản tin chép danh sách từ PDF kỳ trước không phải là in lại đủ 30 mã."
    },
    {
      "evidence": {
        "universe_basis": "CURRENT"
      },
      "id": "ENGINE_UNIVERSE_MODE",
      "status": "FAIL",
      "summary": "Cấu hình khai CURRENT: không thể chứng nhận chọn universe theo từng ngày."
    },
    {
      "evidence": {
        "config_count": 30,
        "csv_state_as_of": "2026-08-03",
        "evidence_count": 30,
        "in_config_not_in_csv_state": [
          "BCM",
          "BVH",
          "PLX",
          "POW",
          "TPB"
        ],
        "in_csv_state_not_in_config": [
          "BSR",
          "LPB",
          "MCH",
          "TCX",
          "VPL"
        ]
      },
      "id": "CONFIG_VS_EVIDENCED_BASKET",
      "status": "FAIL",
      "summary": "Danh sách cố định trong config không trùng rổ dựng từ CSV tại mốc cuối. Đây là lệch thành phần, không phải khuyến nghị giao dịch."
    },
    {
      "evidence": {
        "members_ever_in_csv": [
          "ACB",
          "BCM",
          "BID",
          "BSR",
          "CTG",
          "DGC",
          "FPT",
          "GAS",
          "GVR",
          "HDB",
          "HPG",
          "LPB",
          "MBB",
          "MCH",
          "MSN",
          "MWG",
          "PLX",
          "SAB",
          "SHB",
          "SSB",
          "SSI",
          "STB",
          "TCB",
          "TCX",
          "TPB",
          "VCB",
          "VHM",
          "VIB",
          "VIC",
          "VJC",
          "VNM",
          "VPB",
          "VPL",
          "VRE"
        ],
        "members_without_any_price_row": [
          "BSR",
          "DGC",
          "LPB",
          "MCH",
          "TCX",
          "VPL"
        ],
        "paths": [
          "data/store/prices.csv.gz",
          "data/store/prices/2026-11.csv"
        ],
        "price_first": "2016-01-04",
        "price_last": "2026-11-20",
        "price_rows": 73402,
        "price_tickers": [
          "ACB",
          "BCM",
          "BID",
          "BVH",
          "CTG",
          "FPT",
          "GAS",
          "GVR",
          "HDB",
          "HPG",
          "MBB",
          "MSN",
          "MWG",
          "PLX",
          "POW",
          "SAB",
          "SHB",
          "SSB",
          "SSI",
          "STB",
          "TCB",
          "TPB",
          "VCB",
          "VHM",
          "VIB",
          "VIC",
          "VJC",
          "VNM",
          "VPB",
          "VRE"
        ],
        "priced_but_never_in_pinned_baskets": [
          "BVH",
          "POW"
        ]
      },
      "id": "TICKER_PRESENCE",
      "status": "FAIL",
      "summary": "Có mã từng nằm trong rổ ghim nhưng không có dòng giá."
    },
    {
      "evidence": {
        "feature_lookback": 121,
        "horizon_days": 20,
        "min_distinct_sessions_for_individual_ticker": 122,
        "missing_dates_on_observed_market_calendar": [
          {
            "effective_date": "2025-08-04",
            "examples": [
              "2025-08-04",
              "2025-08-05",
              "2025-08-06"
            ],
            "missing_session_count": 130,
            "ticker": "DGC"
          },
          {
            "effective_date": "2025-08-04",
            "examples": [
              "2025-08-04",
              "2025-08-05",
              "2025-08-06"
            ],
            "missing_session_count": 130,
            "ticker": "LPB"
          },
          {
            "effective_date": "2026-02-02",
            "examples": [
              "2026-02-02",
              "2026-02-03",
              "2026-02-04"
            ],
            "missing_session_count": 72,
            "ticker": "DGC"
          },
          {
            "effective_date": "2026-02-02",
            "examples": [
              "2026-02-02",
              "2026-02-03",
              "2026-02-04"
            ],
            "missing_session_count": 72,
            "ticker": "LPB"
          },
          {
            "effective_date": "2026-02-02",
            "examples": [
              "2026-02-02",
              "2026-02-03",
              "2026-02-04"
            ],
            "missing_session_count": 72,
            "ticker": "VPL"
          },
          {
            "effective_date": "2026-05-13",
            "examples": [
              "2026-05-13",
              "2026-05-14",
              "2026-05-15"
            ],
            "missing_session_count": 58,
            "ticker": "BSR"
          },
          {
            "effective_date": "2026-05-13",
            "examples": [
              "2026-05-13",
              "2026-05-14",
              "2026-05-15"
            ],
            "missing_session_count": 58,
            "ticker": "LPB"
          },
          {
            "effective_date": "2026-05-13",
            "examples": [
              "2026-05-13",
              "2026-05-14",
              "2026-05-15"
            ],
            "missing_session_count": 58,
            "ticker": "VPL"
          },
          {
            "effective_date": "2026-08-03",
            "examples": [
              "2026-08-03",
              "2026-08-04",
              "2026-08-05"
            ],
            "missing_session_count": 80,
            "ticker": "BSR"
          },
          {
            "effective_date": "2026-08-03",
            "examples": [
              "2026-08-03",
              "2026-08-04",
              "2026-08-05"
            ],
            "missing_session_count": 80,
            "ticker": "LPB"
          },
          {
            "effective_date": "2026-08-03",
            "examples": [
              "2026-08-03",
              "2026-08-04",
              "2026-08-05"
            ],
            "missing_session_count": 80,
            "ticker": "MCH"
          },
          {
            "effective_date": "2026-08-03",
            "examples": [
              "2026-08-03",
              "2026-08-04",
              "2026-08-05"
            ],
            "missing_session_count": 80,
            "ticker": "TCX"
          },
          {
            "effective_date": "2026-08-03",
            "examples": [
              "2026-08-03",
              "2026-08-04",
              "2026-08-05"
            ],
            "missing_session_count": 80,
            "ticker": "VPL"
          }
        ],
        "missing_tickers": [
          "BSR",
          "DGC",
          "LPB",
          "MCH",
          "TCX",
          "VPL"
        ],
        "official_exchange_calendar_verified": false,
        "short_series": [
          {
            "distinct_sessions": 0,
            "ticker": "BSR"
          },
          {
            "distinct_sessions": 0,
            "ticker": "DGC"
          },
          {
            "distinct_sessions": 0,
            "ticker": "LPB"
          },
          {
            "distinct_sessions": 0,
            "ticker": "MCH"
          },
          {
            "distinct_sessions": 0,
            "ticker": "TCX"
          },
          {
            "distinct_sessions": 0,
            "ticker": "VPL"
          }
        ]
      },
      "id": "PRICE_WINDOW_COVERAGE",
      "status": "FAIL",
      "summary": "Thiếu mã, chuỗi quá ngắn hoặc thiếu ngày giá trong phiên có dữ liệu cho mã khác. Chưa xét liệu lịch phiên suy từ kho có đầy đủ hay không."
    },
    {
      "evidence": {
        "unverified": [
          {
            "csv_ex_date": "2024-06-11",
            "csv_ratio": "2.0",
            "csv_source_status": "CAN_DOI_CHIEU",
            "csv_type": "stock_dividend",
            "dates_match": false,
            "evidence_source_id": "hose-1705374",
            "official_ex_date": "2024-06-20",
            "published_at": null,
            "published_at_status": "CHUA_XAC_MINH",
            "ticker": "TCB"
          },
          {
            "csv_ex_date": "2025-03-03",
            "csv_ratio": "1.495",
            "csv_source_status": "CAN_DOI_CHIEU",
            "csv_type": "stock_dividend",
            "dates_match": false,
            "evidence_source_id": "hose-1753594",
            "official_ex_date": "2025-03-12",
            "published_at": null,
            "published_at_status": "CHUA_XAC_MINH",
            "ticker": "VCB"
          }
        ]
      },
      "id": "CORPORATE_ACTION_VERIFICATION",
      "status": "FAIL",
      "summary": "Có sự kiện quyền nhập tay chưa ở trạng thái DA_DOI_CHIEU. Không xác nhận sự kiện từ bước nhảy giá. Ngày trên CSV lệch ngày official_ex_date của bản HOSE đã ghim thì vẫn là chưa xác minh, kể cả khi hash PDF khớp."
    },
    {
      "evidence": {
        "behavioral_proof_verified_gate": false,
        "build_events_ast_mentions_source_status": false,
        "load_market_ast_mentions_verified_function": false,
        "load_market_calls_adjust_build_events": true,
        "unverified_manual_rows": 2
      },
      "id": "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
      "status": "FAIL",
      "summary": "Có sự kiện chưa xác minh, load_market gọi build_events, nhưng hàm build_events không đọc source_status. Không được cho vào verified-adjusted khi chưa có cổng hành vi."
    },
    {
      "evidence": {
        "documents": [
          {
            "content_status": "PASS",
            "effective_date": "2025-08-04",
            "expected_count": 30,
            "other_index_headings": [],
            "parsed_count": 30,
            "parsed_tickers": [
              "ACB",
              "BCM",
              "BID",
              "CTG",
              "DGC",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MSN",
              "MWG",
              "PLX",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TPB",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VRE"
            ],
            "path": "data/evidence/vn30_reviews/hose-2388633/20250716 CBTT-Danh muc thanh phan HOSE-Index thang 7.2025.pdf",
            "pdf_contains_effective_date_dmy": false,
            "source_id": "hose-2388633",
            "vn30_heading_pages": [
              {
                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
                "page": 1
              }
            ]
          },
          {
            "content_status": "PASS",
            "effective_date": "2026-02-02",
            "expected_count": 30,
            "other_index_headings": [],
            "parsed_count": 30,
            "parsed_tickers": [
              "ACB",
              "BID",
              "CTG",
              "DGC",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MSN",
              "MWG",
              "PLX",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TPB",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ],
            "path": "data/evidence/vn30_reviews/hose-2432828/21012026 CBTT Danh sach thanh phan HOSE-Index thang 1.2026 update.pdf",
            "pdf_contains_effective_date_dmy": false,
            "source_id": "hose-2432828",
            "vn30_heading_pages": [
              {
                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
                "page": 1
              }
            ]
          },
          {
            "content_status": "PASS",
            "effective_date": "2026-08-03",
            "expected_count": 30,
            "other_index_headings": [],
            "parsed_count": 30,
            "parsed_tickers": [
              "ACB",
              "BID",
              "BSR",
              "CTG",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MCH",
              "MSN",
              "MWG",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TCX",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ],
            "path": "data/evidence/vn30_reviews/hose-2479382/15072026 CBTT - Danh muc thanh phan HOSE-Index thang 7.2026.pdf",
            "pdf_contains_effective_date_dmy": false,
            "source_id": "hose-2479382",
            "vn30_heading_pages": [
              {
                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN30",
                "page": 1
              }
            ]
          },
          {
            "content_status": "PASS",
            "effective_date": "2026-11-16",
            "expected_count": 30,
            "other_index_headings": [
              {
                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
                "page": 2
              },
              {
                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
                "page": 4
              },
              {
                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
                "page": 6
              }
            ],
            "parsed_count": 30,
            "parsed_tickers": [
              "ACB",
              "BID",
              "BSR",
              "CTG",
              "FPT",
              "GAS",
              "GVR",
              "HDB",
              "HPG",
              "LPB",
              "MBB",
              "MCH",
              "MSN",
              "MWG",
              "SAB",
              "SHB",
              "SSB",
              "SSI",
              "STB",
              "TCB",
              "TCX",
              "VCB",
              "VHM",
              "VIB",
              "VIC",
              "VJC",
              "VNM",
              "VPB",
              "VPL",
              "VRE"
            ],
            "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
            "pdf_contains_effective_date_dmy": false,
            "source_id": "hose-2510691",
            "vn30_heading_pages": [
              {
                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
                "page": 1
              }
            ]
          }
        ],
        "hose_2510691": {
          "content_status": "PASS",
          "effective_date": "2026-11-16",
          "expected_count": 30,
          "other_index_headings": [
            {
              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
              "page": 2
            },
            {
              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
              "page": 4
            },
            {
              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
              "page": 6
            }
          ],
          "parsed_count": 30,
          "parsed_tickers": [
            "ACB",
            "BID",
            "BSR",
            "CTG",
            "FPT",
            "GAS",
            "GVR",
            "HDB",
            "HPG",
            "LPB",
            "MBB",
            "MCH",
            "MSN",
            "MWG",
            "SAB",
            "SHB",
            "SSB",
            "SSI",
            "STB",
            "TCB",
            "TCX",
            "VCB",
            "VHM",
            "VIB",
            "VIC",
            "VJC",
            "VNM",
            "VPB",
            "VPL",
            "VRE"
          ],
          "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
          "pdf_contains_effective_date_dmy": false,
          "source_id": "hose-2510691",
          "vn30_heading_pages": [
            {
              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
              "page": 1
            }
          ]
        }
      },
      "id": "PDF_VN30_CONTENT",
      "status": "PASS",
      "summary": "Mỗi PDF đã ghim có mục VN30 và danh sách đọc được trùng members_after. Ngày hiệu lực có thể nằm ở tin, không nằm trong PDF."
    },
    {
      "evidence": {
        "news_contains_effective_date": true,
        "news_title": "HOSE: Cập nhật danh mục cổ phiếu thành phần của Chỉ số quy mô VNAllshare  kỳ tháng 10/2026",
        "other_index_headings": [
          {
            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
            "page": 2
          },
          {
            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
            "page": 4
          },
          {
            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
            "page": 6
          }
        ],
        "pdf_contains_effective_date": false,
        "pdf_membership_matches": true
      },
      "id": "HOSE_2510691_SCOPE",
      "status": "PASS",
      "summary": "hose-2510691 là PDF tên VNAllshare kỳ 10/2026 và có mục «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30» in đủ 30 mã, trùng members_after. Ngày hiệu lực 16/11/2026 đọc từ tin HOSE đã ghim, không thấy dạng 16/11/2026 trong chữ PDF. Các mục chỉ số khác trong cùng tệp không phải rổ VN30."
    },
    {
      "evidence": {
        "documents": [
          {
            "effective_date": "2025-08-04",
            "path": "data/evidence/vn30_reviews/hose-2388633/news.json",
            "present_in_announcement_summary": true,
            "source_id": "hose-2388633-news",
            "status": "PASS",
            "token": "04/08/2025"
          },
          {
            "effective_date": "2026-02-02",
            "path": "data/evidence/vn30_reviews/hose-2432828/news.json",
            "present_in_announcement_summary": true,
            "source_id": "hose-2432828-news",
            "status": "PASS",
            "token": "02/02/2026"
          },
          {
            "effective_date": "2026-05-13",
            "path": "data/evidence/vn30_reviews/hose-2460387/news.json",
            "present_in_announcement_summary": true,
            "source_id": "hose-2460387",
            "status": "PASS",
            "token": "13/05/2026"
          },
          {
            "effective_date": "2026-08-03",
            "path": "data/evidence/vn30_reviews/hose-2479382/news.json",
            "present_in_announcement_summary": true,
            "source_id": "hose-2479382-news",
            "status": "PASS",
            "token": "03/08/2026"
          },
          {
            "effective_date": "2026-11-16",
            "path": "data/evidence/vn30_reviews/hose-2510691/news.json",
            "present_in_announcement_summary": true,
            "source_id": "hose-2510691-news",
            "status": "PASS",
            "token": "16/11/2026"
          }
        ]
      },
      "id": "NEWS_EFFECTIVE_DATE_TEXT",
      "status": "PASS",
      "summary": "Các bản tin đã ghim có ngày hiệu lực trong phần summary, không chỉ metadata."
    },
    {
      "evidence": {
        "costs": {
          "buy_fee": 0.0015,
          "dividend_tax": 0.05,
          "sell_fee": 0.0015,
          "sell_tax": 0.001,
          "slippage": 0.001
        },
        "lot_size": 100,
        "paper_trade_rows": null,
        "price_limit": 0.07
      },
      "id": "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
      "status": "INCONCLUSIVE",
      "summary": "Phí, thuế, trượt giá, lô và biên độ là giả định trong config hoặc hằng số giấy. Chưa có đối chiếu lệnh khớp thật. Không chứng minh được khả năng khớp."
    }
  ],
  "first_pinned_membership_date": "2025-08-04",
  "read_only": true,
  "research_start": "2016-01-01",
  "tool": "pit001_audit"
}
~~~~

## reports/PIT-001_20261121.md

**Git blob SHA**: `32f4cd03d8d203a41b3646e4423cccda3431d87d`  ·  **Số dòng:** 125

~~~~markdown
# PIT-001 — Kiểm toán đúng thời điểm dữ liệu nghiên cứu VN30

- Ngày chạy: 2026-11-21
- Cây đọc: `main` `1d2f5c58acbeb3155118babc92bbb1bc9e06b382` cộng công cụ kiểm toán của PR này. Công cụ không sửa dữ liệu gốc.
- Lệnh: `python3 tools/pit001_audit.py`
- Máy đọc được: [reports/PIT-001_20261121.json](PIT-001_20261121.json)
- Kết luận dùng dữ liệu này cho nghiên cứu alpha đáng tin: **NOT_READY**
- Không tuyên bố vượt thị trường, vượt nhà đầu tư, hay có model ACTIVE.

Hash SHA-256 khớp chứng minh byte không đổi. Nó không chứng minh nội dung đúng. Nội dung chỉ được ghi PASS khi chữ trong PDF hoặc tin đã ghim được đọc ra và đối được với manifest.

## Kết quả kiểm toán

| Hạng mục | Trạng thái | Việc đã thấy |
|---|---|---|
| PROVENANCE_HASH | PASS | Mọi tệp trong `data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json` khớp hash và số byte |
| PUBLICATION_BEFORE_USE | PASS | Ngày công bố trên manifest, theo giờ Việt Nam, không sau ngày hiệu lực đã khai |
| DECISION_TIME_OF_KNOWLEDGE | INCONCLUSIVE | Chưa đăng ký giờ quyết định tại mỗi phiên; ngày hiệu lực và ngày công bố không đủ để chứng minh thông tin đã biết trước thời điểm quyết định. |
| NEWS_EFFECTIVE_DATE_TEXT | PASS | Năm tin JSON đều chứa đúng chuỗi ngày hiệu lực (04/08/2025, 02/02/2026, 13/05/2026, 03/08/2026, 16/11/2026) |
| PDF_VN30_CONTENT | PASS | Bốn PDF có mục thành phần VN30; tập mã đọc được trùng `members_after` |
| HOSE_2510691_SCOPE | PASS | Xem mục riêng bên dưới |
| CSV_INTERNAL | PASS | 38 dòng ADD/REMOVE dựng được bốn mốc, mỗi mốc 30 mã, mốc đầu 2025-08-04 |
| ADR0008_SCHEMA | FAIL | CSV đang là `effective_date,ticker,action,source_id`, không phải khuôn ADR-0008 `change,source_url,source_status`. Không ghi đè CSV |
| UNIVERSE_COVERAGE | FAIL | `config.yaml` `data.start` là 2016-01-01; bản gốc đầu tiên là 2025-08-04 |
| MEMBERSHIP_BEFORE_FIRST_EVIDENCE | UNKNOWN | Trước 2025-08-04 không suy thành phần |
| CONTINUITY_BETWEEN_REVIEWS | UNKNOWN | Không có tệp nào khác trong các khoảng giữa mốc không chứng minh rổ đứng yên |
| ENGINE_UNIVERSE_MODE | FAIL | `universe_basis: CURRENT`. `engine/data.py` nạp theo `CFG["universe"]`, không đọc `data/vn30_history.csv` |
| CONFIG_VS_EVIDENCED_BASKET | FAIL | Lệch với rổ dựng tại mốc CSV cuối (2026-08-03, và trùng mục PDF 2026-11-16) |
| TICKER_PRESENCE | FAIL | Kho giá 2016-01-04 đến 2026-11-20, 73402 dòng; thiếu mã từng trong rổ đã ghim. Chỉ đo có/không có dòng giá, không gọi là đủ phiên. |
| PRICE_WINDOW_COVERAGE | FAIL | Thiếu mã và phiên dữ liệu ở các mốc đã ghim; lịch phiên chính thức và vintage giá vẫn chưa xác minh. Không được PASS chỉ vì mỗi mã có một dòng. |
| CORPORATE_ACTION_VERIFICATION | FAIL | TCB và VCB vẫn `CAN_DOI_CHIEU`; ngày CSV lệch `official_ex_date`; `published_at` null |
| UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN | FAIL | `load_market` gọi `adjust.build_events`. Hàm đó không đọc `source_status` trước khi có thể gán `APPLIED` |
| MARKET_MICROSTRUCTURE_ASSUMPTIONS | INCONCLUSIVE | Phí, thuế, trượt giá, lô 100, biên độ 0.07 là giả định. Không có `paper/trades.csv` để chứng minh lệnh khớp |

`universe_basis` không được chuyển sang `HISTORICAL` trong PR này. `engine/adjust.py`, `engine/research.py` và `config.yaml` không đổi. Bộ audit được siết cổng sau phản biện trên PR #69.

## hose-2510691 (hiệu lực khai 2026-11-16)

Tài liệu là PDF tên `II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf`, SHA-256 `ca0c5ee6fc20234ea7c0dff93f0b0a5eac4bb16df93f9b36268c0ffadaa567d4`, 416988 byte. Tin HOSE id 2510691 có tiêu đề cập nhật danh mục chỉ số quy mô VNAllshare.

Đã đọc chữ PDF, không chỉ đọc tên tệp:

- Trang 1, dòng tiêu đề: «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30», kỳ tháng 10/2026.
- Đúng 30 mã, trùng `members_after`: ACB, BID, BSR, CTG, FPT, GAS, GVR, HDB, HPG, LPB, MBB, MCH, MSN, MWG, SAB, SHB, SSB, SSI, STB, TCB, TCX, VCB, VHM, VIB, VIC, VJC, VNM, VPB, VPL, VRE.
- Cùng tệp còn mục VNMIDCAP (trang 2), VN100 (trang 4), VNSMALLCAP (trang 6). Những mục đó không phải rổ VN30.
- Chữ PDF không chứa `16/11/2026`. Ngày hiệu lực nằm trong tin `hose-2510691-news`: các chỉ số quy mô VNAllshare có hiệu lực vào ngày 16/11/2026.
- CSV không có dòng ADD/REMOVE ngày 2026-11-16. Rổ dựng sau mốc 2026-08-03 đã trùng 30 mã này, nên không có dòng không có nghĩa là thiếu bản gốc của kỳ này.

`reports/G1_DATA_SPRINT0_20261120/A3_LO_HONG.md` nói tệp này không phải kỳ VN30 và chưa có bản gốc rổ sau 2026-08-03. Câu đó không đúng với mục VN30 trong PDF. `reports/VN30_UNIVERSE_DIFF_20261119.md` mô tả đúng mục và đúng 30 mã. Báo cáo cũ không bị sửa trong PR này.

Ba PDF kỳ trước cũng đọc được mục thành phần (tiêu đề «CÔNG BỐ THÔNG TIN…», không phải «CẬP NHẬT…») và trùng `members_after`. Ngày hiệu lực của chúng cũng không nằm trong chữ PDF; chúng nằm trong tin JSON đã ghim. Tin `hose-2460387` xác nhận VN30 loại DGC, thêm BSR, hiệu lực 13/05/2026, và không in lại đủ 30 mã. 28 mã còn lại trên manifest được chép từ PDF kỳ 01/2026. Đó không phải xác minh độc lập cả rổ tại 2026-05-13.

## Lệch rổ và lỗ giá

Rổ config so với rổ đã dựng tại mốc cuối:

- Có trong config, không còn trong rổ đó: BCM, BVH, PLX, POW, TPB.
- Có trong rổ đó, không có trong config: BSR, LPB, MCH, TCX, VPL.

Mã từng vào rổ đã ghim nhưng không có dòng giá: BSR, DGC, LPB, MCH, TCX, VPL.

Mã có giá nhưng không nằm trong bất kỳ rổ đã ghim: BVH, POW.

Không điền giá và không điền thành phần cho các kỳ chưa có PDF. Các kỳ từ 2016 đến trước 2025-08-04, cùng các khoảng giữa các mốc đã ghim, là UNKNOWN.

## Sự kiện quyền chưa được xác minh

Không kết luận sự kiện từ bước nhảy giá.

| Mã | CSV | Trạng thái CSV | Bản HOSE | official_ex_date | published_at |
|---|---|---|---|---|---|
| TCB | 2024-06-11, stock_dividend, ratio 2.0 | CAN_DOI_CHIEU | hose-1705374 | 2024-06-20 | null, `CHUA_XAC_MINH` |
| VCB | 2025-03-03, stock_dividend, ratio 1.495 | CAN_DOI_CHIEU | hose-1753594 | 2025-03-12 | null, `CHUA_XAC_MINH` |

`engine/data.py` `load_market` vẫn nhân hệ số từ `engine/adjust.py`. `build_events` không xét `source_status`. Sự kiện chưa xác minh vẫn có thể thành `APPLIED` nếu tỷ lệ khớp biến động giá. Việc đó làm lệch chuỗi giá nghiên cứu. PR này không sửa `engine/adjust.py` (ADR-0009 điều 7 và lệnh PIT-001).

## Alpha có chứng minh được không

**NOT_READY.** Không có khoảng ngày nào đủ điều kiện để backtest point-in-time rồi gọi là alpha.

Tập đã đủ để làm gì:

- Đối chiếu byte và, với bốn PDF VN30, đối chiếu danh sách thành phần tại đúng ngày hiệu lực đã đọc từ tin. Chỉ những ngày đó, không phải cả quãng giữa hai ngày.
- Không đủ để gán thành phần cho 2016-01-01 đến 2025-08-03.
- Không đủ để nói rổ không đổi giữa hai lần công bố.
- Không đủ để nghiên cứu các mã đã vào rổ nhưng chưa có giá.
- Không đủ để coi giá điều chỉnh hiện hành là verified-adjusted.

Chỉ số nghiên cứu trên cửa sổ 2016 đến nay vẫn chịu thiên lệch sống sót: engine dùng một danh sách cố định, và báo cáo chu kỳ đã gắn nhãn đó (ADR-0008). Nhãn không làm con số đúng.

Giả định chưa chứng minh: phí mua/bán 0,0015, thuế bán 0,001, trượt giá 0,001, lô 100, khóa trần/sàn ở 95% biên độ, biên độ mặc định 0,07. Không có sổ lệnh giấy `paper/trades.csv` trong cây này. Không có đối chiếu khớp lệnh thật.

`state/ENGINE_STATE.json` ngày 2026-11-20: 222 lần thử, 0 model ACTIVE, NAV giấy 1.000.000.000, sụt giảm giấy 0, `universe_basis` CURRENT. `reports/scorecard.json` cùng ngày: 6 dự báo, 0 resolved, 0 timing_valid, 3 cặp A/B, 1 cặp bất đồng thô bị chặn vì `legacy_unproven`, mẫu 194 không đổi. Những số này không được dùng để tuyên bố alpha. Không gian 13 feature × 3 model, top-k và horizon không bị đổi.

`state/PROJECT_STATE.yaml` vẫn ghi thư viện 1/40 SOURCED và ghi chú KN-T2 DRAFT, chưa CITED. ADR-0007 vì vậy chưa mở lại engine kịch bản. ADR-0008 vẫn hoãn CVaR và tối ưu danh mục. PR này không triển khai các tầng đó.

## Sửa cổng READY sau phản biện (ChatGPT OpenAI, 21/11/2026)

Lượt sửa tiếp trên cùng PR #69 giữ nguyên nguồn/engine. Bản kiểm toán sử dụng **cổng fail-closed**: bất kỳ điều kiện bắt buộc nào FAIL dẫn đến NOT_READY; thiếu chứng cứ (UNKNOWN/INCONCLUSIVE) dẫn đến INCONCLUSIVE khi không có lỗi khác. Không một kiểm tra đơn lẻ nào tự chứng nhận full PIT.

- Không coi comment hoặc string literal chứa `source_status`, `verified_factors`, `vn30_history` là xác minh hành vi. Kiểm tra AST chỉ hỗ trợ phát hiện cấu trúc; **PASS cho chuỗi verified hoặc historical selection vẫn yêu cầu phép thử hành vi độc lập**.
- Độ phủ giá được tách thành `TICKER_PRESENCE` và `PRICE_WINDOW_COVERAGE`; một dòng giá không thể tạo PASS về cửa sổ nhiều phiên.
- Có thêm `DECISION_TIME_OF_KNOWLEDGE`: chưa khai giờ quyết định thì INCONCLUSIVE, kể cả `PUBLICATION_BEFORE_USE` PASS.
- Tin JSON phải nêu ngày hiệu lực trong phần **summary công bố**, không phải chỉ xuất hiện tình cờ trong metadata hoặc tiêu đề.
- Ma trận test đối kháng bảo đảm FAIL/UNKNOWN/INCONCLUSIVE ở mọi cổng bắt buộc đều chặn READY.
- Bộ audit tiếp tục **chỉ đọc**. Snapshot JSON đã được tái sinh từ đầu ra `PIT001_JSON` của GitHub Actions `44876139858` trên commit `6d638ad0` (SUCCESS); hai lần chạy audit tại cùng commit cho kết quả giống hệt nhau.
- Test suite tại run này: **319 passed, 68 subtests passed**, 79 cảnh báo; toàn bộ bước CI bắt buộc kết thúc SUCCESS. Bản ghi JSON mới vẫn có kết luận **NOT_READY** và 18 findings. L-09/Owner chưa hoàn tất.

## Điều kiện tối thiểu trước một baseline công bằng

Chưa mở baseline. Muốn mở sau này, cùng lúc, không chọn lại sau khi nhìn kết quả:

1. Thành phần từng ngày là UNKNOWN ở đâu thì ngày đó không vào kết luận. Không dùng rổ config để thế.
2. Mọi mã trong cửa sổ đã chọn có giá, và sự kiện quyền chưa `DA_DOI_CHIEU` không vào chuỗi verified-adjusted.
3. Đăng ký trước một lần thử trong không gian đang khóa. Không thêm feature, model, horizon, top-k, benchmark.
4. Phí, trần/sàn, lệnh không khớp để là giả định thì phải ghi INCONCLUSIVE về khả năng khớp, không ghi là đã chứng minh.
5. So với đúng benchmark đã định nghĩa. Không đổi tên VN-Index, VN30 hay bình quân 30 mã để chúng thành nhau.
6. Kết quả âm hoặc không rõ phải được giữ. 0 model ACTIVE thì không promote.

## Việc kế tiếp có tác động lớn nhất

Thu và ghim PDF gốc HOSE cho các kỳ thành phần VN30 từ 2016 đến trước 2025-08-04. Không điền mã từ báo chí hay từ rổ hiện tại. Không có lớp đó thì mọi con số nghiên cứu trên cửa sổ engine đang chạy vẫn không phải point-in-time.

Việc mã phải đi kèm, nhưng không làm trong PR này: PR riêng cho cổng `source_status` trên chuỗi giá nghiên cứu, vì TCB/VCB đang có thể sửa lịch sử giá khi chưa xác minh. ADR-0009 chưa cho sửa `engine/adjust.py` bằng PIT-001.
~~~~

## tests/test_pit001_audit.py

**Git blob SHA**: `51c918f60e1192766dc823846fe68b2e33f3d545`  ·  **Số dòng:** 306

~~~~python
"""PIT-001: fixture độc lập. Không đụng kho giá, config hay engine của repo khi dựng cây tạm."""
import hashlib, json, unittest
from pathlib import Path

from tools import pit001_audit as pit

ROOT = Path(__file__).resolve().parents[1]
HEADING = pit.VN30_HEADING


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _members(n=30, prefix="A"):
    # 30 mã giả, đúng 3 chữ, không trùng mã thật để fixture không bị đọc nhầm là khuyến nghị.
    out = []
    i = 0
    while len(out) < n:
        out.append(f"{prefix}{i:02d}"[-3:])
        i += 1
    return out


class ParserTests(unittest.TestCase):
    def test_vn30_section_stops_before_reserve_list(self):
        names = [f"T{i:02d}" for i in range(30)]
        lines = [f"    {i+1:2d}         {name}      Công ty" for i, name in enumerate(names)]
        text = HEADING + "\n" + "\n".join(lines) + "\nDanh mục cổ phiếu dự phòng chỉ số VN30\n    1         ZZZ      ngoài rổ"
        self.assertEqual(pit.tickers_in_vn30_section(text), names)

    def test_missing_heading_is_none(self):
        self.assertIsNone(pit.tickers_in_vn30_section("không có mục chỉ số\n    1         AAA      x"))


class AuditFixtureTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _snapshot(self):
        h = hashlib.sha256()
        for path in sorted(p for p in self.root.rglob("*") if p.is_file()):
            h.update(str(path.relative_to(self.root)).encode())
            h.update(path.read_bytes())
        return h.hexdigest()

    def _write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _manifest(self, docs):
        self._write("data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json",
                    json.dumps({"source_documents": docs}, ensure_ascii=False))

    def _doc(self, source_id, body, effective, published, members):
        rel = f"data/evidence/vn30_reviews/{source_id}/note.txt"
        self._write(rel, body)
        return {
            "source_id": source_id, "path": rel, "sha256": _sha(body), "bytes": len(body.encode("utf-8")),
            "published_at": published, "effective_date": effective, "members_after": members,
        }

    def test_bad_hash_is_fail_and_audit_does_not_write(self):
        body = "nguon"
        doc = self._doc("s1", body, "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
        doc["sha256"] = "0" * 64
        self._manifest([doc])
        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n")
        before = self._snapshot()
        result = pit.audit(self.root)
        self.assertEqual(before, self._snapshot())
        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")
        self.assertTrue(result["read_only"])

    def test_missing_source_file_is_fail(self):
        self._manifest([{
            "source_id": "s1", "path": "data/evidence/vn30_reviews/missing.txt",
            "sha256": "abc", "bytes": 1, "published_at": "2024-01-01", "effective_date": "2024-01-02",
            "members_after": [],
        }])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")

    def test_published_after_effective_is_fail(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-03T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "FAIL")

    def test_missing_published_at_is_unknown(self):
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
        doc["published_at"] = None
        self._manifest([doc])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "UNKNOWN")

    def test_universe_short_of_research_start_is_fail_and_before_is_unknown(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2025-08-04", "2025-07-16T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2025-08-04,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        self._write("config.yaml", "universe_basis: CURRENT\ndata:\n  start: \"2016-01-01\"\nuniverse: [" + ", ".join(members) + "]\n")
        result = pit.audit(self.root)
        st = pit._status_map(result["findings"])
        self.assertEqual(st["UNIVERSE_COVERAGE"], "FAIL")
        self.assertEqual(st["MEMBERSHIP_BEFORE_FIRST_EVIDENCE"], "UNKNOWN")
        self.assertEqual(st["CSV_INTERNAL"], "PASS")
        self.assertNotEqual(result["conclusion"], "READY")

    def test_incomplete_membership_is_fail(self):
        members = _members(29)
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["CSV_INTERNAL"], "FAIL")

    def test_unverified_event_enters_chain_when_adjust_ignores_status(self):
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,CAN_DOI_CHIEU,chua doi chieu\n")
        self._write("engine/adjust.py", "def build_events(close, observed, manual, yahoo):\n    status = 'APPLIED'\n    return status\n")
        self._write("engine/data.py", "def load_market(as_of=None):\n    events = adjust.build_events(None, None, None, None)\n    return events\n")
        result = pit.audit(self.root)
        st = pit._status_map(result["findings"])
        self.assertEqual(st["CORPORATE_ACTION_VERIFICATION"], "FAIL")
        self.assertEqual(st["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "FAIL")

    def test_verified_gate_is_pass_for_chain_check(self):
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,DA_DOI_CHIEU,da doi chieu\n")
        self._write("engine/adjust.py",
                    "def build_events(close, observed, manual, yahoo):\n"
                    "    source_status = manual\n"
                    "    if source_status != 'DA_DOI_CHIEU':\n"
                    "        return 'KHONG'\n"
                    "    return 'APPLIED'\n")
        self._write("engine/data.py", "def load_market(as_of=None):\n    return adjust.build_events(None, None, None, None)\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "INCONCLUSIVE")

    def test_schema_fail_never_certifies_ready(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T10:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        self._write("config.yaml",
                    "universe_basis: HISTORICAL\n"
                    "data:\n  start: \"2024-01-02\"\n"
                    "universe: [" + ", ".join(members) + "]\n")
        self._write("engine/data.py",
                    "def ingest(end=None):\n"
                    "    history = open('data/vn30_history.csv').read()\n"
                    "    return history\n"
                    "def load_market(as_of=None):\n"
                    "    return verified_factors()\n")
        self._write("engine/adjust.py",
                    "def build_events(close, observed, manual, yahoo):\n"
                    "    source_status = 'DA_DOI_CHIEU'\n"
                    "    return source_status\n")
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n")
        prices = ["date,ticker,close"]
        for ticker in members:
            prices.append(f"2024-01-02,{ticker},1")
        self._write("data/store/prices/2024-01.csv", "\n".join(prices) + "\n")
        before = self._snapshot()
        result = pit.audit(self.root)
        self.assertEqual(before, self._snapshot())
        st = pit._status_map(result["findings"])
        self.assertEqual(st["ADR0008_SCHEMA"], "FAIL")
        self.assertEqual(st["UNIVERSE_COVERAGE"], "PASS")
        self.assertEqual(st["ENGINE_UNIVERSE_MODE"], "INCONCLUSIVE")
        self.assertEqual(st["TICKER_PRESENCE"], "PASS")
        self.assertEqual(st["PROVENANCE_HASH"], "PASS")
        self.assertEqual(result["conclusion"], "NOT_READY")
        self.assertFalse(result["alpha_claim"])

    def test_news_without_effective_token_is_fail(self):
        rel = "data/evidence/vn30_reviews/n1/news.json"
        self._write(rel, '{"data":{"summary":"khong ghi ngay hieu luc"}}')
        blob = (self.root / rel).read_bytes()
        self._manifest([{
            "source_id": "n1", "path": rel, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob),
            "published_at": "2024-01-01T00:00:00Z", "effective_date": "2024-01-02", "members_after": [],
        }])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["NEWS_EFFECTIVE_DATE_TEXT"], "FAIL")

    def test_schema_mismatch_does_not_invent_rows(self):
        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n2024-01-02,ABC,ADD,s1\n")
        result = pit.audit(self.root)
        finding = next(item for item in result["findings"] if item["id"] == "ADR0008_SCHEMA")
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["evidence"]["actual_columns"], ["effective_date", "ticker", "action", "source_id"])


class FailClosedMatrixTests(unittest.TestCase):
    """Mỗi thiếu hụt trong hợp đồng đều ngăn READY, kể cả không có FAIL khác."""
    def test_each_critical_fail_blocks_ready(self):
        critical = (
            "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
            "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
            "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
            "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
            "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
            "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
            "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE",
            "NEWS_EFFECTIVE_DATE_TEXT", "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
        )
        baseline = [pit.finding(k, "PASS", "fixture") for k in critical]
        self.assertEqual(pit.conclude(baseline)[0], "READY")
        for key in critical:
            for status in ("FAIL", "UNKNOWN", "INCONCLUSIVE"):
                changed = [pit.finding(f["id"], status if f["id"] == key else "PASS", "fixture")
                           for f in baseline]
                got = pit.conclude(changed)[0]
                want = "NOT_READY" if status == "FAIL" else "INCONCLUSIVE"
                with self.subTest(key=key, status=status):
                    self.assertEqual(got, want)
        self.assertEqual(pit.conclude(baseline[:-1])[0], "INCONCLUSIVE")

    def test_not_ready_overrides_other_missing_evidence(self):
        rows = [pit.finding("PROVENANCE_HASH", "UNKNOWN", "x"),
                pit.finding("ADR0008_SCHEMA", "FAIL", "x")]
        self.assertEqual(pit.conclude(rows)[0], "NOT_READY")

    def test_comments_and_literals_do_not_prove_verified_gate(self):
        src = ("def build_events(a,b,c,d):\n"
               "    # source_status is checked\n"
               "    note = 'source_status'\n"
               "    return 'APPLIED'\n")
        self.assertFalse(pit.research_chain_requires_verified_status(src))
        self.assertFalse(pit.load_market_uses_verified_chain(
            "def load_market():\n    # verified_factors()\n    note = 'verified_factors'\n    return 1\n"))

    def test_engine_historical_string_in_comment_is_not_proof(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "engine").mkdir()
            (root / "engine/data.py").write_text(
                "def load_market():\n    # vn30_history is loaded\n"
                "    path = 'vn30_history'\n    return path\n", encoding="utf-8")
            result = pit.check_engine_mode(root, {"universe_basis":"HISTORICAL"})
            self.assertEqual(result["status"], "INCONCLUSIVE")

    def test_price_one_row_per_symbol_is_not_window_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "data/store/prices/2024-01.csv"
            p.parent.mkdir(parents=True)
            p.write_text("date,ticker,close\n2024-01-02,AAA,1\n"
                         "2024-01-02,BBB,1\n", encoding="utf-8")
            info = pit._price_tickers(root)
            states = [("2024-01-02", {"AAA", "BBB"})]
            self.assertEqual(pit.check_ticker_presence(info, states)["status"], "PASS")
            coverage = pit.check_price_window_coverage(info, states, {"horizon_days":20})
            self.assertEqual(coverage["status"], "FAIL")

    def test_publication_same_day_after_decision_is_fail(self):
        docs = [{"source_id":"news", "published_at":"2026-11-02T09:00:00Z",
                 "effective_date":"2026-11-02"}]   # 16:00 VN > 15:00 decision
        cfg = {"research":{"decision_time_local":"15:00"}}
        self.assertEqual(pit.check_publication_order(docs)["status"], "PASS")
        self.assertEqual(pit.check_decision_cutoff(docs, cfg)["status"], "FAIL")
        self.assertEqual(pit.check_decision_cutoff(docs, {})["status"], "INCONCLUSIVE")

    def test_date_only_outside_news_summary_is_not_proof(self):
        raw = '{"data":{"title":"13/05/2026", "summary":"Không có thông báo ngày hiệu lực"}}'
        self.assertFalse(pit._news_effective_statement(raw, "2026-05-13"))

    def test_missing_pdf_content_never_counts_as_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = [{"source_id":"p", "path":"data/missing.pdf",
                     "effective_date":"2026-11-16", "members_after":["AAA"]}]
            self.assertEqual(pit.check_pdf_contents(root, docs)["status"], "INCONCLUSIVE")

if __name__ == "__main__":
    unittest.main()
~~~~

## tools/pit001_audit.py

**Git blob SHA**: `a332a90fe4bdd6a350add186e1c5a8ea5fab574c`  ·  **Số dòng:** 945

~~~~python
"""PIT-001 — kiểm toán chỉ đọc: đúng thời điểm, đủ thành phần, provenance.

Không mạng. Không ghi kho giá, config, engine, ledger, luật hay manifest.
Kết quả in JSON ra stdout. Hash khớp chỉ chứng minh byte không đổi, không chứng minh nội dung đúng.
"""
import ast, csv, gzip, hashlib, json, re, unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")
ADR0008_COLUMNS = ["effective_date", "ticker", "change", "source_url", "source_status"]
CSV_COLUMNS = ["effective_date", "ticker", "action", "source_id"]
VERIFIED_STATUS = "DA_DOI_CHIEU"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VN30_HEADING = "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30"
# Các mục khác trong cùng một PDF quy mô. Không kết luận nội dung VN30 từ tên tệp.
OTHER_INDEX_HEADINGS = (
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
)


def finding(fid, status, summary, **evidence):
    if status not in STATUSES:
        raise ValueError(status)
    item = {"id": fid, "status": status, "summary": summary}
    if evidence:
        item["evidence"] = evidence
    return item


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(root: Path):
    path = root / "config.yaml"
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _vn_date(value):
    """Ngày lịch theo giờ Việt Nam. Thiếu hoặc không đọc được → None."""
    if value is None or value == "":
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)
    return dt.astimezone(VN_TZ).date().isoformat()


def _dmy(iso_date: str) -> str:
    y, m, d = iso_date.split("-")
    return f"{d}/{m}/{y}"


def load_vn30_rows(root: Path):
    path = root / "data" / "vn30_history.csv"
    if not path.is_file():
        return None, path
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), path


def load_manifest_docs(root: Path):
    path = root / "data" / "evidence" / "vn30_reviews" / "EVIDENCE_MANIFEST.json"
    if not path.is_file():
        return None, path
    payload = _load_json(path)
    docs = payload.get("source_documents") if isinstance(payload, dict) else None
    if not isinstance(docs, list):
        return None, path
    return docs, path


def reconstruct(rows):
    """Tập thành viên sau mỗi effective_date. Lỗi cấu trúc → (None, lý do)."""
    by_date = {}
    for row in rows:
        by_date.setdefault(row.get("effective_date"), []).append(row)
    members = set()
    states = []
    for date in sorted(d for d in by_date if d):
        day = by_date[date]
        for row in day:
            if row.get("action") == "REMOVE":
                ticker = row.get("ticker")
                if ticker not in members:
                    return None, f"REMOVE mã không có mặt: {ticker} {date}"
                members.remove(ticker)
        for row in day:
            if row.get("action") == "ADD":
                ticker = row.get("ticker")
                if ticker in members:
                    return None, f"ADD mã đang có mặt: {ticker} {date}"
                members.add(ticker)
            elif row.get("action") not in ("ADD", "REMOVE"):
                return None, f"action lạ: {row.get('action')} {date}"
        if len(members) != 30:
            return None, f"{date}: {len(members)} mã, không phải 30"
        states.append((date, set(members)))
    return states, None


def members_on(states, day):
    current = None
    for date, members in states or []:
        if date <= day:
            current = members
        else:
            break
    return current


def check_provenance(root, docs):
    if docs is None:
        return finding("PROVENANCE_HASH", "UNKNOWN", "Không có manifest VN30 để đối chiếu hash.")
    bad, ok = [], []
    for doc in docs:
        rel = doc.get("path")
        if not rel:
            bad.append({"source_id": doc.get("source_id"), "error": "thiếu path"})
            continue
        path = root / rel
        if not path.is_file():
            bad.append({"source_id": doc.get("source_id"), "path": rel, "error": "thiếu tệp"})
            continue
        digest = _sha256(path)
        size = path.stat().st_size
        row = {"source_id": doc.get("source_id"), "path": rel, "sha256": digest, "bytes": size}
        if digest != doc.get("sha256") or size != doc.get("bytes"):
            row["expected_sha256"] = doc.get("sha256")
            row["expected_bytes"] = doc.get("bytes")
            bad.append(row)
        else:
            ok.append(row)
    if bad:
        return finding(
            "PROVENANCE_HASH", "FAIL",
            "Có tệp nguồn lệch hash, lệch số byte hoặc không có trên đĩa. Hash khớp không được hiểu là nội dung đã đúng.",
            mismatches=bad, matched=len(ok))
    return finding(
        "PROVENANCE_HASH", "PASS",
        "Mọi tệp kê trong manifest VN30 khớp SHA-256 và số byte. Việc này không xác minh nội dung.",
        matched=ok)


def check_publication_order(docs):
    if docs is None:
        return finding("PUBLICATION_BEFORE_USE", "UNKNOWN", "Không có manifest để so ngày công bố với ngày hiệu lực.")
    bad, unknown, ok = [], [], []
    for doc in docs:
        published = _vn_date(doc.get("published_at"))
        effective = doc.get("effective_date")
        row = {"source_id": doc.get("source_id"), "published_on": published, "effective_date": effective}
        if not published or not effective:
            unknown.append(row)
        elif published > effective:
            bad.append(row)
        else:
            ok.append(row)
    if bad:
        return finding(
            "PUBLICATION_BEFORE_USE", "FAIL",
            "Có tài liệu được phép dùng trước ngày công bố theo giờ Việt Nam.",
            lookahead=bad, undated=unknown)
    if unknown:
        return finding(
            "PUBLICATION_BEFORE_USE", "UNKNOWN",
            "Một số tài liệu thiếu published_at hoặc effective_date nên không kết luận được thứ tự thời điểm.",
            undated=unknown, dated_ok=len(ok))
    return finding(
        "PUBLICATION_BEFORE_USE", "PASS",
        "Với mọi tài liệu có đủ hai ngày, ngày công bố theo giờ Việt Nam không sau ngày hiệu lực.",
        checked=len(ok))


def check_decision_cutoff(docs, cfg):
    """Kiểm tra chính xác phút công bố so với phút ra quyết định theo giờ VN.
    Thiếu lịch quyết định đã đăng ký => INCONCLUSIVE, không lấy ngày hiệu lực thay thế.
    """
    if not docs:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
                       "Không có nguồn để đối chiếu thời điểm công bố.")
    cutoff = ((cfg or {}).get("research") or {}).get("decision_time_local")
    if not isinstance(cutoff, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", cutoff):
        return finding("DECISION_TIME_OF_KNOWLEDGE", "INCONCLUSIVE",
                       "Chưa đăng ký giờ ra quyết định theo ngày giao dịch (research.decision_time_local). "
                       "So published_on <= effective_date không chứng minh có thể dùng ngay trong phiên.",
                       decision_time_local=None)
    bad, unknown, ok = [], [], []
    for doc in docs:
        published, effective = doc.get("published_at"), doc.get("effective_date")
        row = {"source_id": doc.get("source_id"), "published_at": published,
               "effective_date": effective}
        try:
            pub = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            if pub.tzinfo is None:
                raise ValueError("published_at thiếu timezone")
            decision = datetime.fromisoformat(f"{effective}T{cutoff}:00").replace(tzinfo=VN_TZ)
            row["decision_at_local"] = decision.isoformat()
            row["publication_at_local"] = pub.astimezone(VN_TZ).isoformat()
            (bad if pub > decision else ok).append(row)
        except (ValueError, TypeError):
            unknown.append(row)
    if bad:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "FAIL",
                       "Có nguồn được công bố sau giờ ra quyết định; không thể dùng trong cùng phiên.",
                       late_publications=bad, undated=unknown, verified_before=len(ok))
    if unknown:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
                       "Ngày/giờ nguồn chưa đủ để so với giờ ra quyết định.",
                       undated=unknown, verified_before=len(ok))
    return finding("DECISION_TIME_OF_KNOWLEDGE", "PASS",
                   "Các bản tin trong manifest được công bố trước giờ quyết định giả định đã khai; "
                   "không xác nhận vintage cho toàn bộ giá và BCTC.",
                   checked=len(ok), decision_time_local=cutoff)

def check_csv(rows):
    if rows is None:
        return finding("CSV_INTERNAL", "UNKNOWN", "Không có data/vn30_history.csv."), None
    if not rows:
        return finding("CSV_INTERNAL", "FAIL", "CSV thành phần không có dòng dữ liệu."), None
    missing = [c for c in CSV_COLUMNS if c not in rows[0]]
    if missing:
        return finding("CSV_INTERNAL", "FAIL", "CSV thiếu cột mà bộ test hiện hành đang khóa.", missing_columns=missing), None
    states, err = reconstruct(rows)
    if err:
        return finding("CSV_INTERNAL", "FAIL", "Không dựng lại được rổ 30 mã từ CSV.", error=err), None
    return finding(
        "CSV_INTERNAL", "PASS",
        "CSV dựng lại được các mốc, mỗi mốc đúng 30 mã. Không suy ra thành phần trước mốc đầu tiên.",
        states=[{"effective_date": d, "members": sorted(m)} for d, m in states]), states


def check_adr_schema(rows):
    if rows is None:
        return finding("ADR0008_SCHEMA", "UNKNOWN", "Không có CSV để đối chiếu khuôn ADR-0008.")
    actual = list(rows[0].keys()) if rows else []
    if actual == ADR0008_COLUMNS:
        return finding("ADR0008_SCHEMA", "PASS", "CSV đúng khuôn cột ADR-0008.", columns=actual)
    return finding(
        "ADR0008_SCHEMA", "FAIL",
        "CSV không theo khuôn ADR-0008 (effective_date,ticker,change,source_url,source_status). "
        "Không được tự ghi đè CSV trong PIT-001. Khuôn đang khóa bởi test là cột action/source_id.",
        actual_columns=actual, adr0008_columns=ADR0008_COLUMNS)


def check_coverage(cfg, states):
    start = ((cfg or {}).get("data") or {}).get("start")
    if states is None:
        return finding("UNIVERSE_COVERAGE", "UNKNOWN", "Chưa dựng được lịch sử thành phần.")
    first = states[0][0]
    if not start:
        return finding(
            "UNIVERSE_COVERAGE", "UNKNOWN",
            "Không đọc được data.start trong config nên không chốt được cửa sổ nghiên cứu.",
            first_evidence_date=first)
    if start < first:
        return finding(
            "UNIVERSE_COVERAGE", "FAIL",
            "Lịch sử thành phần đã ghim không phủ từ ngày đầu cửa sổ nghiên cứu. Không tự điền các kỳ thiếu.",
            research_start=start, first_evidence_date=first,
            uncovered_until_exclusive=first)
    return finding(
        "UNIVERSE_COVERAGE", "PASS",
        "Mốc thành phần đầu tiên không sau ngày đầu cửa sổ nghiên cứu trong config.",
        research_start=start, first_evidence_date=first)


def check_before_first(cfg, states):
    if states is None or not states:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN", "Chưa có mốc thành phần.")
    first = states[0][0]
    start = ((cfg or {}).get("data") or {}).get("start")
    if not start:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
                       "Không có ngày đầu nghiên cứu để so với mốc bản gốc.")
    if start < first:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
                       "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN.",
                       first_evidence_date=first, research_start=start, applies=True)
    return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "PASS",
                   "Khoảng nghiên cứu không yêu cầu thành phần trước mốc gốc đầu tiên. "
                   "Điều này chưa chứng minh tính liên tục giữa các kỳ.",
                   first_evidence_date=first, research_start=start, applies=False)

def check_continuity(docs, states):
    if not states or len(states) < 2:
        return finding(
            "CONTINUITY_BETWEEN_REVIEWS", "INCONCLUSIVE",
            "Chưa đủ hai mốc đã ghim để nói về khoảng giữa các kỳ.")
    gaps = []
    for (a, _), (b, _) in zip(states, states[1:]):
        gaps.append({"after": a, "before": b,
                     "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). "
                             "Việc không thấy tệp không chứng minh rổ không đổi."})
    copied = []
    for doc in docs or []:
        if doc.get("names_copied_from") and doc.get("names_copied_from") != doc.get("source_id"):
            copied.append({"source_id": doc.get("source_id"), "names_copied_from": doc.get("names_copied_from"),
                           "effective_date": doc.get("effective_date")})
    return finding(
        "CONTINUITY_BETWEEN_REVIEWS", "UNKNOWN",
        "Khoảng giữa các mốc đã ghim không được coi là đã chứng minh liên tục. "
        "Bản tin chép danh sách từ PDF kỳ trước không phải là in lại đủ 30 mã.",
        gaps=gaps, names_copied_from_other_document=copied)


def _function_ast(src, name):
    """Chỉ xét AST thật; comment hoặc string literal không được tính là hành vi."""
    try:
        module = ast.parse(src)
    except SyntaxError:
        return None
    return next((n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == name), None)


def _calls_adjust_build_events(fn):
    return any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "build_events"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "adjust"
        for n in ast.walk(fn)
    )


def research_chain_requires_verified_status(src: str):
    """Dấu hiệu cú pháp, KHÔNG phải chứng minh đã chặn các event chưa xác minh."""
    fn = _function_ast(src, "build_events")
    if fn is None:
        return None
    return any(isinstance(n, ast.Name) and n.id == "source_status"
               for n in ast.walk(fn))


def load_market_uses_verified_chain(src: str):
    """Trả về dấu hiệu gọi hàm verified; không bao giờ tự cấp PASS từ dấu hiệu này."""
    fn = _function_ast(src, "load_market")
    if fn is None:
        return None
    return any(isinstance(n, ast.Call) and (
        (isinstance(n.func, ast.Name) and n.func.id in ("verified_adjust", "verified_factors"))
        or (isinstance(n.func, ast.Attribute)
            and n.func.attr in ("verified_adjust", "verified_factors"))
    ) for n in ast.walk(fn))


def check_engine_mode(root, cfg):
    data_py = root / "engine" / "data.py"
    if not data_py.is_file():
        return finding("ENGINE_UNIVERSE_MODE", "UNKNOWN", "Không có engine/data.py để kiểm tra.")
    basis = (cfg or {}).get("universe_basis")
    fn = _function_ast(data_py.read_text(encoding="utf-8"), "load_market")
    if basis == "CURRENT":
        return finding("ENGINE_UNIVERSE_MODE", "FAIL",
                       "Cấu hình khai CURRENT: không thể chứng nhận chọn universe theo từng ngày.",
                       universe_basis=basis)
    if fn is None:
        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                       "Không phân tích được hàm load_market; không được tự chứng nhận HISTORICAL.",
                       universe_basis=basis)
    if basis == "HISTORICAL":
        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                       "HISTORICAL là một khai báo, không chứng minh engine dùng đúng tập thành viên "
                       "từng phiên. Cần kiểm thử hành vi replay với ngày vào/ra và thiếu nguồn.",
                       universe_basis=basis, behavioral_membership_test_verified=False)
    return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                   "Không có bằng chứng hành vi chọn universe theo ngày.", universe_basis=basis)

def check_config_vs_basket(cfg, states):
    if not states:
        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Chưa có rổ dựng từ CSV.")
    configured = (cfg or {}).get("universe")
    if not configured:
        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Config không có danh sách universe.")
    configured = set(configured)
    latest_date, latest = states[-1]
    only_config = sorted(configured - latest)
    only_evidence = sorted(latest - configured)
    if not only_config and not only_evidence and len(configured) == 30:
        return finding(
            "CONFIG_VS_EVIDENCED_BASKET", "PASS",
            "Danh sách config trùng rổ dựng được tại mốc CSV cuối cùng.",
            as_of=latest_date)
    return finding(
        "CONFIG_VS_EVIDENCED_BASKET", "FAIL",
        "Danh sách cố định trong config không trùng rổ dựng từ CSV tại mốc cuối. "
        "Đây là lệch thành phần, không phải khuyến nghị giao dịch.",
        csv_state_as_of=latest_date,
        in_config_not_in_csv_state=only_config,
        in_csv_state_not_in_config=only_evidence,
        config_count=len(configured), evidence_count=len(latest))


def _price_tickers(root: Path):
    """Tập mã, các ngày thực có giá và khoảng ngày của kho (chỉ đọc)."""
    tickers, dates_by_ticker, market_dates = set(), {}, set()
    first = last = None
    rows, paths = 0, []
    legacy = root / "data" / "store" / "prices.csv.gz"
    monthly = root / "data" / "store" / "prices"
    candidates = []
    if legacy.is_file():
        candidates.append(legacy)
    if monthly.is_dir():
        candidates.extend(sorted(monthly.glob("*.csv")))
    if not candidates:
        return None

    def consume(stream):
        nonlocal first, last, rows
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "ticker" not in reader.fieldnames or "date" not in reader.fieldnames:
            return
        for rec in reader:
            ticker, date = rec.get("ticker"), (rec.get("date") or "")[:10]
            if not ticker:
                continue
            tickers.add(ticker)
            rows += 1
            if date:
                dates_by_ticker.setdefault(ticker, set()).add(date)
                market_dates.add(date)
                if first is None or date < first:
                    first = date
                if last is None or date > last:
                    last = date

    for path in candidates:
        paths.append(str(path.relative_to(root)))
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
                consume(f)
        else:
            with path.open(encoding="utf-8", newline="") as f:
                consume(f)
    return {"tickers": tickers, "dates_by_ticker": dates_by_ticker, "market_dates": market_dates,
            "first": first, "last": last, "rows": rows, "paths": paths}


def check_ticker_presence(info, states):
    if info is None:
        return finding("TICKER_PRESENCE", "UNKNOWN", "Không thấy kho giá data/store.")
    if not states:
        return finding("TICKER_PRESENCE", "INCONCLUSIVE",
                       "Có kho giá nhưng thiếu rổ lịch sử để kiểm tra đủ mã.")
    needed = set().union(*(members for _, members in states))
    missing = sorted(needed - info["tickers"])
    extra = sorted(info["tickers"] - needed)
    details = {"price_first": info["first"], "price_last": info["last"],
               "price_rows": info["rows"], "price_tickers": sorted(info["tickers"]),
               "members_ever_in_csv": sorted(needed), "members_without_any_price_row": missing,
               "priced_but_never_in_pinned_baskets": extra, "paths": info["paths"]}
    if missing:
        return finding("TICKER_PRESENCE", "FAIL",
                       "Có mã từng nằm trong rổ ghim nhưng không có dòng giá.", **details)
    return finding("TICKER_PRESENCE", "PASS",
                   "Mỗi mã trong rổ đã ghim có ít nhất một dòng. KHÔNG chứng nhận đủ chuỗi giá.",
                   **details)


def check_price_window_coverage(info, states, cfg):
    """Độ phủ theo PHIÊN. Không có lịch phiên chính thức/vintage thì không thể PASS."""
    if info is None:
        return finding("PRICE_WINDOW_COVERAGE", "UNKNOWN", "Không thấy kho giá.")
    if not states:
        return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
                       "Chưa có thành phần lịch sử để ghép với chuỗi giá từng phiên.")
    horizon = int((cfg or {}).get("horizon_days") or 20)
    lookback = int(((cfg or {}).get("quality") or {}).get("feature_lookback") or 0)
    required = max(2, horizon + 1, lookback + 1)
    needed = set().union(*(m for _, m in states))
    absent = sorted(needed - info["tickers"])
    short = [{"ticker": t, "distinct_sessions": len(info["dates_by_ticker"].get(t, set()))}
             for t in sorted(needed)
             if len(info["dates_by_ticker"].get(t, set())) < required]
    # Các ngày được suy từ GIÁ ĐÃ CÓ, không phải lịch giao dịch chính thức.
    market_days = sorted(info["market_dates"])
    missing_by_period = []
    for k, (effective, members) in enumerate(states):
        end = states[k + 1][0] if k + 1 < len(states) else None
        dates = [d for d in market_days if d >= effective and (end is None or d < end)]
        for ticker in sorted(members):
            gaps = [d for d in dates if d not in info["dates_by_ticker"].get(ticker, set())]
            if gaps and len(missing_by_period) < 40:
                missing_by_period.append({"ticker": ticker, "effective_date": effective,
                                          "missing_session_count": len(gaps), "examples": gaps[:3]})
    details = {"horizon_days": horizon, "feature_lookback": lookback,
               "min_distinct_sessions_for_individual_ticker": required,
               "missing_tickers": absent, "short_series": short[:40],
               "missing_dates_on_observed_market_calendar": missing_by_period,
               "official_exchange_calendar_verified": False}
    if absent or short or missing_by_period:
        return finding("PRICE_WINDOW_COVERAGE", "FAIL",
                       "Thiếu mã, chuỗi quá ngắn hoặc thiếu ngày giá trong phiên có dữ liệu cho mã khác. "
                       "Chưa xét liệu lịch phiên suy từ kho có đầy đủ hay không.", **details)
    return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
                   "Các mã có đủ số phiên tối thiểu trong kho quan sát, nhưng chưa có lịch phiên "
                   "chính thức và dữ liệu giá/vintage được xác minh để kết luận độ phủ PIT.", **details)

def _manual_events(root: Path):
    path = root / "data" / "corporate_actions.csv"
    if not path.is_file():
        return None, path
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f)), path


def _ca_manifest(root: Path):
    path = root / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
    if not path.is_file():
        return None
    payload = _load_json(path)
    docs = payload.get("source_documents") if isinstance(payload, dict) else None
    return docs if isinstance(docs, list) else None


def check_corporate_actions(root):
    rows, path = _manual_events(root)
    if rows is None:
        return finding("CORPORATE_ACTION_VERIFICATION", "UNKNOWN", "Không có data/corporate_actions.csv.")
    docs = _ca_manifest(root) or []
    by_ticker = {}
    for doc in docs:
        ticker = doc.get("ticker")
        if ticker and ticker not in by_ticker:
            by_ticker[ticker] = doc
    pending = []
    for row in rows:
        status = (row.get("source_status") or "").strip()
        if status == VERIFIED_STATUS:
            continue
        doc = by_ticker.get(row.get("ticker")) or {}
        pending.append({
            "ticker": row.get("ticker"),
            "csv_ex_date": row.get("ex_date"),
            "csv_type": row.get("type"),
            "csv_ratio": row.get("ratio"),
            "csv_source_status": status or None,
            "evidence_source_id": doc.get("source_id"),
            "official_ex_date": doc.get("official_ex_date"),
            "published_at": doc.get("published_at"),
            "published_at_status": doc.get("published_at_status"),
            "dates_match": (row.get("ex_date") == doc.get("official_ex_date")) if doc.get("official_ex_date") else None,
        })
    if not rows:
        return finding(
            "CORPORATE_ACTION_VERIFICATION", "PASS",
            "CSV sự kiện quyền không có dòng nhập tay. Không có gì để xác nhận từ bước nhảy giá.",
            rows=0)
    if not pending:
        return finding(
            "CORPORATE_ACTION_VERIFICATION", "PASS",
            "Mọi dòng sự kiện quyền nhập tay có source_status DA_DOI_CHIEU.",
            rows=len(rows))
    return finding(
        "CORPORATE_ACTION_VERIFICATION", "FAIL",
        "Có sự kiện quyền nhập tay chưa ở trạng thái DA_DOI_CHIEU. "
        "Không xác nhận sự kiện từ bước nhảy giá. Ngày trên CSV lệch ngày official_ex_date của bản HOSE đã ghim "
        "thì vẫn là chưa xác minh, kể cả khi hash PDF khớp.",
        unverified=pending)


def check_unverified_chain(root, ca_finding):
    adjust_path, data_path = root / "engine" / "adjust.py", root / "engine" / "data.py"
    if not adjust_path.is_file() or not data_path.is_file():
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "UNKNOWN",
                       "Thiếu engine/adjust.py hoặc engine/data.py.")
    adjust_src = adjust_path.read_text(encoding="utf-8")
    data_src = data_path.read_text(encoding="utf-8")
    build_fn = _function_ast(adjust_src, "build_events")
    market_fn = _function_ast(data_src, "load_market")
    if build_fn is None or market_fn is None:
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
                       "Không thể đọc AST hàm build_events/load_market; không tự xác nhận cổng.")
    call = _calls_adjust_build_events(market_fn)
    mention = research_chain_requires_verified_status(adjust_src)
    verified_hint = load_market_uses_verified_chain(data_src)
    unverified_rows = (ca_finding.get("evidence") or {}).get("unverified") or []
    details = {"load_market_calls_adjust_build_events": call,
               "build_events_ast_mentions_source_status": mention,
               "load_market_ast_mentions_verified_function": verified_hint,
               "unverified_manual_rows": len(unverified_rows),
               "behavioral_proof_verified_gate": False}
    if call and not mention and unverified_rows:
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "FAIL",
                       "Có sự kiện chưa xác minh, load_market gọi build_events, "
                       "nhưng hàm build_events không đọc source_status. "
                       "Không được cho vào verified-adjusted khi chưa có cổng hành vi.", **details)
    return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
                   "Phân tích AST chỉ là dấu hiệu cú pháp; ngay cả khi source_status/verified_factors "
                   "xuất hiện trong mã, vẫn cần thử hành vi loại CAN_DOI_CHIEU trước khi cấp PASS.",
                   **details)

def _pdf_pages_text(path: Path):
    try:
        from pypdf import PdfReader
    except Exception as exc:  # noqa: BLE001 — môi trường thiếu pypdf thì không bịa nội dung
        return None, f"không import được pypdf ({exc})"
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text(extraction_mode="layout") or "")
        return pages, None
    except Exception as exc:  # noqa: BLE001
        return None, f"không đọc được PDF ({exc})"


def constituent_heading_line(page_text: str):
    """Dòng tiêu đề rổ VN30, không phải danh mục dự phòng. None nếu không thấy."""
    text = unicodedata.normalize("NFC", page_text)
    for line in text.splitlines():
        compact = " ".join(line.split())
        low = compact.lower()
        if "vn30" in low and "thành phần" in low and "dự phòng" not in low:
            return compact
    return None


def tickers_in_vn30_section(page_text: str):
    text = unicodedata.normalize("NFC", page_text)
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if constituent_heading_line(line):
            start = i
            break
    if start is None:
        return None
    chunk = []
    for line in lines[start + 1:]:
        compact = " ".join(unicodedata.normalize("NFC", line).split())
        if "dự phòng" in compact.lower() and "vn30" in compact.lower():
            break
        chunk.append(line)
    found = re.findall(r"(?m)^\s*\d+\s+([A-Z0-9]{3})\b", "\n".join(chunk))
    out = []
    for ticker in found:
        if ticker not in out:
            out.append(ticker)
    return out


def check_pdf_contents(root, docs):
    if not docs:
        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Không có manifest để mở PDF.")
    checked = []
    any_fail = False
    any_unknown = False
    for doc in docs:
        rel = doc.get("path") or ""
        if not str(rel).lower().endswith(".pdf"):
            continue
        path = root / rel
        item = {"source_id": doc.get("source_id"), "path": rel, "effective_date": doc.get("effective_date")}
        if not path.is_file():
            item["content_status"] = "UNKNOWN"
            item["reason"] = "thiếu tệp"
            any_unknown = True
            checked.append(item)
            continue
        pages, err = _pdf_pages_text(path)
        if err:
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = err
            any_unknown = True
            checked.append(item)
            continue
        heading_pages = []
        for i, text in enumerate(pages):
            heading = constituent_heading_line(text)
            if heading:
                heading_pages.append({"page": i + 1, "heading": heading})
        other = []
        for i, text in enumerate(pages):
            for heading in OTHER_INDEX_HEADINGS:
                if heading in text:
                    other.append({"page": i + 1, "heading": heading})
        item["vn30_heading_pages"] = heading_pages
        item["other_index_headings"] = other
        if not heading_pages:
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = "không thấy mục VN30 trong lớp chữ PDF; hash không thay cho việc này"
            any_unknown = True
            checked.append(item)
            continue
        parsed = None
        for item_page in heading_pages:
            parsed = tickers_in_vn30_section(pages[item_page["page"] - 1])
            if parsed:
                break
        expected = list(doc.get("members_after") or [])
        item["parsed_tickers"] = parsed or []
        item["parsed_count"] = len(parsed or [])
        item["expected_count"] = len(expected)
        if not parsed or len(parsed) != len(set(parsed)):
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = "không tách được danh sách mã không trùng trong mục VN30"
            any_unknown = True
        elif set(parsed) != set(expected) or len(parsed) != len(expected):
            item["content_status"] = "FAIL"
            item["only_in_pdf"] = sorted(set(parsed) - set(expected))
            item["only_in_manifest"] = sorted(set(expected) - set(parsed))
            any_fail = True
        else:
            item["content_status"] = "PASS"
        joined = "\n".join(pages)
        token = _dmy(doc["effective_date"]) if doc.get("effective_date") else None
        item["pdf_contains_effective_date_dmy"] = bool(token and token in joined)
        checked.append(item)
    if not checked:
        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Manifest không có PDF.")
    focus = next((x for x in checked if x.get("source_id") == "hose-2510691"), None)
    if any_fail:
        status = "FAIL"
        summary = "Có PDF mà mục VN30 đọc được không trùng members_after của manifest."
    elif any_unknown:
        status = "INCONCLUSIVE"
        summary = "Có PDF chưa đọc được mục VN30 hoặc không tách được đủ mã. Không nâng hash thành đã xác minh nội dung."
    else:
        status = "PASS"
        summary = "Mỗi PDF đã ghim có mục VN30 và danh sách đọc được trùng members_after. Ngày hiệu lực có thể nằm ở tin, không nằm trong PDF."
    return finding("PDF_VN30_CONTENT", status, summary, documents=checked, hose_2510691=focus)


def check_2510691_effective_date(root, docs, content_finding):
    focus = (content_finding.get("evidence") or {}).get("hose_2510691")
    news = next((d for d in docs or [] if d.get("source_id") == "hose-2510691-news"), None)
    if focus is None and news is None:
        return finding("HOSE_2510691_SCOPE", "UNKNOWN", "Không có hồ sơ hose-2510691 trong manifest.")
    news_has_date = False
    news_title = None
    if news and (root / news.get("path", "")).is_file():
        raw = (root / news["path"]).read_text(encoding="utf-8")
        token = _dmy(news["effective_date"]) if news.get("effective_date") else ""
        news_has_date = bool(token and _news_effective_statement(raw, news["effective_date"]))
        try:
            news_title = (_load_json(root / news["path"]).get("data") or {}).get("title")
        except json.JSONDecodeError:
            news_title = None
    pdf_has_date = bool(focus and focus.get("pdf_contains_effective_date_dmy"))
    pdf_match = bool(focus and focus.get("content_status") == "PASS")
    other = (focus or {}).get("other_index_headings") or []
    if pdf_match and news_has_date and not pdf_has_date:
        status = "PASS"
        summary = (
            "hose-2510691 là PDF tên VNAllshare kỳ 10/2026 và có mục «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN "
            "CỦA CHỈ SỐ VN30» in đủ 30 mã, trùng members_after. Ngày hiệu lực 16/11/2026 đọc từ tin HOSE đã ghim, "
            "không thấy dạng 16/11/2026 trong chữ PDF. Các mục chỉ số khác trong cùng tệp không phải rổ VN30."
        )
    elif pdf_match and pdf_has_date:
        status = "PASS"
        summary = "PDF 2510691 có mục VN30 trùng manifest và có chữ ngày hiệu lực."
    elif focus and focus.get("content_status") == "FAIL":
        status = "FAIL"
        summary = "Mục VN30 của PDF 2510691 không trùng members_after."
    else:
        status = "INCONCLUSIVE"
        summary = "Chưa đủ chữ để kết luận vừa thành phần vừa ngày hiệu lực của hồ sơ 2510691."
    return finding(
        "HOSE_2510691_SCOPE", status, summary,
        pdf_membership_matches=pdf_match,
        pdf_contains_effective_date=pdf_has_date,
        news_contains_effective_date=news_has_date,
        news_title=news_title,
        other_index_headings=other)


def _news_effective_statement(raw: str, effective_date: str):
    """Chỉ đọc lời công bố trong summary, không tìm ngày ở metadata/comment ngoài."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return False
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("summary"), str):
        return False
    summary = re.sub(r"<[^>]+>", " ", data["summary"])
    summary = summary.replace("&nbsp;", " ")
    token = _dmy(effective_date)
    return token in summary and "hiệu lực" in summary.lower()


def check_news_effective_dates(root, docs):
    if not docs:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Không có manifest.")
    checked = []
    for doc in docs:
        rel = doc.get("path") or ""
        if not rel.endswith(".json"):
            continue
        effective = doc.get("effective_date")
        path = root / rel
        row = {"source_id": doc.get("source_id"), "path": rel, "effective_date": effective}
        if not effective or not path.is_file():
            row["status"] = "UNKNOWN"
        else:
            present = _news_effective_statement(path.read_text(encoding="utf-8"), effective)
            row["token"] = _dmy(effective)
            row["present_in_announcement_summary"] = present
            row["status"] = "PASS" if present else "FAIL"
        checked.append(row)
    if not checked:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Manifest không có JSON tin.")
    if any(row["status"] == "FAIL" for row in checked):
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "FAIL",
                       "Có bản tin không chứng minh ngày hiệu lực trong lời công bố (summary).",
                       documents=checked)
    if any(row["status"] == "UNKNOWN" for row in checked):
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN",
                       "Có tin thiếu ngày hoặc không mở được.", documents=checked)
    return finding("NEWS_EFFECTIVE_DATE_TEXT", "PASS",
                   "Các bản tin đã ghim có ngày hiệu lực trong phần summary, không chỉ metadata.",
                   documents=checked)

def check_microstructure(root, cfg):
    costs = (cfg or {}).get("costs") or {}
    quality = (cfg or {}).get("quality") or {}
    trades = root / "paper" / "trades.csv"
    n_trades = None
    if trades.is_file():
        with trades.open(encoding="utf-8", newline="") as f:
            n_trades = max(0, sum(1 for _ in f) - 1)
    return finding(
        "MARKET_MICROSTRUCTURE_ASSUMPTIONS", "INCONCLUSIVE",
        "Phí, thuế, trượt giá, lô và biên độ là giả định trong config hoặc hằng số giấy. "
        "Chưa có đối chiếu lệnh khớp thật. Không chứng minh được khả năng khớp.",
        costs=costs, price_limit=quality.get("price_limit"), lot_size=(cfg or {}).get("lot_size"),
        paper_trade_rows=n_trades)


def _status_map(findings):
    return {item["id"]: item["status"] for item in findings}


def conclude(findings):
    """Cổng fail-closed: thiếu bất kỳ kiểm tra bắt buộc nào => không READY."""
    st = _status_map(findings)
    critical = (
        "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
        "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
        "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
        "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
        "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
        "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
        "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE", "NEWS_EFFECTIVE_DATE_TEXT",
        "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
    )
    blocked = {k: st.get(k) for k in critical if st.get(k) == "FAIL"}
    unknown = {k: st.get(k) for k in critical
               if st.get(k) in ("INCONCLUSIVE", "UNKNOWN", None)}
    invalid = {k: st.get(k) for k in critical if st.get(k) is not None and st.get(k) not in (
        "PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")}
    if blocked or invalid:
        return "NOT_READY", ("Kiểm tra bắt buộc FAIL/không hợp lệ: "
                             + ", ".join(sorted(set(blocked) | set(invalid))))
    if unknown:
        return "INCONCLUSIVE", ("Chưa đủ chứng cứ để cấp READY: "
                                + ", ".join(sorted(unknown)))
    return "READY", "Tất cả kiểm tra bắt buộc đều PASS; không phải xác nhận alpha."

def audit(root) -> dict:
    """Đọc cây root; không mở tệp để ghi hay nâng chứng cứ."""
    root = Path(root)
    cfg = _load_config(root)
    docs, _ = load_manifest_docs(root)
    rows, _ = load_vn30_rows(root)
    csv_finding, states = check_csv(rows)
    price_info = _price_tickers(root)
    findings = [
        check_provenance(root, docs),
        check_publication_order(docs),
        check_decision_cutoff(docs, cfg),
        csv_finding,
        check_adr_schema(rows),
        check_coverage(cfg, states),
        check_before_first(cfg, states),
        check_continuity(docs, states),
        check_engine_mode(root, cfg),
        check_config_vs_basket(cfg, states),
        check_ticker_presence(price_info, states),
        check_price_window_coverage(price_info, states, cfg),
        check_corporate_actions(root),
    ]
    findings.append(check_unverified_chain(root, findings[-1]))
    content = check_pdf_contents(root, docs)
    findings.append(content)
    findings.append(check_2510691_effective_date(root, docs, content))
    findings.append(check_news_effective_dates(root, docs))
    findings.append(check_microstructure(root, cfg))
    conclusion, reason = conclude(findings)
    first = states[0][0] if states else None
    return {
        "tool": "pit001_audit",
        "read_only": True,
        "alpha_claim": False,
        "conclusion": conclusion,
        "conclusion_reason": reason,
        "research_start": ((cfg or {}).get("data") or {}).get("start"),
        "first_pinned_membership_date": first,
        "eligible_window": None if conclusion != "READY" else {
            "from": ((cfg or {}).get("data") or {}).get("start"),
            "note": "Kiểm tra trên cây chỉ định; không phải bằng chứng alpha.",
        },
        "findings": findings,
    }

def main(argv=None) -> int:
    import argparse, sys
    parser = argparse.ArgumentParser(description="PIT-001 kiểm toán chỉ đọc")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    json.dump(audit(args.root), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
~~~~

# PHẦN B — UNIFIED DIFF ĐẦY ĐỦ CỦA PR #69 (5 TỆP)

Bốn tệp mới có toàn bộ dòng dưới dạng `+`; workflow đã tồn tại nên diff chỉ chứa phần thay đổi và ngữ cảnh (toàn bộ workflow nằm ở PHẦN A).

~~~~diff
diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
--- a/.github/workflows/tests.yml
+++ b/.github/workflows/tests.yml
@@ -15,7 +15,7 @@ jobs:
     runs-on: ubuntu-latest
     timeout-minutes: 30
     env:
-      UNITTEST: "test_laws_validate test_ledger_compat test_ledger_resolution test_knowledge_notes test_governance test_timing_lock test_source_original test_directional_accuracy test_measurement_integration test_scorecard_refresh test_b1_engine_bridge test_verified_adjust test_corporate_action_evidence test_corporate_action_evidence_2026h2 test_vn30_history test_forecast_candidates"
+      UNITTEST: "test_laws_validate test_ledger_compat test_ledger_resolution test_knowledge_notes test_governance test_timing_lock test_source_original test_directional_accuracy test_measurement_integration test_scorecard_refresh test_b1_engine_bridge test_verified_adjust test_corporate_action_evidence test_corporate_action_evidence_2026h2 test_vn30_history test_forecast_candidates test_pit001_audit"
       SCRIPTS: "test_no_lookahead test_adjustment test_ingest_errors test_ledger_pipeline test_quality_gate test_llm_review_budget"
     steps:
       - uses: actions/checkout@v4
@@ -33,6 +33,12 @@ jobs:
             n=$(basename "$f" .py)
             echo " $UNITTEST $SCRIPTS " | grep -q " $n " || { echo "Tep $f chua duoc dua vao tests.yml"; exit 1; }
           done
+      - name: PIT-001 replay deterministic (read-only)
+        run: |
+          python tools/pit001_audit.py > /tmp/pit001_a.json
+          python tools/pit001_audit.py > /tmp/pit001_b.json
+          cmp /tmp/pit001_a.json /tmp/pit001_b.json
+          python -c 'import json; x=json.load(open("/tmp/pit001_a.json")); print("PIT-001:",x["conclusion"],"findings=",len(x["findings"]))'
       - name: Test dang unittest (luat, Ledger, phan dinh, so thu L-06)
         run: python -m pytest -q $(for n in $UNITTEST; do printf "tests/%s.py " "$n"; done)
       - name: Test dang script cu cua engine (moi tep mot tien trinh rieng, khong dung chung TTC_HOME)
diff --git a/reports/PIT-001_20261121.json b/reports/PIT-001_20261121.json
new file mode 100644
--- /dev/null
+++ b/reports/PIT-001_20261121.json
@@ -0,0 +1,1045 @@
+{
+  "alpha_claim": false,
+  "conclusion": "NOT_READY",
+  "conclusion_reason": "Kiểm tra bắt buộc FAIL/không hợp lệ: ADR0008_SCHEMA, CONFIG_VS_EVIDENCED_BASKET, CORPORATE_ACTION_VERIFICATION, ENGINE_UNIVERSE_MODE, PRICE_WINDOW_COVERAGE, TICKER_PRESENCE, UNIVERSE_COVERAGE, UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
+  "eligible_window": null,
+  "findings": [
+    {
+      "evidence": {
+        "matched": [
+          {
+            "bytes": 1045,
+            "path": "data/evidence/vn30_reviews/hose-2388633/news.json",
+            "sha256": "76d1b776e0fc92199cf9249e0cb1a69e5aa9e7d724db15462d75e0f05ff6956a",
+            "source_id": "hose-2388633-news"
+          },
+          {
+            "bytes": 687177,
+            "path": "data/evidence/vn30_reviews/hose-2388633/20250716 CBTT-Danh muc thanh phan HOSE-Index thang 7.2025.pdf",
+            "sha256": "8573aaed26f2f087ac30567b1c943e4112a85f6c3efc6a57faa80b7b3f020eae",
+            "source_id": "hose-2388633"
+          },
+          {
+            "bytes": 1061,
+            "path": "data/evidence/vn30_reviews/hose-2432828/news.json",
+            "sha256": "90e46883d3b0ef72c0ebba8ba0165ba338cea3c7735ed92ad0b9e832c5558ba3",
+            "source_id": "hose-2432828-news"
+          },
+          {
+            "bytes": 710524,
+            "path": "data/evidence/vn30_reviews/hose-2432828/21012026 CBTT Danh sach thanh phan HOSE-Index thang 1.2026 update.pdf",
+            "sha256": "67f0087e74cd21c1f24b364403bf176db8a39732ef65847d56ea85b316fb6f7f",
+            "source_id": "hose-2432828"
+          },
+          {
+            "bytes": 11616,
+            "path": "data/evidence/vn30_reviews/hose-2460387/news.json",
+            "sha256": "d883018f2f93fc26fec2aa70bff8e9e06338c335ae49ba66fda0cdccad796e90",
+            "source_id": "hose-2460387"
+          },
+          {
+            "bytes": 1052,
+            "path": "data/evidence/vn30_reviews/hose-2479382/news.json",
+            "sha256": "cf574c5e63143d5b74bc062f03bbf91ca276164f9c8d7d5e15f4c242f93f675b",
+            "source_id": "hose-2479382-news"
+          },
+          {
+            "bytes": 737357,
+            "path": "data/evidence/vn30_reviews/hose-2479382/15072026 CBTT - Danh muc thanh phan HOSE-Index thang 7.2026.pdf",
+            "sha256": "441799b3afbc4f29f8b53ce6ef3b500b9121a4d032ca4cfeb1d4aa6e14407879",
+            "source_id": "hose-2479382"
+          },
+          {
+            "bytes": 1092,
+            "path": "data/evidence/vn30_reviews/hose-2510691/news.json",
+            "sha256": "fe6d4d88fd6285f799bedd33f9f31535e5d40051cf283790ed05d8d0e6937ed3",
+            "source_id": "hose-2510691-news"
+          },
+          {
+            "bytes": 416988,
+            "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
+            "sha256": "ca0c5ee6fc20234ea7c0dff93f0b0a5eac4bb16df93f9b36268c0ffadaa567d4",
+            "source_id": "hose-2510691"
+          }
+        ]
+      },
+      "id": "PROVENANCE_HASH",
+      "status": "PASS",
+      "summary": "Mọi tệp kê trong manifest VN30 khớp SHA-256 và số byte. Việc này không xác minh nội dung."
+    },
+    {
+      "evidence": {
+        "checked": 9
+      },
+      "id": "PUBLICATION_BEFORE_USE",
+      "status": "PASS",
+      "summary": "Với mọi tài liệu có đủ hai ngày, ngày công bố theo giờ Việt Nam không sau ngày hiệu lực."
+    },
+    {
+      "evidence": {
+        "decision_time_local": null
+      },
+      "id": "DECISION_TIME_OF_KNOWLEDGE",
+      "status": "INCONCLUSIVE",
+      "summary": "Chưa đăng ký giờ ra quyết định theo ngày giao dịch (research.decision_time_local). So published_on <= effective_date không chứng minh có thể dùng ngay trong phiên."
+    },
+    {
+      "evidence": {
+        "states": [
+          {
+            "effective_date": "2025-08-04",
+            "members": [
+              "ACB",
+              "BCM",
+              "BID",
+              "CTG",
+              "DGC",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MSN",
+              "MWG",
+              "PLX",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TPB",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VRE"
+            ]
+          },
+          {
+            "effective_date": "2026-02-02",
+            "members": [
+              "ACB",
+              "BID",
+              "CTG",
+              "DGC",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MSN",
+              "MWG",
+              "PLX",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TPB",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ]
+          },
+          {
+            "effective_date": "2026-05-13",
+            "members": [
+              "ACB",
+              "BID",
+              "BSR",
+              "CTG",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MSN",
+              "MWG",
+              "PLX",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TPB",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ]
+          },
+          {
+            "effective_date": "2026-08-03",
+            "members": [
+              "ACB",
+              "BID",
+              "BSR",
+              "CTG",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MCH",
+              "MSN",
+              "MWG",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TCX",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ]
+          }
+        ]
+      },
+      "id": "CSV_INTERNAL",
+      "status": "PASS",
+      "summary": "CSV dựng lại được các mốc, mỗi mốc đúng 30 mã. Không suy ra thành phần trước mốc đầu tiên."
+    },
+    {
+      "evidence": {
+        "actual_columns": [
+          "effective_date",
+          "ticker",
+          "action",
+          "source_id"
+        ],
+        "adr0008_columns": [
+          "effective_date",
+          "ticker",
+          "change",
+          "source_url",
+          "source_status"
+        ]
+      },
+      "id": "ADR0008_SCHEMA",
+      "status": "FAIL",
+      "summary": "CSV không theo khuôn ADR-0008 (effective_date,ticker,change,source_url,source_status). Không được tự ghi đè CSV trong PIT-001. Khuôn đang khóa bởi test là cột action/source_id."
+    },
+    {
+      "evidence": {
+        "first_evidence_date": "2025-08-04",
+        "research_start": "2016-01-01",
+        "uncovered_until_exclusive": "2025-08-04"
+      },
+      "id": "UNIVERSE_COVERAGE",
+      "status": "FAIL",
+      "summary": "Lịch sử thành phần đã ghim không phủ từ ngày đầu cửa sổ nghiên cứu. Không tự điền các kỳ thiếu."
+    },
+    {
+      "evidence": {
+        "applies": true,
+        "first_evidence_date": "2025-08-04",
+        "research_start": "2016-01-01"
+      },
+      "id": "MEMBERSHIP_BEFORE_FIRST_EVIDENCE",
+      "status": "UNKNOWN",
+      "summary": "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN."
+    },
+    {
+      "evidence": {
+        "gaps": [
+          {
+            "after": "2025-08-04",
+            "before": "2026-02-02",
+            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
+          },
+          {
+            "after": "2026-02-02",
+            "before": "2026-05-13",
+            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
+          },
+          {
+            "after": "2026-05-13",
+            "before": "2026-08-03",
+            "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). Việc không thấy tệp không chứng minh rổ không đổi."
+          }
+        ],
+        "names_copied_from_other_document": [
+          {
+            "effective_date": "2025-08-04",
+            "names_copied_from": "hose-2388633",
+            "source_id": "hose-2388633-news"
+          },
+          {
+            "effective_date": "2026-02-02",
+            "names_copied_from": "hose-2432828",
+            "source_id": "hose-2432828-news"
+          },
+          {
+            "effective_date": "2026-05-13",
+            "names_copied_from": "hose-2432828",
+            "source_id": "hose-2460387"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "names_copied_from": "hose-2479382",
+            "source_id": "hose-2479382-news"
+          },
+          {
+            "effective_date": "2026-11-16",
+            "names_copied_from": "hose-2510691",
+            "source_id": "hose-2510691-news"
+          }
+        ]
+      },
+      "id": "CONTINUITY_BETWEEN_REVIEWS",
+      "status": "UNKNOWN",
+      "summary": "Khoảng giữa các mốc đã ghim không được coi là đã chứng minh liên tục. Bản tin chép danh sách từ PDF kỳ trước không phải là in lại đủ 30 mã."
+    },
+    {
+      "evidence": {
+        "universe_basis": "CURRENT"
+      },
+      "id": "ENGINE_UNIVERSE_MODE",
+      "status": "FAIL",
+      "summary": "Cấu hình khai CURRENT: không thể chứng nhận chọn universe theo từng ngày."
+    },
+    {
+      "evidence": {
+        "config_count": 30,
+        "csv_state_as_of": "2026-08-03",
+        "evidence_count": 30,
+        "in_config_not_in_csv_state": [
+          "BCM",
+          "BVH",
+          "PLX",
+          "POW",
+          "TPB"
+        ],
+        "in_csv_state_not_in_config": [
+          "BSR",
+          "LPB",
+          "MCH",
+          "TCX",
+          "VPL"
+        ]
+      },
+      "id": "CONFIG_VS_EVIDENCED_BASKET",
+      "status": "FAIL",
+      "summary": "Danh sách cố định trong config không trùng rổ dựng từ CSV tại mốc cuối. Đây là lệch thành phần, không phải khuyến nghị giao dịch."
+    },
+    {
+      "evidence": {
+        "members_ever_in_csv": [
+          "ACB",
+          "BCM",
+          "BID",
+          "BSR",
+          "CTG",
+          "DGC",
+          "FPT",
+          "GAS",
+          "GVR",
+          "HDB",
+          "HPG",
+          "LPB",
+          "MBB",
+          "MCH",
+          "MSN",
+          "MWG",
+          "PLX",
+          "SAB",
+          "SHB",
+          "SSB",
+          "SSI",
+          "STB",
+          "TCB",
+          "TCX",
+          "TPB",
+          "VCB",
+          "VHM",
+          "VIB",
+          "VIC",
+          "VJC",
+          "VNM",
+          "VPB",
+          "VPL",
+          "VRE"
+        ],
+        "members_without_any_price_row": [
+          "BSR",
+          "DGC",
+          "LPB",
+          "MCH",
+          "TCX",
+          "VPL"
+        ],
+        "paths": [
+          "data/store/prices.csv.gz",
+          "data/store/prices/2026-11.csv"
+        ],
+        "price_first": "2016-01-04",
+        "price_last": "2026-11-20",
+        "price_rows": 73402,
+        "price_tickers": [
+          "ACB",
+          "BCM",
+          "BID",
+          "BVH",
+          "CTG",
+          "FPT",
+          "GAS",
+          "GVR",
+          "HDB",
+          "HPG",
+          "MBB",
+          "MSN",
+          "MWG",
+          "PLX",
+          "POW",
+          "SAB",
+          "SHB",
+          "SSB",
+          "SSI",
+          "STB",
+          "TCB",
+          "TPB",
+          "VCB",
+          "VHM",
+          "VIB",
+          "VIC",
+          "VJC",
+          "VNM",
+          "VPB",
+          "VRE"
+        ],
+        "priced_but_never_in_pinned_baskets": [
+          "BVH",
+          "POW"
+        ]
+      },
+      "id": "TICKER_PRESENCE",
+      "status": "FAIL",
+      "summary": "Có mã từng nằm trong rổ ghim nhưng không có dòng giá."
+    },
+    {
+      "evidence": {
+        "feature_lookback": 121,
+        "horizon_days": 20,
+        "min_distinct_sessions_for_individual_ticker": 122,
+        "missing_dates_on_observed_market_calendar": [
+          {
+            "effective_date": "2025-08-04",
+            "examples": [
+              "2025-08-04",
+              "2025-08-05",
+              "2025-08-06"
+            ],
+            "missing_session_count": 130,
+            "ticker": "DGC"
+          },
+          {
+            "effective_date": "2025-08-04",
+            "examples": [
+              "2025-08-04",
+              "2025-08-05",
+              "2025-08-06"
+            ],
+            "missing_session_count": 130,
+            "ticker": "LPB"
+          },
+          {
+            "effective_date": "2026-02-02",
+            "examples": [
+              "2026-02-02",
+              "2026-02-03",
+              "2026-02-04"
+            ],
+            "missing_session_count": 72,
+            "ticker": "DGC"
+          },
+          {
+            "effective_date": "2026-02-02",
+            "examples": [
+              "2026-02-02",
+              "2026-02-03",
+              "2026-02-04"
+            ],
+            "missing_session_count": 72,
+            "ticker": "LPB"
+          },
+          {
+            "effective_date": "2026-02-02",
+            "examples": [
+              "2026-02-02",
+              "2026-02-03",
+              "2026-02-04"
+            ],
+            "missing_session_count": 72,
+            "ticker": "VPL"
+          },
+          {
+            "effective_date": "2026-05-13",
+            "examples": [
+              "2026-05-13",
+              "2026-05-14",
+              "2026-05-15"
+            ],
+            "missing_session_count": 58,
+            "ticker": "BSR"
+          },
+          {
+            "effective_date": "2026-05-13",
+            "examples": [
+              "2026-05-13",
+              "2026-05-14",
+              "2026-05-15"
+            ],
+            "missing_session_count": 58,
+            "ticker": "LPB"
+          },
+          {
+            "effective_date": "2026-05-13",
+            "examples": [
+              "2026-05-13",
+              "2026-05-14",
+              "2026-05-15"
+            ],
+            "missing_session_count": 58,
+            "ticker": "VPL"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "examples": [
+              "2026-08-03",
+              "2026-08-04",
+              "2026-08-05"
+            ],
+            "missing_session_count": 80,
+            "ticker": "BSR"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "examples": [
+              "2026-08-03",
+              "2026-08-04",
+              "2026-08-05"
+            ],
+            "missing_session_count": 80,
+            "ticker": "LPB"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "examples": [
+              "2026-08-03",
+              "2026-08-04",
+              "2026-08-05"
+            ],
+            "missing_session_count": 80,
+            "ticker": "MCH"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "examples": [
+              "2026-08-03",
+              "2026-08-04",
+              "2026-08-05"
+            ],
+            "missing_session_count": 80,
+            "ticker": "TCX"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "examples": [
+              "2026-08-03",
+              "2026-08-04",
+              "2026-08-05"
+            ],
+            "missing_session_count": 80,
+            "ticker": "VPL"
+          }
+        ],
+        "missing_tickers": [
+          "BSR",
+          "DGC",
+          "LPB",
+          "MCH",
+          "TCX",
+          "VPL"
+        ],
+        "official_exchange_calendar_verified": false,
+        "short_series": [
+          {
+            "distinct_sessions": 0,
+            "ticker": "BSR"
+          },
+          {
+            "distinct_sessions": 0,
+            "ticker": "DGC"
+          },
+          {
+            "distinct_sessions": 0,
+            "ticker": "LPB"
+          },
+          {
+            "distinct_sessions": 0,
+            "ticker": "MCH"
+          },
+          {
+            "distinct_sessions": 0,
+            "ticker": "TCX"
+          },
+          {
+            "distinct_sessions": 0,
+            "ticker": "VPL"
+          }
+        ]
+      },
+      "id": "PRICE_WINDOW_COVERAGE",
+      "status": "FAIL",
+      "summary": "Thiếu mã, chuỗi quá ngắn hoặc thiếu ngày giá trong phiên có dữ liệu cho mã khác. Chưa xét liệu lịch phiên suy từ kho có đầy đủ hay không."
+    },
+    {
+      "evidence": {
+        "unverified": [
+          {
+            "csv_ex_date": "2024-06-11",
+            "csv_ratio": "2.0",
+            "csv_source_status": "CAN_DOI_CHIEU",
+            "csv_type": "stock_dividend",
+            "dates_match": false,
+            "evidence_source_id": "hose-1705374",
+            "official_ex_date": "2024-06-20",
+            "published_at": null,
+            "published_at_status": "CHUA_XAC_MINH",
+            "ticker": "TCB"
+          },
+          {
+            "csv_ex_date": "2025-03-03",
+            "csv_ratio": "1.495",
+            "csv_source_status": "CAN_DOI_CHIEU",
+            "csv_type": "stock_dividend",
+            "dates_match": false,
+            "evidence_source_id": "hose-1753594",
+            "official_ex_date": "2025-03-12",
+            "published_at": null,
+            "published_at_status": "CHUA_XAC_MINH",
+            "ticker": "VCB"
+          }
+        ]
+      },
+      "id": "CORPORATE_ACTION_VERIFICATION",
+      "status": "FAIL",
+      "summary": "Có sự kiện quyền nhập tay chưa ở trạng thái DA_DOI_CHIEU. Không xác nhận sự kiện từ bước nhảy giá. Ngày trên CSV lệch ngày official_ex_date của bản HOSE đã ghim thì vẫn là chưa xác minh, kể cả khi hash PDF khớp."
+    },
+    {
+      "evidence": {
+        "behavioral_proof_verified_gate": false,
+        "build_events_ast_mentions_source_status": false,
+        "load_market_ast_mentions_verified_function": false,
+        "load_market_calls_adjust_build_events": true,
+        "unverified_manual_rows": 2
+      },
+      "id": "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
+      "status": "FAIL",
+      "summary": "Có sự kiện chưa xác minh, load_market gọi build_events, nhưng hàm build_events không đọc source_status. Không được cho vào verified-adjusted khi chưa có cổng hành vi."
+    },
+    {
+      "evidence": {
+        "documents": [
+          {
+            "content_status": "PASS",
+            "effective_date": "2025-08-04",
+            "expected_count": 30,
+            "other_index_headings": [],
+            "parsed_count": 30,
+            "parsed_tickers": [
+              "ACB",
+              "BCM",
+              "BID",
+              "CTG",
+              "DGC",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MSN",
+              "MWG",
+              "PLX",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TPB",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VRE"
+            ],
+            "path": "data/evidence/vn30_reviews/hose-2388633/20250716 CBTT-Danh muc thanh phan HOSE-Index thang 7.2025.pdf",
+            "pdf_contains_effective_date_dmy": false,
+            "source_id": "hose-2388633",
+            "vn30_heading_pages": [
+              {
+                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
+                "page": 1
+              }
+            ]
+          },
+          {
+            "content_status": "PASS",
+            "effective_date": "2026-02-02",
+            "expected_count": 30,
+            "other_index_headings": [],
+            "parsed_count": 30,
+            "parsed_tickers": [
+              "ACB",
+              "BID",
+              "CTG",
+              "DGC",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MSN",
+              "MWG",
+              "PLX",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TPB",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ],
+            "path": "data/evidence/vn30_reviews/hose-2432828/21012026 CBTT Danh sach thanh phan HOSE-Index thang 1.2026 update.pdf",
+            "pdf_contains_effective_date_dmy": false,
+            "source_id": "hose-2432828",
+            "vn30_heading_pages": [
+              {
+                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
+                "page": 1
+              }
+            ]
+          },
+          {
+            "content_status": "PASS",
+            "effective_date": "2026-08-03",
+            "expected_count": 30,
+            "other_index_headings": [],
+            "parsed_count": 30,
+            "parsed_tickers": [
+              "ACB",
+              "BID",
+              "BSR",
+              "CTG",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MCH",
+              "MSN",
+              "MWG",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TCX",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ],
+            "path": "data/evidence/vn30_reviews/hose-2479382/15072026 CBTT - Danh muc thanh phan HOSE-Index thang 7.2026.pdf",
+            "pdf_contains_effective_date_dmy": false,
+            "source_id": "hose-2479382",
+            "vn30_heading_pages": [
+              {
+                "heading": "CÔNG BỐ THÔNG TIN DANH MỤC CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN30",
+                "page": 1
+              }
+            ]
+          },
+          {
+            "content_status": "PASS",
+            "effective_date": "2026-11-16",
+            "expected_count": 30,
+            "other_index_headings": [
+              {
+                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
+                "page": 2
+              },
+              {
+                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
+                "page": 4
+              },
+              {
+                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
+                "page": 6
+              }
+            ],
+            "parsed_count": 30,
+            "parsed_tickers": [
+              "ACB",
+              "BID",
+              "BSR",
+              "CTG",
+              "FPT",
+              "GAS",
+              "GVR",
+              "HDB",
+              "HPG",
+              "LPB",
+              "MBB",
+              "MCH",
+              "MSN",
+              "MWG",
+              "SAB",
+              "SHB",
+              "SSB",
+              "SSI",
+              "STB",
+              "TCB",
+              "TCX",
+              "VCB",
+              "VHM",
+              "VIB",
+              "VIC",
+              "VJC",
+              "VNM",
+              "VPB",
+              "VPL",
+              "VRE"
+            ],
+            "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
+            "pdf_contains_effective_date_dmy": false,
+            "source_id": "hose-2510691",
+            "vn30_heading_pages": [
+              {
+                "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
+                "page": 1
+              }
+            ]
+          }
+        ],
+        "hose_2510691": {
+          "content_status": "PASS",
+          "effective_date": "2026-11-16",
+          "expected_count": 30,
+          "other_index_headings": [
+            {
+              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
+              "page": 2
+            },
+            {
+              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
+              "page": 4
+            },
+            {
+              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
+              "page": 6
+            }
+          ],
+          "parsed_count": 30,
+          "parsed_tickers": [
+            "ACB",
+            "BID",
+            "BSR",
+            "CTG",
+            "FPT",
+            "GAS",
+            "GVR",
+            "HDB",
+            "HPG",
+            "LPB",
+            "MBB",
+            "MCH",
+            "MSN",
+            "MWG",
+            "SAB",
+            "SHB",
+            "SSB",
+            "SSI",
+            "STB",
+            "TCB",
+            "TCX",
+            "VCB",
+            "VHM",
+            "VIB",
+            "VIC",
+            "VJC",
+            "VNM",
+            "VPB",
+            "VPL",
+            "VRE"
+          ],
+          "path": "data/evidence/vn30_reviews/hose-2510691/II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf",
+          "pdf_contains_effective_date_dmy": false,
+          "source_id": "hose-2510691",
+          "vn30_heading_pages": [
+            {
+              "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30",
+              "page": 1
+            }
+          ]
+        }
+      },
+      "id": "PDF_VN30_CONTENT",
+      "status": "PASS",
+      "summary": "Mỗi PDF đã ghim có mục VN30 và danh sách đọc được trùng members_after. Ngày hiệu lực có thể nằm ở tin, không nằm trong PDF."
+    },
+    {
+      "evidence": {
+        "news_contains_effective_date": true,
+        "news_title": "HOSE: Cập nhật danh mục cổ phiếu thành phần của Chỉ số quy mô VNAllshare  kỳ tháng 10/2026",
+        "other_index_headings": [
+          {
+            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
+            "page": 2
+          },
+          {
+            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
+            "page": 4
+          },
+          {
+            "heading": "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
+            "page": 6
+          }
+        ],
+        "pdf_contains_effective_date": false,
+        "pdf_membership_matches": true
+      },
+      "id": "HOSE_2510691_SCOPE",
+      "status": "PASS",
+      "summary": "hose-2510691 là PDF tên VNAllshare kỳ 10/2026 và có mục «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30» in đủ 30 mã, trùng members_after. Ngày hiệu lực 16/11/2026 đọc từ tin HOSE đã ghim, không thấy dạng 16/11/2026 trong chữ PDF. Các mục chỉ số khác trong cùng tệp không phải rổ VN30."
+    },
+    {
+      "evidence": {
+        "documents": [
+          {
+            "effective_date": "2025-08-04",
+            "path": "data/evidence/vn30_reviews/hose-2388633/news.json",
+            "present_in_announcement_summary": true,
+            "source_id": "hose-2388633-news",
+            "status": "PASS",
+            "token": "04/08/2025"
+          },
+          {
+            "effective_date": "2026-02-02",
+            "path": "data/evidence/vn30_reviews/hose-2432828/news.json",
+            "present_in_announcement_summary": true,
+            "source_id": "hose-2432828-news",
+            "status": "PASS",
+            "token": "02/02/2026"
+          },
+          {
+            "effective_date": "2026-05-13",
+            "path": "data/evidence/vn30_reviews/hose-2460387/news.json",
+            "present_in_announcement_summary": true,
+            "source_id": "hose-2460387",
+            "status": "PASS",
+            "token": "13/05/2026"
+          },
+          {
+            "effective_date": "2026-08-03",
+            "path": "data/evidence/vn30_reviews/hose-2479382/news.json",
+            "present_in_announcement_summary": true,
+            "source_id": "hose-2479382-news",
+            "status": "PASS",
+            "token": "03/08/2026"
+          },
+          {
+            "effective_date": "2026-11-16",
+            "path": "data/evidence/vn30_reviews/hose-2510691/news.json",
+            "present_in_announcement_summary": true,
+            "source_id": "hose-2510691-news",
+            "status": "PASS",
+            "token": "16/11/2026"
+          }
+        ]
+      },
+      "id": "NEWS_EFFECTIVE_DATE_TEXT",
+      "status": "PASS",
+      "summary": "Các bản tin đã ghim có ngày hiệu lực trong phần summary, không chỉ metadata."
+    },
+    {
+      "evidence": {
+        "costs": {
+          "buy_fee": 0.0015,
+          "dividend_tax": 0.05,
+          "sell_fee": 0.0015,
+          "sell_tax": 0.001,
+          "slippage": 0.001
+        },
+        "lot_size": 100,
+        "paper_trade_rows": null,
+        "price_limit": 0.07
+      },
+      "id": "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
+      "status": "INCONCLUSIVE",
+      "summary": "Phí, thuế, trượt giá, lô và biên độ là giả định trong config hoặc hằng số giấy. Chưa có đối chiếu lệnh khớp thật. Không chứng minh được khả năng khớp."
+    }
+  ],
+  "first_pinned_membership_date": "2025-08-04",
+  "read_only": true,
+  "research_start": "2016-01-01",
+  "tool": "pit001_audit"
+}
diff --git a/reports/PIT-001_20261121.md b/reports/PIT-001_20261121.md
new file mode 100644
--- /dev/null
+++ b/reports/PIT-001_20261121.md
@@ -0,0 +1,124 @@
+# PIT-001 — Kiểm toán đúng thời điểm dữ liệu nghiên cứu VN30
+
+- Ngày chạy: 2026-11-21
+- Cây đọc: `main` `1d2f5c58acbeb3155118babc92bbb1bc9e06b382` cộng công cụ kiểm toán của PR này. Công cụ không sửa dữ liệu gốc.
+- Lệnh: `python3 tools/pit001_audit.py`
+- Máy đọc được: [reports/PIT-001_20261121.json](PIT-001_20261121.json)
+- Kết luận dùng dữ liệu này cho nghiên cứu alpha đáng tin: **NOT_READY**
+- Không tuyên bố vượt thị trường, vượt nhà đầu tư, hay có model ACTIVE.
+
+Hash SHA-256 khớp chứng minh byte không đổi. Nó không chứng minh nội dung đúng. Nội dung chỉ được ghi PASS khi chữ trong PDF hoặc tin đã ghim được đọc ra và đối được với manifest.
+
+## Kết quả kiểm toán
+
+| Hạng mục | Trạng thái | Việc đã thấy |
+|---|---|---|
+| PROVENANCE_HASH | PASS | Mọi tệp trong `data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json` khớp hash và số byte |
+| PUBLICATION_BEFORE_USE | PASS | Ngày công bố trên manifest, theo giờ Việt Nam, không sau ngày hiệu lực đã khai |
+| DECISION_TIME_OF_KNOWLEDGE | INCONCLUSIVE | Chưa đăng ký giờ quyết định tại mỗi phiên; ngày hiệu lực và ngày công bố không đủ để chứng minh thông tin đã biết trước thời điểm quyết định. |
+| NEWS_EFFECTIVE_DATE_TEXT | PASS | Năm tin JSON đều chứa đúng chuỗi ngày hiệu lực (04/08/2025, 02/02/2026, 13/05/2026, 03/08/2026, 16/11/2026) |
+| PDF_VN30_CONTENT | PASS | Bốn PDF có mục thành phần VN30; tập mã đọc được trùng `members_after` |
+| HOSE_2510691_SCOPE | PASS | Xem mục riêng bên dưới |
+| CSV_INTERNAL | PASS | 38 dòng ADD/REMOVE dựng được bốn mốc, mỗi mốc 30 mã, mốc đầu 2025-08-04 |
+| ADR0008_SCHEMA | FAIL | CSV đang là `effective_date,ticker,action,source_id`, không phải khuôn ADR-0008 `change,source_url,source_status`. Không ghi đè CSV |
+| UNIVERSE_COVERAGE | FAIL | `config.yaml` `data.start` là 2016-01-01; bản gốc đầu tiên là 2025-08-04 |
+| MEMBERSHIP_BEFORE_FIRST_EVIDENCE | UNKNOWN | Trước 2025-08-04 không suy thành phần |
+| CONTINUITY_BETWEEN_REVIEWS | UNKNOWN | Không có tệp nào khác trong các khoảng giữa mốc không chứng minh rổ đứng yên |
+| ENGINE_UNIVERSE_MODE | FAIL | `universe_basis: CURRENT`. `engine/data.py` nạp theo `CFG["universe"]`, không đọc `data/vn30_history.csv` |
+| CONFIG_VS_EVIDENCED_BASKET | FAIL | Lệch với rổ dựng tại mốc CSV cuối (2026-08-03, và trùng mục PDF 2026-11-16) |
+| TICKER_PRESENCE | FAIL | Kho giá 2016-01-04 đến 2026-11-20, 73402 dòng; thiếu mã từng trong rổ đã ghim. Chỉ đo có/không có dòng giá, không gọi là đủ phiên. |
+| PRICE_WINDOW_COVERAGE | FAIL | Thiếu mã và phiên dữ liệu ở các mốc đã ghim; lịch phiên chính thức và vintage giá vẫn chưa xác minh. Không được PASS chỉ vì mỗi mã có một dòng. |
+| CORPORATE_ACTION_VERIFICATION | FAIL | TCB và VCB vẫn `CAN_DOI_CHIEU`; ngày CSV lệch `official_ex_date`; `published_at` null |
+| UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN | FAIL | `load_market` gọi `adjust.build_events`. Hàm đó không đọc `source_status` trước khi có thể gán `APPLIED` |
+| MARKET_MICROSTRUCTURE_ASSUMPTIONS | INCONCLUSIVE | Phí, thuế, trượt giá, lô 100, biên độ 0.07 là giả định. Không có `paper/trades.csv` để chứng minh lệnh khớp |
+
+`universe_basis` không được chuyển sang `HISTORICAL` trong PR này. `engine/adjust.py`, `engine/research.py` và `config.yaml` không đổi. Bộ audit được siết cổng sau phản biện trên PR #69.
+
+## hose-2510691 (hiệu lực khai 2026-11-16)
+
+Tài liệu là PDF tên `II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf`, SHA-256 `ca0c5ee6fc20234ea7c0dff93f0b0a5eac4bb16df93f9b36268c0ffadaa567d4`, 416988 byte. Tin HOSE id 2510691 có tiêu đề cập nhật danh mục chỉ số quy mô VNAllshare.
+
+Đã đọc chữ PDF, không chỉ đọc tên tệp:
+
+- Trang 1, dòng tiêu đề: «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30», kỳ tháng 10/2026.
+- Đúng 30 mã, trùng `members_after`: ACB, BID, BSR, CTG, FPT, GAS, GVR, HDB, HPG, LPB, MBB, MCH, MSN, MWG, SAB, SHB, SSB, SSI, STB, TCB, TCX, VCB, VHM, VIB, VIC, VJC, VNM, VPB, VPL, VRE.
+- Cùng tệp còn mục VNMIDCAP (trang 2), VN100 (trang 4), VNSMALLCAP (trang 6). Những mục đó không phải rổ VN30.
+- Chữ PDF không chứa `16/11/2026`. Ngày hiệu lực nằm trong tin `hose-2510691-news`: các chỉ số quy mô VNAllshare có hiệu lực vào ngày 16/11/2026.
+- CSV không có dòng ADD/REMOVE ngày 2026-11-16. Rổ dựng sau mốc 2026-08-03 đã trùng 30 mã này, nên không có dòng không có nghĩa là thiếu bản gốc của kỳ này.
+
+`reports/G1_DATA_SPRINT0_20261120/A3_LO_HONG.md` nói tệp này không phải kỳ VN30 và chưa có bản gốc rổ sau 2026-08-03. Câu đó không đúng với mục VN30 trong PDF. `reports/VN30_UNIVERSE_DIFF_20261119.md` mô tả đúng mục và đúng 30 mã. Báo cáo cũ không bị sửa trong PR này.
+
+Ba PDF kỳ trước cũng đọc được mục thành phần (tiêu đề «CÔNG BỐ THÔNG TIN…», không phải «CẬP NHẬT…») và trùng `members_after`. Ngày hiệu lực của chúng cũng không nằm trong chữ PDF; chúng nằm trong tin JSON đã ghim. Tin `hose-2460387` xác nhận VN30 loại DGC, thêm BSR, hiệu lực 13/05/2026, và không in lại đủ 30 mã. 28 mã còn lại trên manifest được chép từ PDF kỳ 01/2026. Đó không phải xác minh độc lập cả rổ tại 2026-05-13.
+
+## Lệch rổ và lỗ giá
+
+Rổ config so với rổ đã dựng tại mốc cuối:
+
+- Có trong config, không còn trong rổ đó: BCM, BVH, PLX, POW, TPB.
+- Có trong rổ đó, không có trong config: BSR, LPB, MCH, TCX, VPL.
+
+Mã từng vào rổ đã ghim nhưng không có dòng giá: BSR, DGC, LPB, MCH, TCX, VPL.
+
+Mã có giá nhưng không nằm trong bất kỳ rổ đã ghim: BVH, POW.
+
+Không điền giá và không điền thành phần cho các kỳ chưa có PDF. Các kỳ từ 2016 đến trước 2025-08-04, cùng các khoảng giữa các mốc đã ghim, là UNKNOWN.
+
+## Sự kiện quyền chưa được xác minh
+
+Không kết luận sự kiện từ bước nhảy giá.
+
+| Mã | CSV | Trạng thái CSV | Bản HOSE | official_ex_date | published_at |
+|---|---|---|---|---|---|
+| TCB | 2024-06-11, stock_dividend, ratio 2.0 | CAN_DOI_CHIEU | hose-1705374 | 2024-06-20 | null, `CHUA_XAC_MINH` |
+| VCB | 2025-03-03, stock_dividend, ratio 1.495 | CAN_DOI_CHIEU | hose-1753594 | 2025-03-12 | null, `CHUA_XAC_MINH` |
+
+`engine/data.py` `load_market` vẫn nhân hệ số từ `engine/adjust.py`. `build_events` không xét `source_status`. Sự kiện chưa xác minh vẫn có thể thành `APPLIED` nếu tỷ lệ khớp biến động giá. Việc đó làm lệch chuỗi giá nghiên cứu. PR này không sửa `engine/adjust.py` (ADR-0009 điều 7 và lệnh PIT-001).
+
+## Alpha có chứng minh được không
+
+**NOT_READY.** Không có khoảng ngày nào đủ điều kiện để backtest point-in-time rồi gọi là alpha.
+
+Tập đã đủ để làm gì:
+
+- Đối chiếu byte và, với bốn PDF VN30, đối chiếu danh sách thành phần tại đúng ngày hiệu lực đã đọc từ tin. Chỉ những ngày đó, không phải cả quãng giữa hai ngày.
+- Không đủ để gán thành phần cho 2016-01-01 đến 2025-08-03.
+- Không đủ để nói rổ không đổi giữa hai lần công bố.
+- Không đủ để nghiên cứu các mã đã vào rổ nhưng chưa có giá.
+- Không đủ để coi giá điều chỉnh hiện hành là verified-adjusted.
+
+Chỉ số nghiên cứu trên cửa sổ 2016 đến nay vẫn chịu thiên lệch sống sót: engine dùng một danh sách cố định, và báo cáo chu kỳ đã gắn nhãn đó (ADR-0008). Nhãn không làm con số đúng.
+
+Giả định chưa chứng minh: phí mua/bán 0,0015, thuế bán 0,001, trượt giá 0,001, lô 100, khóa trần/sàn ở 95% biên độ, biên độ mặc định 0,07. Không có sổ lệnh giấy `paper/trades.csv` trong cây này. Không có đối chiếu khớp lệnh thật.
+
+`state/ENGINE_STATE.json` ngày 2026-11-20: 222 lần thử, 0 model ACTIVE, NAV giấy 1.000.000.000, sụt giảm giấy 0, `universe_basis` CURRENT. `reports/scorecard.json` cùng ngày: 6 dự báo, 0 resolved, 0 timing_valid, 3 cặp A/B, 1 cặp bất đồng thô bị chặn vì `legacy_unproven`, mẫu 194 không đổi. Những số này không được dùng để tuyên bố alpha. Không gian 13 feature × 3 model, top-k và horizon không bị đổi.
+
+`state/PROJECT_STATE.yaml` vẫn ghi thư viện 1/40 SOURCED và ghi chú KN-T2 DRAFT, chưa CITED. ADR-0007 vì vậy chưa mở lại engine kịch bản. ADR-0008 vẫn hoãn CVaR và tối ưu danh mục. PR này không triển khai các tầng đó.
+
+## Sửa cổng READY sau phản biện (ChatGPT OpenAI, 21/11/2026)
+
+Lượt sửa tiếp trên cùng PR #69 giữ nguyên nguồn/engine. Bản kiểm toán sử dụng **cổng fail-closed**: bất kỳ điều kiện bắt buộc nào FAIL dẫn đến NOT_READY; thiếu chứng cứ (UNKNOWN/INCONCLUSIVE) dẫn đến INCONCLUSIVE khi không có lỗi khác. Không một kiểm tra đơn lẻ nào tự chứng nhận full PIT.
+
+- Không coi comment hoặc string literal chứa `source_status`, `verified_factors`, `vn30_history` là xác minh hành vi. Kiểm tra AST chỉ hỗ trợ phát hiện cấu trúc; **PASS cho chuỗi verified hoặc historical selection vẫn yêu cầu phép thử hành vi độc lập**.
+- Độ phủ giá được tách thành `TICKER_PRESENCE` và `PRICE_WINDOW_COVERAGE`; một dòng giá không thể tạo PASS về cửa sổ nhiều phiên.
+- Có thêm `DECISION_TIME_OF_KNOWLEDGE`: chưa khai giờ quyết định thì INCONCLUSIVE, kể cả `PUBLICATION_BEFORE_USE` PASS.
+- Tin JSON phải nêu ngày hiệu lực trong phần **summary công bố**, không phải chỉ xuất hiện tình cờ trong metadata hoặc tiêu đề.
+- Ma trận test đối kháng bảo đảm FAIL/UNKNOWN/INCONCLUSIVE ở mọi cổng bắt buộc đều chặn READY.
+- Bộ audit tiếp tục **chỉ đọc**. Snapshot JSON đã được tái sinh từ đầu ra `PIT001_JSON` của GitHub Actions `44876139858` trên commit `6d638ad0` (SUCCESS); hai lần chạy audit tại cùng commit cho kết quả giống hệt nhau.
+- Test suite tại run này: **319 passed, 68 subtests passed**, 79 cảnh báo; toàn bộ bước CI bắt buộc kết thúc SUCCESS. Bản ghi JSON mới vẫn có kết luận **NOT_READY** và 18 findings. L-09/Owner chưa hoàn tất.
+
+## Điều kiện tối thiểu trước một baseline công bằng
+
+Chưa mở baseline. Muốn mở sau này, cùng lúc, không chọn lại sau khi nhìn kết quả:
+
+1. Thành phần từng ngày là UNKNOWN ở đâu thì ngày đó không vào kết luận. Không dùng rổ config để thế.
+2. Mọi mã trong cửa sổ đã chọn có giá, và sự kiện quyền chưa `DA_DOI_CHIEU` không vào chuỗi verified-adjusted.
+3. Đăng ký trước một lần thử trong không gian đang khóa. Không thêm feature, model, horizon, top-k, benchmark.
+4. Phí, trần/sàn, lệnh không khớp để là giả định thì phải ghi INCONCLUSIVE về khả năng khớp, không ghi là đã chứng minh.
+5. So với đúng benchmark đã định nghĩa. Không đổi tên VN-Index, VN30 hay bình quân 30 mã để chúng thành nhau.
+6. Kết quả âm hoặc không rõ phải được giữ. 0 model ACTIVE thì không promote.
+
+## Việc kế tiếp có tác động lớn nhất
+
+Thu và ghim PDF gốc HOSE cho các kỳ thành phần VN30 từ 2016 đến trước 2025-08-04. Không điền mã từ báo chí hay từ rổ hiện tại. Không có lớp đó thì mọi con số nghiên cứu trên cửa sổ engine đang chạy vẫn không phải point-in-time.
+
+Việc mã phải đi kèm, nhưng không làm trong PR này: PR riêng cho cổng `source_status` trên chuỗi giá nghiên cứu, vì TCB/VCB đang có thể sửa lịch sử giá khi chưa xác minh. ADR-0009 chưa cho sửa `engine/adjust.py` bằng PIT-001.
diff --git a/tests/test_pit001_audit.py b/tests/test_pit001_audit.py
new file mode 100644
--- /dev/null
+++ b/tests/test_pit001_audit.py
@@ -0,0 +1,305 @@
+"""PIT-001: fixture độc lập. Không đụng kho giá, config hay engine của repo khi dựng cây tạm."""
+import hashlib, json, unittest
+from pathlib import Path
+
+from tools import pit001_audit as pit
+
+ROOT = Path(__file__).resolve().parents[1]
+HEADING = pit.VN30_HEADING
+
+
+def _sha(text: str) -> str:
+    return hashlib.sha256(text.encode("utf-8")).hexdigest()
+
+
+def _members(n=30, prefix="A"):
+    # 30 mã giả, đúng 3 chữ, không trùng mã thật để fixture không bị đọc nhầm là khuyến nghị.
+    out = []
+    i = 0
+    while len(out) < n:
+        out.append(f"{prefix}{i:02d}"[-3:])
+        i += 1
+    return out
+
+
+class ParserTests(unittest.TestCase):
+    def test_vn30_section_stops_before_reserve_list(self):
+        names = [f"T{i:02d}" for i in range(30)]
+        lines = [f"    {i+1:2d}         {name}      Công ty" for i, name in enumerate(names)]
+        text = HEADING + "\n" + "\n".join(lines) + "\nDanh mục cổ phiếu dự phòng chỉ số VN30\n    1         ZZZ      ngoài rổ"
+        self.assertEqual(pit.tickers_in_vn30_section(text), names)
+
+    def test_missing_heading_is_none(self):
+        self.assertIsNone(pit.tickers_in_vn30_section("không có mục chỉ số\n    1         AAA      x"))
+
+
+class AuditFixtureTests(unittest.TestCase):
+    def setUp(self):
+        import tempfile
+        self.tmp = tempfile.TemporaryDirectory()
+        self.root = Path(self.tmp.name)
+
+    def tearDown(self):
+        self.tmp.cleanup()
+
+    def _snapshot(self):
+        h = hashlib.sha256()
+        for path in sorted(p for p in self.root.rglob("*") if p.is_file()):
+            h.update(str(path.relative_to(self.root)).encode())
+            h.update(path.read_bytes())
+        return h.hexdigest()
+
+    def _write(self, rel, text):
+        path = self.root / rel
+        path.parent.mkdir(parents=True, exist_ok=True)
+        path.write_text(text, encoding="utf-8")
+        return path
+
+    def _manifest(self, docs):
+        self._write("data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json",
+                    json.dumps({"source_documents": docs}, ensure_ascii=False))
+
+    def _doc(self, source_id, body, effective, published, members):
+        rel = f"data/evidence/vn30_reviews/{source_id}/note.txt"
+        self._write(rel, body)
+        return {
+            "source_id": source_id, "path": rel, "sha256": _sha(body), "bytes": len(body.encode("utf-8")),
+            "published_at": published, "effective_date": effective, "members_after": members,
+        }
+
+    def test_bad_hash_is_fail_and_audit_does_not_write(self):
+        body = "nguon"
+        doc = self._doc("s1", body, "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
+        doc["sha256"] = "0" * 64
+        self._manifest([doc])
+        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n")
+        before = self._snapshot()
+        result = pit.audit(self.root)
+        self.assertEqual(before, self._snapshot())
+        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")
+        self.assertTrue(result["read_only"])
+
+    def test_missing_source_file_is_fail(self):
+        self._manifest([{
+            "source_id": "s1", "path": "data/evidence/vn30_reviews/missing.txt",
+            "sha256": "abc", "bytes": 1, "published_at": "2024-01-01", "effective_date": "2024-01-02",
+            "members_after": [],
+        }])
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")
+
+    def test_published_after_effective_is_fail(self):
+        members = _members()
+        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-03T00:00:00Z", members)
+        self._manifest([doc])
+        rows = ["effective_date,ticker,action,source_id"]
+        for ticker in members:
+            rows.append(f"2024-01-02,{ticker},ADD,s1")
+        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "FAIL")
+
+    def test_missing_published_at_is_unknown(self):
+        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
+        doc["published_at"] = None
+        self._manifest([doc])
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "UNKNOWN")
+
+    def test_universe_short_of_research_start_is_fail_and_before_is_unknown(self):
+        members = _members()
+        doc = self._doc("s1", "ban goc", "2025-08-04", "2025-07-16T00:00:00Z", members)
+        self._manifest([doc])
+        rows = ["effective_date,ticker,action,source_id"]
+        for ticker in members:
+            rows.append(f"2025-08-04,{ticker},ADD,s1")
+        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
+        self._write("config.yaml", "universe_basis: CURRENT\ndata:\n  start: \"2016-01-01\"\nuniverse: [" + ", ".join(members) + "]\n")
+        result = pit.audit(self.root)
+        st = pit._status_map(result["findings"])
+        self.assertEqual(st["UNIVERSE_COVERAGE"], "FAIL")
+        self.assertEqual(st["MEMBERSHIP_BEFORE_FIRST_EVIDENCE"], "UNKNOWN")
+        self.assertEqual(st["CSV_INTERNAL"], "PASS")
+        self.assertNotEqual(result["conclusion"], "READY")
+
+    def test_incomplete_membership_is_fail(self):
+        members = _members(29)
+        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", members)
+        self._manifest([doc])
+        rows = ["effective_date,ticker,action,source_id"]
+        for ticker in members:
+            rows.append(f"2024-01-02,{ticker},ADD,s1")
+        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["CSV_INTERNAL"], "FAIL")
+
+    def test_unverified_event_enters_chain_when_adjust_ignores_status(self):
+        self._write("data/corporate_actions.csv",
+                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
+                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,CAN_DOI_CHIEU,chua doi chieu\n")
+        self._write("engine/adjust.py", "def build_events(close, observed, manual, yahoo):\n    status = 'APPLIED'\n    return status\n")
+        self._write("engine/data.py", "def load_market(as_of=None):\n    events = adjust.build_events(None, None, None, None)\n    return events\n")
+        result = pit.audit(self.root)
+        st = pit._status_map(result["findings"])
+        self.assertEqual(st["CORPORATE_ACTION_VERIFICATION"], "FAIL")
+        self.assertEqual(st["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "FAIL")
+
+    def test_verified_gate_is_pass_for_chain_check(self):
+        self._write("data/corporate_actions.csv",
+                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
+                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,DA_DOI_CHIEU,da doi chieu\n")
+        self._write("engine/adjust.py",
+                    "def build_events(close, observed, manual, yahoo):\n"
+                    "    source_status = manual\n"
+                    "    if source_status != 'DA_DOI_CHIEU':\n"
+                    "        return 'KHONG'\n"
+                    "    return 'APPLIED'\n")
+        self._write("engine/data.py", "def load_market(as_of=None):\n    return adjust.build_events(None, None, None, None)\n")
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "INCONCLUSIVE")
+
+    def test_schema_fail_never_certifies_ready(self):
+        members = _members()
+        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T10:00:00Z", members)
+        self._manifest([doc])
+        rows = ["effective_date,ticker,action,source_id"]
+        for ticker in members:
+            rows.append(f"2024-01-02,{ticker},ADD,s1")
+        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
+        self._write("config.yaml",
+                    "universe_basis: HISTORICAL\n"
+                    "data:\n  start: \"2024-01-02\"\n"
+                    "universe: [" + ", ".join(members) + "]\n")
+        self._write("engine/data.py",
+                    "def ingest(end=None):\n"
+                    "    history = open('data/vn30_history.csv').read()\n"
+                    "    return history\n"
+                    "def load_market(as_of=None):\n"
+                    "    return verified_factors()\n")
+        self._write("engine/adjust.py",
+                    "def build_events(close, observed, manual, yahoo):\n"
+                    "    source_status = 'DA_DOI_CHIEU'\n"
+                    "    return source_status\n")
+        self._write("data/corporate_actions.csv",
+                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n")
+        prices = ["date,ticker,close"]
+        for ticker in members:
+            prices.append(f"2024-01-02,{ticker},1")
+        self._write("data/store/prices/2024-01.csv", "\n".join(prices) + "\n")
+        before = self._snapshot()
+        result = pit.audit(self.root)
+        self.assertEqual(before, self._snapshot())
+        st = pit._status_map(result["findings"])
+        self.assertEqual(st["ADR0008_SCHEMA"], "FAIL")
+        self.assertEqual(st["UNIVERSE_COVERAGE"], "PASS")
+        self.assertEqual(st["ENGINE_UNIVERSE_MODE"], "INCONCLUSIVE")
+        self.assertEqual(st["TICKER_PRESENCE"], "PASS")
+        self.assertEqual(st["PROVENANCE_HASH"], "PASS")
+        self.assertEqual(result["conclusion"], "NOT_READY")
+        self.assertFalse(result["alpha_claim"])
+
+    def test_news_without_effective_token_is_fail(self):
+        rel = "data/evidence/vn30_reviews/n1/news.json"
+        self._write(rel, '{"data":{"summary":"khong ghi ngay hieu luc"}}')
+        blob = (self.root / rel).read_bytes()
+        self._manifest([{
+            "source_id": "n1", "path": rel, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob),
+            "published_at": "2024-01-01T00:00:00Z", "effective_date": "2024-01-02", "members_after": [],
+        }])
+        result = pit.audit(self.root)
+        self.assertEqual(pit._status_map(result["findings"])["NEWS_EFFECTIVE_DATE_TEXT"], "FAIL")
+
+    def test_schema_mismatch_does_not_invent_rows(self):
+        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n2024-01-02,ABC,ADD,s1\n")
+        result = pit.audit(self.root)
+        finding = next(item for item in result["findings"] if item["id"] == "ADR0008_SCHEMA")
+        self.assertEqual(finding["status"], "FAIL")
+        self.assertEqual(finding["evidence"]["actual_columns"], ["effective_date", "ticker", "action", "source_id"])
+
+
+class FailClosedMatrixTests(unittest.TestCase):
+    """Mỗi thiếu hụt trong hợp đồng đều ngăn READY, kể cả không có FAIL khác."""
+    def test_each_critical_fail_blocks_ready(self):
+        critical = (
+            "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
+            "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
+            "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
+            "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
+            "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
+            "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
+            "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE",
+            "NEWS_EFFECTIVE_DATE_TEXT", "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
+        )
+        baseline = [pit.finding(k, "PASS", "fixture") for k in critical]
+        self.assertEqual(pit.conclude(baseline)[0], "READY")
+        for key in critical:
+            for status in ("FAIL", "UNKNOWN", "INCONCLUSIVE"):
+                changed = [pit.finding(f["id"], status if f["id"] == key else "PASS", "fixture")
+                           for f in baseline]
+                got = pit.conclude(changed)[0]
+                want = "NOT_READY" if status == "FAIL" else "INCONCLUSIVE"
+                with self.subTest(key=key, status=status):
+                    self.assertEqual(got, want)
+        self.assertEqual(pit.conclude(baseline[:-1])[0], "INCONCLUSIVE")
+
+    def test_not_ready_overrides_other_missing_evidence(self):
+        rows = [pit.finding("PROVENANCE_HASH", "UNKNOWN", "x"),
+                pit.finding("ADR0008_SCHEMA", "FAIL", "x")]
+        self.assertEqual(pit.conclude(rows)[0], "NOT_READY")
+
+    def test_comments_and_literals_do_not_prove_verified_gate(self):
+        src = ("def build_events(a,b,c,d):\n"
+               "    # source_status is checked\n"
+               "    note = 'source_status'\n"
+               "    return 'APPLIED'\n")
+        self.assertFalse(pit.research_chain_requires_verified_status(src))
+        self.assertFalse(pit.load_market_uses_verified_chain(
+            "def load_market():\n    # verified_factors()\n    note = 'verified_factors'\n    return 1\n"))
+
+    def test_engine_historical_string_in_comment_is_not_proof(self):
+        import tempfile
+        with tempfile.TemporaryDirectory() as td:
+            root = Path(td)
+            (root / "engine").mkdir()
+            (root / "engine/data.py").write_text(
+                "def load_market():\n    # vn30_history is loaded\n"
+                "    path = 'vn30_history'\n    return path\n", encoding="utf-8")
+            result = pit.check_engine_mode(root, {"universe_basis":"HISTORICAL"})
+            self.assertEqual(result["status"], "INCONCLUSIVE")
+
+    def test_price_one_row_per_symbol_is_not_window_pass(self):
+        import tempfile
+        with tempfile.TemporaryDirectory() as td:
+            root = Path(td)
+            p = root / "data/store/prices/2024-01.csv"
+            p.parent.mkdir(parents=True)
+            p.write_text("date,ticker,close\n2024-01-02,AAA,1\n"
+                         "2024-01-02,BBB,1\n", encoding="utf-8")
+            info = pit._price_tickers(root)
+            states = [("2024-01-02", {"AAA", "BBB"})]
+            self.assertEqual(pit.check_ticker_presence(info, states)["status"], "PASS")
+            coverage = pit.check_price_window_coverage(info, states, {"horizon_days":20})
+            self.assertEqual(coverage["status"], "FAIL")
+
+    def test_publication_same_day_after_decision_is_fail(self):
+        docs = [{"source_id":"news", "published_at":"2026-11-02T09:00:00Z",
+                 "effective_date":"2026-11-02"}]   # 16:00 VN > 15:00 decision
+        cfg = {"research":{"decision_time_local":"15:00"}}
+        self.assertEqual(pit.check_publication_order(docs)["status"], "PASS")
+        self.assertEqual(pit.check_decision_cutoff(docs, cfg)["status"], "FAIL")
+        self.assertEqual(pit.check_decision_cutoff(docs, {})["status"], "INCONCLUSIVE")
+
+    def test_date_only_outside_news_summary_is_not_proof(self):
+        raw = '{"data":{"title":"13/05/2026", "summary":"Không có thông báo ngày hiệu lực"}}'
+        self.assertFalse(pit._news_effective_statement(raw, "2026-05-13"))
+
+    def test_missing_pdf_content_never_counts_as_pass(self):
+        import tempfile
+        with tempfile.TemporaryDirectory() as td:
+            root = Path(td)
+            docs = [{"source_id":"p", "path":"data/missing.pdf",
+                     "effective_date":"2026-11-16", "members_after":["AAA"]}]
+            self.assertEqual(pit.check_pdf_contents(root, docs)["status"], "INCONCLUSIVE")
+
+if __name__ == "__main__":
+    unittest.main()
diff --git a/tools/pit001_audit.py b/tools/pit001_audit.py
new file mode 100644
--- /dev/null
+++ b/tools/pit001_audit.py
@@ -0,0 +1,944 @@
+"""PIT-001 — kiểm toán chỉ đọc: đúng thời điểm, đủ thành phần, provenance.
+
+Không mạng. Không ghi kho giá, config, engine, ledger, luật hay manifest.
+Kết quả in JSON ra stdout. Hash khớp chỉ chứng minh byte không đổi, không chứng minh nội dung đúng.
+"""
+import ast, csv, gzip, hashlib, json, re, unicodedata
+from datetime import datetime
+from pathlib import Path
+from zoneinfo import ZoneInfo
+
+import yaml
+
+STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")
+ADR0008_COLUMNS = ["effective_date", "ticker", "change", "source_url", "source_status"]
+CSV_COLUMNS = ["effective_date", "ticker", "action", "source_id"]
+VERIFIED_STATUS = "DA_DOI_CHIEU"
+VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
+VN30_HEADING = "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30"
+# Các mục khác trong cùng một PDF quy mô. Không kết luận nội dung VN30 từ tên tệp.
+OTHER_INDEX_HEADINGS = (
+    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
+    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
+    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
+)
+
+
+def finding(fid, status, summary, **evidence):
+    if status not in STATUSES:
+        raise ValueError(status)
+    item = {"id": fid, "status": status, "summary": summary}
+    if evidence:
+        item["evidence"] = evidence
+    return item
+
+
+def _sha256(path: Path) -> str:
+    h = hashlib.sha256()
+    with path.open("rb") as f:
+        for chunk in iter(lambda: f.read(1 << 20), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def _load_json(path: Path):
+    return json.loads(path.read_text(encoding="utf-8"))
+
+
+def _load_config(root: Path):
+    path = root / "config.yaml"
+    if not path.is_file():
+        return None
+    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
+
+
+def _vn_date(value):
+    """Ngày lịch theo giờ Việt Nam. Thiếu hoặc không đọc được → None."""
+    if value is None or value == "":
+        return None
+    text = str(value).strip()
+    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
+        return text
+    try:
+        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
+    except ValueError:
+        return None
+    if dt.tzinfo is None:
+        dt = dt.replace(tzinfo=VN_TZ)
+    return dt.astimezone(VN_TZ).date().isoformat()
+
+
+def _dmy(iso_date: str) -> str:
+    y, m, d = iso_date.split("-")
+    return f"{d}/{m}/{y}"
+
+
+def load_vn30_rows(root: Path):
+    path = root / "data" / "vn30_history.csv"
+    if not path.is_file():
+        return None, path
+    with path.open(encoding="utf-8", newline="") as f:
+        reader = csv.DictReader(f)
+        return list(reader), path
+
+
+def load_manifest_docs(root: Path):
+    path = root / "data" / "evidence" / "vn30_reviews" / "EVIDENCE_MANIFEST.json"
+    if not path.is_file():
+        return None, path
+    payload = _load_json(path)
+    docs = payload.get("source_documents") if isinstance(payload, dict) else None
+    if not isinstance(docs, list):
+        return None, path
+    return docs, path
+
+
+def reconstruct(rows):
+    """Tập thành viên sau mỗi effective_date. Lỗi cấu trúc → (None, lý do)."""
+    by_date = {}
+    for row in rows:
+        by_date.setdefault(row.get("effective_date"), []).append(row)
+    members = set()
+    states = []
+    for date in sorted(d for d in by_date if d):
+        day = by_date[date]
+        for row in day:
+            if row.get("action") == "REMOVE":
+                ticker = row.get("ticker")
+                if ticker not in members:
+                    return None, f"REMOVE mã không có mặt: {ticker} {date}"
+                members.remove(ticker)
+        for row in day:
+            if row.get("action") == "ADD":
+                ticker = row.get("ticker")
+                if ticker in members:
+                    return None, f"ADD mã đang có mặt: {ticker} {date}"
+                members.add(ticker)
+            elif row.get("action") not in ("ADD", "REMOVE"):
+                return None, f"action lạ: {row.get('action')} {date}"
+        if len(members) != 30:
+            return None, f"{date}: {len(members)} mã, không phải 30"
+        states.append((date, set(members)))
+    return states, None
+
+
+def members_on(states, day):
+    current = None
+    for date, members in states or []:
+        if date <= day:
+            current = members
+        else:
+            break
+    return current
+
+
+def check_provenance(root, docs):
+    if docs is None:
+        return finding("PROVENANCE_HASH", "UNKNOWN", "Không có manifest VN30 để đối chiếu hash.")
+    bad, ok = [], []
+    for doc in docs:
+        rel = doc.get("path")
+        if not rel:
+            bad.append({"source_id": doc.get("source_id"), "error": "thiếu path"})
+            continue
+        path = root / rel
+        if not path.is_file():
+            bad.append({"source_id": doc.get("source_id"), "path": rel, "error": "thiếu tệp"})
+            continue
+        digest = _sha256(path)
+        size = path.stat().st_size
+        row = {"source_id": doc.get("source_id"), "path": rel, "sha256": digest, "bytes": size}
+        if digest != doc.get("sha256") or size != doc.get("bytes"):
+            row["expected_sha256"] = doc.get("sha256")
+            row["expected_bytes"] = doc.get("bytes")
+            bad.append(row)
+        else:
+            ok.append(row)
+    if bad:
+        return finding(
+            "PROVENANCE_HASH", "FAIL",
+            "Có tệp nguồn lệch hash, lệch số byte hoặc không có trên đĩa. Hash khớp không được hiểu là nội dung đã đúng.",
+            mismatches=bad, matched=len(ok))
+    return finding(
+        "PROVENANCE_HASH", "PASS",
+        "Mọi tệp kê trong manifest VN30 khớp SHA-256 và số byte. Việc này không xác minh nội dung.",
+        matched=ok)
+
+
+def check_publication_order(docs):
+    if docs is None:
+        return finding("PUBLICATION_BEFORE_USE", "UNKNOWN", "Không có manifest để so ngày công bố với ngày hiệu lực.")
+    bad, unknown, ok = [], [], []
+    for doc in docs:
+        published = _vn_date(doc.get("published_at"))
+        effective = doc.get("effective_date")
+        row = {"source_id": doc.get("source_id"), "published_on": published, "effective_date": effective}
+        if not published or not effective:
+            unknown.append(row)
+        elif published > effective:
+            bad.append(row)
+        else:
+            ok.append(row)
+    if bad:
+        return finding(
+            "PUBLICATION_BEFORE_USE", "FAIL",
+            "Có tài liệu được phép dùng trước ngày công bố theo giờ Việt Nam.",
+            lookahead=bad, undated=unknown)
+    if unknown:
+        return finding(
+            "PUBLICATION_BEFORE_USE", "UNKNOWN",
+            "Một số tài liệu thiếu published_at hoặc effective_date nên không kết luận được thứ tự thời điểm.",
+            undated=unknown, dated_ok=len(ok))
+    return finding(
+        "PUBLICATION_BEFORE_USE", "PASS",
+        "Với mọi tài liệu có đủ hai ngày, ngày công bố theo giờ Việt Nam không sau ngày hiệu lực.",
+        checked=len(ok))
+
+
+def check_decision_cutoff(docs, cfg):
+    """Kiểm tra chính xác phút công bố so với phút ra quyết định theo giờ VN.
+    Thiếu lịch quyết định đã đăng ký => INCONCLUSIVE, không lấy ngày hiệu lực thay thế.
+    """
+    if not docs:
+        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
+                       "Không có nguồn để đối chiếu thời điểm công bố.")
+    cutoff = ((cfg or {}).get("research") or {}).get("decision_time_local")
+    if not isinstance(cutoff, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", cutoff):
+        return finding("DECISION_TIME_OF_KNOWLEDGE", "INCONCLUSIVE",
+                       "Chưa đăng ký giờ ra quyết định theo ngày giao dịch (research.decision_time_local). "
+                       "So published_on <= effective_date không chứng minh có thể dùng ngay trong phiên.",
+                       decision_time_local=None)
+    bad, unknown, ok = [], [], []
+    for doc in docs:
+        published, effective = doc.get("published_at"), doc.get("effective_date")
+        row = {"source_id": doc.get("source_id"), "published_at": published,
+               "effective_date": effective}
+        try:
+            pub = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
+            if pub.tzinfo is None:
+                raise ValueError("published_at thiếu timezone")
+            decision = datetime.fromisoformat(f"{effective}T{cutoff}:00").replace(tzinfo=VN_TZ)
+            row["decision_at_local"] = decision.isoformat()
+            row["publication_at_local"] = pub.astimezone(VN_TZ).isoformat()
+            (bad if pub > decision else ok).append(row)
+        except (ValueError, TypeError):
+            unknown.append(row)
+    if bad:
+        return finding("DECISION_TIME_OF_KNOWLEDGE", "FAIL",
+                       "Có nguồn được công bố sau giờ ra quyết định; không thể dùng trong cùng phiên.",
+                       late_publications=bad, undated=unknown, verified_before=len(ok))
+    if unknown:
+        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
+                       "Ngày/giờ nguồn chưa đủ để so với giờ ra quyết định.",
+                       undated=unknown, verified_before=len(ok))
+    return finding("DECISION_TIME_OF_KNOWLEDGE", "PASS",
+                   "Các bản tin trong manifest được công bố trước giờ quyết định giả định đã khai; "
+                   "không xác nhận vintage cho toàn bộ giá và BCTC.",
+                   checked=len(ok), decision_time_local=cutoff)
+
+def check_csv(rows):
+    if rows is None:
+        return finding("CSV_INTERNAL", "UNKNOWN", "Không có data/vn30_history.csv."), None
+    if not rows:
+        return finding("CSV_INTERNAL", "FAIL", "CSV thành phần không có dòng dữ liệu."), None
+    missing = [c for c in CSV_COLUMNS if c not in rows[0]]
+    if missing:
+        return finding("CSV_INTERNAL", "FAIL", "CSV thiếu cột mà bộ test hiện hành đang khóa.", missing_columns=missing), None
+    states, err = reconstruct(rows)
+    if err:
+        return finding("CSV_INTERNAL", "FAIL", "Không dựng lại được rổ 30 mã từ CSV.", error=err), None
+    return finding(
+        "CSV_INTERNAL", "PASS",
+        "CSV dựng lại được các mốc, mỗi mốc đúng 30 mã. Không suy ra thành phần trước mốc đầu tiên.",
+        states=[{"effective_date": d, "members": sorted(m)} for d, m in states]), states
+
+
+def check_adr_schema(rows):
+    if rows is None:
+        return finding("ADR0008_SCHEMA", "UNKNOWN", "Không có CSV để đối chiếu khuôn ADR-0008.")
+    actual = list(rows[0].keys()) if rows else []
+    if actual == ADR0008_COLUMNS:
+        return finding("ADR0008_SCHEMA", "PASS", "CSV đúng khuôn cột ADR-0008.", columns=actual)
+    return finding(
+        "ADR0008_SCHEMA", "FAIL",
+        "CSV không theo khuôn ADR-0008 (effective_date,ticker,change,source_url,source_status). "
+        "Không được tự ghi đè CSV trong PIT-001. Khuôn đang khóa bởi test là cột action/source_id.",
+        actual_columns=actual, adr0008_columns=ADR0008_COLUMNS)
+
+
+def check_coverage(cfg, states):
+    start = ((cfg or {}).get("data") or {}).get("start")
+    if states is None:
+        return finding("UNIVERSE_COVERAGE", "UNKNOWN", "Chưa dựng được lịch sử thành phần.")
+    first = states[0][0]
+    if not start:
+        return finding(
+            "UNIVERSE_COVERAGE", "UNKNOWN",
+            "Không đọc được data.start trong config nên không chốt được cửa sổ nghiên cứu.",
+            first_evidence_date=first)
+    if start < first:
+        return finding(
+            "UNIVERSE_COVERAGE", "FAIL",
+            "Lịch sử thành phần đã ghim không phủ từ ngày đầu cửa sổ nghiên cứu. Không tự điền các kỳ thiếu.",
+            research_start=start, first_evidence_date=first,
+            uncovered_until_exclusive=first)
+    return finding(
+        "UNIVERSE_COVERAGE", "PASS",
+        "Mốc thành phần đầu tiên không sau ngày đầu cửa sổ nghiên cứu trong config.",
+        research_start=start, first_evidence_date=first)
+
+
+def check_before_first(cfg, states):
+    if states is None or not states:
+        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN", "Chưa có mốc thành phần.")
+    first = states[0][0]
+    start = ((cfg or {}).get("data") or {}).get("start")
+    if not start:
+        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
+                       "Không có ngày đầu nghiên cứu để so với mốc bản gốc.")
+    if start < first:
+        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
+                       "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN.",
+                       first_evidence_date=first, research_start=start, applies=True)
+    return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "PASS",
+                   "Khoảng nghiên cứu không yêu cầu thành phần trước mốc gốc đầu tiên. "
+                   "Điều này chưa chứng minh tính liên tục giữa các kỳ.",
+                   first_evidence_date=first, research_start=start, applies=False)
+
+def check_continuity(docs, states):
+    if not states or len(states) < 2:
+        return finding(
+            "CONTINUITY_BETWEEN_REVIEWS", "INCONCLUSIVE",
+            "Chưa đủ hai mốc đã ghim để nói về khoảng giữa các kỳ.")
+    gaps = []
+    for (a, _), (b, _) in zip(states, states[1:]):
+        gaps.append({"after": a, "before": b,
+                     "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). "
+                             "Việc không thấy tệp không chứng minh rổ không đổi."})
+    copied = []
+    for doc in docs or []:
+        if doc.get("names_copied_from") and doc.get("names_copied_from") != doc.get("source_id"):
+            copied.append({"source_id": doc.get("source_id"), "names_copied_from": doc.get("names_copied_from"),
+                           "effective_date": doc.get("effective_date")})
+    return finding(
+        "CONTINUITY_BETWEEN_REVIEWS", "UNKNOWN",
+        "Khoảng giữa các mốc đã ghim không được coi là đã chứng minh liên tục. "
+        "Bản tin chép danh sách từ PDF kỳ trước không phải là in lại đủ 30 mã.",
+        gaps=gaps, names_copied_from_other_document=copied)
+
+
+def _function_ast(src, name):
+    """Chỉ xét AST thật; comment hoặc string literal không được tính là hành vi."""
+    try:
+        module = ast.parse(src)
+    except SyntaxError:
+        return None
+    return next((n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
+                 and n.name == name), None)
+
+
+def _calls_adjust_build_events(fn):
+    return any(
+        isinstance(n, ast.Call)
+        and isinstance(n.func, ast.Attribute)
+        and n.func.attr == "build_events"
+        and isinstance(n.func.value, ast.Name)
+        and n.func.value.id == "adjust"
+        for n in ast.walk(fn)
+    )
+
+
+def research_chain_requires_verified_status(src: str):
+    """Dấu hiệu cú pháp, KHÔNG phải chứng minh đã chặn các event chưa xác minh."""
+    fn = _function_ast(src, "build_events")
+    if fn is None:
+        return None
+    return any(isinstance(n, ast.Name) and n.id == "source_status"
+               for n in ast.walk(fn))
+
+
+def load_market_uses_verified_chain(src: str):
+    """Trả về dấu hiệu gọi hàm verified; không bao giờ tự cấp PASS từ dấu hiệu này."""
+    fn = _function_ast(src, "load_market")
+    if fn is None:
+        return None
+    return any(isinstance(n, ast.Call) and (
+        (isinstance(n.func, ast.Name) and n.func.id in ("verified_adjust", "verified_factors"))
+        or (isinstance(n.func, ast.Attribute)
+            and n.func.attr in ("verified_adjust", "verified_factors"))
+    ) for n in ast.walk(fn))
+
+
+def check_engine_mode(root, cfg):
+    data_py = root / "engine" / "data.py"
+    if not data_py.is_file():
+        return finding("ENGINE_UNIVERSE_MODE", "UNKNOWN", "Không có engine/data.py để kiểm tra.")
+    basis = (cfg or {}).get("universe_basis")
+    fn = _function_ast(data_py.read_text(encoding="utf-8"), "load_market")
+    if basis == "CURRENT":
+        return finding("ENGINE_UNIVERSE_MODE", "FAIL",
+                       "Cấu hình khai CURRENT: không thể chứng nhận chọn universe theo từng ngày.",
+                       universe_basis=basis)
+    if fn is None:
+        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
+                       "Không phân tích được hàm load_market; không được tự chứng nhận HISTORICAL.",
+                       universe_basis=basis)
+    if basis == "HISTORICAL":
+        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
+                       "HISTORICAL là một khai báo, không chứng minh engine dùng đúng tập thành viên "
+                       "từng phiên. Cần kiểm thử hành vi replay với ngày vào/ra và thiếu nguồn.",
+                       universe_basis=basis, behavioral_membership_test_verified=False)
+    return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
+                   "Không có bằng chứng hành vi chọn universe theo ngày.", universe_basis=basis)
+
+def check_config_vs_basket(cfg, states):
+    if not states:
+        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Chưa có rổ dựng từ CSV.")
+    configured = (cfg or {}).get("universe")
+    if not configured:
+        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Config không có danh sách universe.")
+    configured = set(configured)
+    latest_date, latest = states[-1]
+    only_config = sorted(configured - latest)
+    only_evidence = sorted(latest - configured)
+    if not only_config and not only_evidence and len(configured) == 30:
+        return finding(
+            "CONFIG_VS_EVIDENCED_BASKET", "PASS",
+            "Danh sách config trùng rổ dựng được tại mốc CSV cuối cùng.",
+            as_of=latest_date)
+    return finding(
+        "CONFIG_VS_EVIDENCED_BASKET", "FAIL",
+        "Danh sách cố định trong config không trùng rổ dựng từ CSV tại mốc cuối. "
+        "Đây là lệch thành phần, không phải khuyến nghị giao dịch.",
+        csv_state_as_of=latest_date,
+        in_config_not_in_csv_state=only_config,
+        in_csv_state_not_in_config=only_evidence,
+        config_count=len(configured), evidence_count=len(latest))
+
+
+def _price_tickers(root: Path):
+    """Tập mã, các ngày thực có giá và khoảng ngày của kho (chỉ đọc)."""
+    tickers, dates_by_ticker, market_dates = set(), {}, set()
+    first = last = None
+    rows, paths = 0, []
+    legacy = root / "data" / "store" / "prices.csv.gz"
+    monthly = root / "data" / "store" / "prices"
+    candidates = []
+    if legacy.is_file():
+        candidates.append(legacy)
+    if monthly.is_dir():
+        candidates.extend(sorted(monthly.glob("*.csv")))
+    if not candidates:
+        return None
+
+    def consume(stream):
+        nonlocal first, last, rows
+        reader = csv.DictReader(stream)
+        if not reader.fieldnames or "ticker" not in reader.fieldnames or "date" not in reader.fieldnames:
+            return
+        for rec in reader:
+            ticker, date = rec.get("ticker"), (rec.get("date") or "")[:10]
+            if not ticker:
+                continue
+            tickers.add(ticker)
+            rows += 1
+            if date:
+                dates_by_ticker.setdefault(ticker, set()).add(date)
+                market_dates.add(date)
+                if first is None or date < first:
+                    first = date
+                if last is None or date > last:
+                    last = date
+
+    for path in candidates:
+        paths.append(str(path.relative_to(root)))
+        if path.suffix == ".gz":
+            with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
+                consume(f)
+        else:
+            with path.open(encoding="utf-8", newline="") as f:
+                consume(f)
+    return {"tickers": tickers, "dates_by_ticker": dates_by_ticker, "market_dates": market_dates,
+            "first": first, "last": last, "rows": rows, "paths": paths}
+
+
+def check_ticker_presence(info, states):
+    if info is None:
+        return finding("TICKER_PRESENCE", "UNKNOWN", "Không thấy kho giá data/store.")
+    if not states:
+        return finding("TICKER_PRESENCE", "INCONCLUSIVE",
+                       "Có kho giá nhưng thiếu rổ lịch sử để kiểm tra đủ mã.")
+    needed = set().union(*(members for _, members in states))
+    missing = sorted(needed - info["tickers"])
+    extra = sorted(info["tickers"] - needed)
+    details = {"price_first": info["first"], "price_last": info["last"],
+               "price_rows": info["rows"], "price_tickers": sorted(info["tickers"]),
+               "members_ever_in_csv": sorted(needed), "members_without_any_price_row": missing,
+               "priced_but_never_in_pinned_baskets": extra, "paths": info["paths"]}
+    if missing:
+        return finding("TICKER_PRESENCE", "FAIL",
+                       "Có mã từng nằm trong rổ ghim nhưng không có dòng giá.", **details)
+    return finding("TICKER_PRESENCE", "PASS",
+                   "Mỗi mã trong rổ đã ghim có ít nhất một dòng. KHÔNG chứng nhận đủ chuỗi giá.",
+                   **details)
+
+
+def check_price_window_coverage(info, states, cfg):
+    """Độ phủ theo PHIÊN. Không có lịch phiên chính thức/vintage thì không thể PASS."""
+    if info is None:
+        return finding("PRICE_WINDOW_COVERAGE", "UNKNOWN", "Không thấy kho giá.")
+    if not states:
+        return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
+                       "Chưa có thành phần lịch sử để ghép với chuỗi giá từng phiên.")
+    horizon = int((cfg or {}).get("horizon_days") or 20)
+    lookback = int(((cfg or {}).get("quality") or {}).get("feature_lookback") or 0)
+    required = max(2, horizon + 1, lookback + 1)
+    needed = set().union(*(m for _, m in states))
+    absent = sorted(needed - info["tickers"])
+    short = [{"ticker": t, "distinct_sessions": len(info["dates_by_ticker"].get(t, set()))}
+             for t in sorted(needed)
+             if len(info["dates_by_ticker"].get(t, set())) < required]
+    # Các ngày được suy từ GIÁ ĐÃ CÓ, không phải lịch giao dịch chính thức.
+    market_days = sorted(info["market_dates"])
+    missing_by_period = []
+    for k, (effective, members) in enumerate(states):
+        end = states[k + 1][0] if k + 1 < len(states) else None
+        dates = [d for d in market_days if d >= effective and (end is None or d < end)]
+        for ticker in sorted(members):
+            gaps = [d for d in dates if d not in info["dates_by_ticker"].get(ticker, set())]
+            if gaps and len(missing_by_period) < 40:
+                missing_by_period.append({"ticker": ticker, "effective_date": effective,
+                                          "missing_session_count": len(gaps), "examples": gaps[:3]})
+    details = {"horizon_days": horizon, "feature_lookback": lookback,
+               "min_distinct_sessions_for_individual_ticker": required,
+               "missing_tickers": absent, "short_series": short[:40],
+               "missing_dates_on_observed_market_calendar": missing_by_period,
+               "official_exchange_calendar_verified": False}
+    if absent or short or missing_by_period:
+        return finding("PRICE_WINDOW_COVERAGE", "FAIL",
+                       "Thiếu mã, chuỗi quá ngắn hoặc thiếu ngày giá trong phiên có dữ liệu cho mã khác. "
+                       "Chưa xét liệu lịch phiên suy từ kho có đầy đủ hay không.", **details)
+    return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
+                   "Các mã có đủ số phiên tối thiểu trong kho quan sát, nhưng chưa có lịch phiên "
+                   "chính thức và dữ liệu giá/vintage được xác minh để kết luận độ phủ PIT.", **details)
+
+def _manual_events(root: Path):
+    path = root / "data" / "corporate_actions.csv"
+    if not path.is_file():
+        return None, path
+    with path.open(encoding="utf-8", newline="") as f:
+        return list(csv.DictReader(f)), path
+
+
+def _ca_manifest(root: Path):
+    path = root / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
+    if not path.is_file():
+        return None
+    payload = _load_json(path)
+    docs = payload.get("source_documents") if isinstance(payload, dict) else None
+    return docs if isinstance(docs, list) else None
+
+
+def check_corporate_actions(root):
+    rows, path = _manual_events(root)
+    if rows is None:
+        return finding("CORPORATE_ACTION_VERIFICATION", "UNKNOWN", "Không có data/corporate_actions.csv.")
+    docs = _ca_manifest(root) or []
+    by_ticker = {}
+    for doc in docs:
+        ticker = doc.get("ticker")
+        if ticker and ticker not in by_ticker:
+            by_ticker[ticker] = doc
+    pending = []
+    for row in rows:
+        status = (row.get("source_status") or "").strip()
+        if status == VERIFIED_STATUS:
+            continue
+        doc = by_ticker.get(row.get("ticker")) or {}
+        pending.append({
+            "ticker": row.get("ticker"),
+            "csv_ex_date": row.get("ex_date"),
+            "csv_type": row.get("type"),
+            "csv_ratio": row.get("ratio"),
+            "csv_source_status": status or None,
+            "evidence_source_id": doc.get("source_id"),
+            "official_ex_date": doc.get("official_ex_date"),
+            "published_at": doc.get("published_at"),
+            "published_at_status": doc.get("published_at_status"),
+            "dates_match": (row.get("ex_date") == doc.get("official_ex_date")) if doc.get("official_ex_date") else None,
+        })
+    if not rows:
+        return finding(
+            "CORPORATE_ACTION_VERIFICATION", "PASS",
+            "CSV sự kiện quyền không có dòng nhập tay. Không có gì để xác nhận từ bước nhảy giá.",
+            rows=0)
+    if not pending:
+        return finding(
+            "CORPORATE_ACTION_VERIFICATION", "PASS",
+            "Mọi dòng sự kiện quyền nhập tay có source_status DA_DOI_CHIEU.",
+            rows=len(rows))
+    return finding(
+        "CORPORATE_ACTION_VERIFICATION", "FAIL",
+        "Có sự kiện quyền nhập tay chưa ở trạng thái DA_DOI_CHIEU. "
+        "Không xác nhận sự kiện từ bước nhảy giá. Ngày trên CSV lệch ngày official_ex_date của bản HOSE đã ghim "
+        "thì vẫn là chưa xác minh, kể cả khi hash PDF khớp.",
+        unverified=pending)
+
+
+def check_unverified_chain(root, ca_finding):
+    adjust_path, data_path = root / "engine" / "adjust.py", root / "engine" / "data.py"
+    if not adjust_path.is_file() or not data_path.is_file():
+        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "UNKNOWN",
+                       "Thiếu engine/adjust.py hoặc engine/data.py.")
+    adjust_src = adjust_path.read_text(encoding="utf-8")
+    data_src = data_path.read_text(encoding="utf-8")
+    build_fn = _function_ast(adjust_src, "build_events")
+    market_fn = _function_ast(data_src, "load_market")
+    if build_fn is None or market_fn is None:
+        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
+                       "Không thể đọc AST hàm build_events/load_market; không tự xác nhận cổng.")
+    call = _calls_adjust_build_events(market_fn)
+    mention = research_chain_requires_verified_status(adjust_src)
+    verified_hint = load_market_uses_verified_chain(data_src)
+    unverified_rows = (ca_finding.get("evidence") or {}).get("unverified") or []
+    details = {"load_market_calls_adjust_build_events": call,
+               "build_events_ast_mentions_source_status": mention,
+               "load_market_ast_mentions_verified_function": verified_hint,
+               "unverified_manual_rows": len(unverified_rows),
+               "behavioral_proof_verified_gate": False}
+    if call and not mention and unverified_rows:
+        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "FAIL",
+                       "Có sự kiện chưa xác minh, load_market gọi build_events, "
+                       "nhưng hàm build_events không đọc source_status. "
+                       "Không được cho vào verified-adjusted khi chưa có cổng hành vi.", **details)
+    return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
+                   "Phân tích AST chỉ là dấu hiệu cú pháp; ngay cả khi source_status/verified_factors "
+                   "xuất hiện trong mã, vẫn cần thử hành vi loại CAN_DOI_CHIEU trước khi cấp PASS.",
+                   **details)
+
+def _pdf_pages_text(path: Path):
+    try:
+        from pypdf import PdfReader
+    except Exception as exc:  # noqa: BLE001 — môi trường thiếu pypdf thì không bịa nội dung
+        return None, f"không import được pypdf ({exc})"
+    try:
+        reader = PdfReader(str(path))
+        pages = []
+        for page in reader.pages:
+            pages.append(page.extract_text(extraction_mode="layout") or "")
+        return pages, None
+    except Exception as exc:  # noqa: BLE001
+        return None, f"không đọc được PDF ({exc})"
+
+
+def constituent_heading_line(page_text: str):
+    """Dòng tiêu đề rổ VN30, không phải danh mục dự phòng. None nếu không thấy."""
+    text = unicodedata.normalize("NFC", page_text)
+    for line in text.splitlines():
+        compact = " ".join(line.split())
+        low = compact.lower()
+        if "vn30" in low and "thành phần" in low and "dự phòng" not in low:
+            return compact
+    return None
+
+
+def tickers_in_vn30_section(page_text: str):
+    text = unicodedata.normalize("NFC", page_text)
+    lines = text.splitlines()
+    start = None
+    for i, line in enumerate(lines):
+        if constituent_heading_line(line):
+            start = i
+            break
+    if start is None:
+        return None
+    chunk = []
+    for line in lines[start + 1:]:
+        compact = " ".join(unicodedata.normalize("NFC", line).split())
+        if "dự phòng" in compact.lower() and "vn30" in compact.lower():
+            break
+        chunk.append(line)
+    found = re.findall(r"(?m)^\s*\d+\s+([A-Z0-9]{3})\b", "\n".join(chunk))
+    out = []
+    for ticker in found:
+        if ticker not in out:
+            out.append(ticker)
+    return out
+
+
+def check_pdf_contents(root, docs):
+    if not docs:
+        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Không có manifest để mở PDF.")
+    checked = []
+    any_fail = False
+    any_unknown = False
+    for doc in docs:
+        rel = doc.get("path") or ""
+        if not str(rel).lower().endswith(".pdf"):
+            continue
+        path = root / rel
+        item = {"source_id": doc.get("source_id"), "path": rel, "effective_date": doc.get("effective_date")}
+        if not path.is_file():
+            item["content_status"] = "UNKNOWN"
+            item["reason"] = "thiếu tệp"
+            any_unknown = True
+            checked.append(item)
+            continue
+        pages, err = _pdf_pages_text(path)
+        if err:
+            item["content_status"] = "INCONCLUSIVE"
+            item["reason"] = err
+            any_unknown = True
+            checked.append(item)
+            continue
+        heading_pages = []
+        for i, text in enumerate(pages):
+            heading = constituent_heading_line(text)
+            if heading:
+                heading_pages.append({"page": i + 1, "heading": heading})
+        other = []
+        for i, text in enumerate(pages):
+            for heading in OTHER_INDEX_HEADINGS:
+                if heading in text:
+                    other.append({"page": i + 1, "heading": heading})
+        item["vn30_heading_pages"] = heading_pages
+        item["other_index_headings"] = other
+        if not heading_pages:
+            item["content_status"] = "INCONCLUSIVE"
+            item["reason"] = "không thấy mục VN30 trong lớp chữ PDF; hash không thay cho việc này"
+            any_unknown = True
+            checked.append(item)
+            continue
+        parsed = None
+        for item_page in heading_pages:
+            parsed = tickers_in_vn30_section(pages[item_page["page"] - 1])
+            if parsed:
+                break
+        expected = list(doc.get("members_after") or [])
+        item["parsed_tickers"] = parsed or []
+        item["parsed_count"] = len(parsed or [])
+        item["expected_count"] = len(expected)
+        if not parsed or len(parsed) != len(set(parsed)):
+            item["content_status"] = "INCONCLUSIVE"
+            item["reason"] = "không tách được danh sách mã không trùng trong mục VN30"
+            any_unknown = True
+        elif set(parsed) != set(expected) or len(parsed) != len(expected):
+            item["content_status"] = "FAIL"
+            item["only_in_pdf"] = sorted(set(parsed) - set(expected))
+            item["only_in_manifest"] = sorted(set(expected) - set(parsed))
+            any_fail = True
+        else:
+            item["content_status"] = "PASS"
+        joined = "\n".join(pages)
+        token = _dmy(doc["effective_date"]) if doc.get("effective_date") else None
+        item["pdf_contains_effective_date_dmy"] = bool(token and token in joined)
+        checked.append(item)
+    if not checked:
+        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Manifest không có PDF.")
+    focus = next((x for x in checked if x.get("source_id") == "hose-2510691"), None)
+    if any_fail:
+        status = "FAIL"
+        summary = "Có PDF mà mục VN30 đọc được không trùng members_after của manifest."
+    elif any_unknown:
+        status = "INCONCLUSIVE"
+        summary = "Có PDF chưa đọc được mục VN30 hoặc không tách được đủ mã. Không nâng hash thành đã xác minh nội dung."
+    else:
+        status = "PASS"
+        summary = "Mỗi PDF đã ghim có mục VN30 và danh sách đọc được trùng members_after. Ngày hiệu lực có thể nằm ở tin, không nằm trong PDF."
+    return finding("PDF_VN30_CONTENT", status, summary, documents=checked, hose_2510691=focus)
+
+
+def check_2510691_effective_date(root, docs, content_finding):
+    focus = (content_finding.get("evidence") or {}).get("hose_2510691")
+    news = next((d for d in docs or [] if d.get("source_id") == "hose-2510691-news"), None)
+    if focus is None and news is None:
+        return finding("HOSE_2510691_SCOPE", "UNKNOWN", "Không có hồ sơ hose-2510691 trong manifest.")
+    news_has_date = False
+    news_title = None
+    if news and (root / news.get("path", "")).is_file():
+        raw = (root / news["path"]).read_text(encoding="utf-8")
+        token = _dmy(news["effective_date"]) if news.get("effective_date") else ""
+        news_has_date = bool(token and _news_effective_statement(raw, news["effective_date"]))
+        try:
+            news_title = (_load_json(root / news["path"]).get("data") or {}).get("title")
+        except json.JSONDecodeError:
+            news_title = None
+    pdf_has_date = bool(focus and focus.get("pdf_contains_effective_date_dmy"))
+    pdf_match = bool(focus and focus.get("content_status") == "PASS")
+    other = (focus or {}).get("other_index_headings") or []
+    if pdf_match and news_has_date and not pdf_has_date:
+        status = "PASS"
+        summary = (
+            "hose-2510691 là PDF tên VNAllshare kỳ 10/2026 và có mục «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN "
+            "CỦA CHỈ SỐ VN30» in đủ 30 mã, trùng members_after. Ngày hiệu lực 16/11/2026 đọc từ tin HOSE đã ghim, "
+            "không thấy dạng 16/11/2026 trong chữ PDF. Các mục chỉ số khác trong cùng tệp không phải rổ VN30."
+        )
+    elif pdf_match and pdf_has_date:
+        status = "PASS"
+        summary = "PDF 2510691 có mục VN30 trùng manifest và có chữ ngày hiệu lực."
+    elif focus and focus.get("content_status") == "FAIL":
+        status = "FAIL"
+        summary = "Mục VN30 của PDF 2510691 không trùng members_after."
+    else:
+        status = "INCONCLUSIVE"
+        summary = "Chưa đủ chữ để kết luận vừa thành phần vừa ngày hiệu lực của hồ sơ 2510691."
+    return finding(
+        "HOSE_2510691_SCOPE", status, summary,
+        pdf_membership_matches=pdf_match,
+        pdf_contains_effective_date=pdf_has_date,
+        news_contains_effective_date=news_has_date,
+        news_title=news_title,
+        other_index_headings=other)
+
+
+def _news_effective_statement(raw: str, effective_date: str):
+    """Chỉ đọc lời công bố trong summary, không tìm ngày ở metadata/comment ngoài."""
+    try:
+        payload = json.loads(raw)
+    except json.JSONDecodeError:
+        return False
+    data = payload.get("data")
+    if not isinstance(data, dict) or not isinstance(data.get("summary"), str):
+        return False
+    summary = re.sub(r"<[^>]+>", " ", data["summary"])
+    summary = summary.replace("&nbsp;", " ")
+    token = _dmy(effective_date)
+    return token in summary and "hiệu lực" in summary.lower()
+
+
+def check_news_effective_dates(root, docs):
+    if not docs:
+        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Không có manifest.")
+    checked = []
+    for doc in docs:
+        rel = doc.get("path") or ""
+        if not rel.endswith(".json"):
+            continue
+        effective = doc.get("effective_date")
+        path = root / rel
+        row = {"source_id": doc.get("source_id"), "path": rel, "effective_date": effective}
+        if not effective or not path.is_file():
+            row["status"] = "UNKNOWN"
+        else:
+            present = _news_effective_statement(path.read_text(encoding="utf-8"), effective)
+            row["token"] = _dmy(effective)
+            row["present_in_announcement_summary"] = present
+            row["status"] = "PASS" if present else "FAIL"
+        checked.append(row)
+    if not checked:
+        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Manifest không có JSON tin.")
+    if any(row["status"] == "FAIL" for row in checked):
+        return finding("NEWS_EFFECTIVE_DATE_TEXT", "FAIL",
+                       "Có bản tin không chứng minh ngày hiệu lực trong lời công bố (summary).",
+                       documents=checked)
+    if any(row["status"] == "UNKNOWN" for row in checked):
+        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN",
+                       "Có tin thiếu ngày hoặc không mở được.", documents=checked)
+    return finding("NEWS_EFFECTIVE_DATE_TEXT", "PASS",
+                   "Các bản tin đã ghim có ngày hiệu lực trong phần summary, không chỉ metadata.",
+                   documents=checked)
+
+def check_microstructure(root, cfg):
+    costs = (cfg or {}).get("costs") or {}
+    quality = (cfg or {}).get("quality") or {}
+    trades = root / "paper" / "trades.csv"
+    n_trades = None
+    if trades.is_file():
+        with trades.open(encoding="utf-8", newline="") as f:
+            n_trades = max(0, sum(1 for _ in f) - 1)
+    return finding(
+        "MARKET_MICROSTRUCTURE_ASSUMPTIONS", "INCONCLUSIVE",
+        "Phí, thuế, trượt giá, lô và biên độ là giả định trong config hoặc hằng số giấy. "
+        "Chưa có đối chiếu lệnh khớp thật. Không chứng minh được khả năng khớp.",
+        costs=costs, price_limit=quality.get("price_limit"), lot_size=(cfg or {}).get("lot_size"),
+        paper_trade_rows=n_trades)
+
+
+def _status_map(findings):
+    return {item["id"]: item["status"] for item in findings}
+
+
+def conclude(findings):
+    """Cổng fail-closed: thiếu bất kỳ kiểm tra bắt buộc nào => không READY."""
+    st = _status_map(findings)
+    critical = (
+        "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
+        "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
+        "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
+        "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
+        "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
+        "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
+        "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE", "NEWS_EFFECTIVE_DATE_TEXT",
+        "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
+    )
+    blocked = {k: st.get(k) for k in critical if st.get(k) == "FAIL"}
+    unknown = {k: st.get(k) for k in critical
+               if st.get(k) in ("INCONCLUSIVE", "UNKNOWN", None)}
+    invalid = {k: st.get(k) for k in critical if st.get(k) is not None and st.get(k) not in (
+        "PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")}
+    if blocked or invalid:
+        return "NOT_READY", ("Kiểm tra bắt buộc FAIL/không hợp lệ: "
+                             + ", ".join(sorted(set(blocked) | set(invalid))))
+    if unknown:
+        return "INCONCLUSIVE", ("Chưa đủ chứng cứ để cấp READY: "
+                                + ", ".join(sorted(unknown)))
+    return "READY", "Tất cả kiểm tra bắt buộc đều PASS; không phải xác nhận alpha."
+
+def audit(root) -> dict:
+    """Đọc cây root; không mở tệp để ghi hay nâng chứng cứ."""
+    root = Path(root)
+    cfg = _load_config(root)
+    docs, _ = load_manifest_docs(root)
+    rows, _ = load_vn30_rows(root)
+    csv_finding, states = check_csv(rows)
+    price_info = _price_tickers(root)
+    findings = [
+        check_provenance(root, docs),
+        check_publication_order(docs),
+        check_decision_cutoff(docs, cfg),
+        csv_finding,
+        check_adr_schema(rows),
+        check_coverage(cfg, states),
+        check_before_first(cfg, states),
+        check_continuity(docs, states),
+        check_engine_mode(root, cfg),
+        check_config_vs_basket(cfg, states),
+        check_ticker_presence(price_info, states),
+        check_price_window_coverage(price_info, states, cfg),
+        check_corporate_actions(root),
+    ]
+    findings.append(check_unverified_chain(root, findings[-1]))
+    content = check_pdf_contents(root, docs)
+    findings.append(content)
+    findings.append(check_2510691_effective_date(root, docs, content))
+    findings.append(check_news_effective_dates(root, docs))
+    findings.append(check_microstructure(root, cfg))
+    conclusion, reason = conclude(findings)
+    first = states[0][0] if states else None
+    return {
+        "tool": "pit001_audit",
+        "read_only": True,
+        "alpha_claim": False,
+        "conclusion": conclusion,
+        "conclusion_reason": reason,
+        "research_start": ((cfg or {}).get("data") or {}).get("start"),
+        "first_pinned_membership_date": first,
+        "eligible_window": None if conclusion != "READY" else {
+            "from": ((cfg or {}).get("data") or {}).get("start"),
+            "note": "Kiểm tra trên cây chỉ định; không phải bằng chứng alpha.",
+        },
+        "findings": findings,
+    }
+
+def main(argv=None) -> int:
+    import argparse, sys
+    parser = argparse.ArgumentParser(description="PIT-001 kiểm toán chỉ đọc")
+    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
+    args = parser.parse_args(argv)
+    json.dump(audit(args.root), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
+    sys.stdout.write("\n")
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
~~~~

---

Gói này chỉ được dùng để đối chiếu, không cấp tự động quyền merge. Nếu PR #69 đổi HEAD, phải tạo lại gói từ HEAD mới; tuyệt đối không ký bản chấm cho mã đã thay đổi.
