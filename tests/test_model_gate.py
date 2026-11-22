"""LỆNH E3 (QĐ-6, ADR-0016): mô hình chỉ lên ACTIVE khi Owner ghi nó vào state/MODEL_REGISTRY.yaml qua PR.

Không mạng. Không ghi kho: tệp duyệt dựng trong thư mục tạm; sổ giấy chạy với ROOT trỏ vào thư mục tạm.
"""
import pathlib
import subprocess

import numpy as np
import pandas as pd
import pytest

from engine import config, knowledge, paper

REPO = pathlib.Path(__file__).resolve().parents[1]
MAX_ACTIVE = config.CFG["registry"]["max_active"]


def _model(ic_t, state="WATCH"):
    return {"spec": {"features": ["f1"], "model": "ridge"}, "status": "SUPPORTED", "state": state,
            "backtest": {"ic_t": ic_t}, "created": "2026-01-02", "fitted_at": None, "realized": None,
            "history": [["2026-01-02", state, "vượt ngưỡng walk-forward"]]}


def _reg(n=3, state="WATCH"):
    return {f"M{i}": _model(5.0 - i, state) for i in range(n)}


def _yaml(tmp_path, text):
    p = tmp_path / "MODEL_REGISTRY.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def _rank(reg, tmp_path, text):
    approved, err = knowledge.load_approved(_yaml(tmp_path, text))
    knowledge.rank_active(reg, "2026-11-20", approved=approved)
    return {k: v["state"] for k, v in reg.items()}, err


# ---------- 1. Danh sách duyệt trống: mô hình vượt ngưỡng dừng ở WATCH ----------

def test_empty_approval_list_keeps_promoted_models_at_watch(tmp_path):
    reg = {}
    for i, t in enumerate((4.0, 3.0)):
        knowledge.promote(reg, f"M{i}", {"features": ["f1"], "model": "ridge"}, {"ic_t": t}, "STRONG", "2026-11-20")
    states, err = _rank(reg, tmp_path, "# Trạng thái: ACTIVE | WATCH\nmodels: []\n")
    assert err is None and states == {"M0": "WATCH", "M1": "WATCH"}


def test_already_active_model_without_approval_is_demoted_to_watch(tmp_path):
    reg = _reg(2, state="ACTIVE")
    states, _ = _rank(reg, tmp_path, "models: []\n")
    assert states == {"M0": "WATCH", "M1": "WATCH"}
    assert all("QĐ-6" in v["history"][-1][2] for v in reg.values())


def test_real_repo_approval_file_is_valid_and_empty():
    approved, err = knowledge.load_approved(REPO / knowledge.APPROVED)
    assert err is None and approved == frozenset()


# ---------- 2. Có dòng duyệt: mô hình lên ACTIVE ----------

def test_approved_row_makes_model_active(tmp_path):
    reg = _reg(3)
    states, err = _rank(reg, tmp_path, "models:\n  - id: M1\n    state: ACTIVE\n")
    assert err is None and states == {"M0": "WATCH", "M1": "ACTIVE", "M2": "WATCH"}
    assert "Owner duyệt" in reg["M1"]["history"][-1][2]


def test_approved_row_with_other_state_does_not_activate(tmp_path):
    states, err = _rank(_reg(2), tmp_path, "models:\n  - id: M0\n    state: WATCH\n  - id: M1\n    state: RETIRED\n")
    assert err is None and states == {"M0": "WATCH", "M1": "WATCH"}


def test_approval_cannot_revive_a_degraded_or_retired_model(tmp_path):
    reg = {"M0": _model(5.0, "DEGRADING"), "M1": _model(4.0, "RETIRED")}
    states, _ = _rank(reg, tmp_path, "models:\n  - id: M0\n    state: ACTIVE\n  - id: M1\n    state: ACTIVE\n")
    assert states == {"M0": "DEGRADING", "M1": "RETIRED"}


def test_max_active_still_caps_approved_models(tmp_path):
    reg = _reg(MAX_ACTIVE + 2)
    rows = "".join(f"  - id: M{i}\n    state: ACTIVE\n" for i in range(MAX_ACTIVE + 2))
    states, _ = _rank(reg, tmp_path, "models:\n" + rows)
    assert [k for k, v in states.items() if v == "ACTIVE"] == [f"M{i}" for i in range(MAX_ACTIVE)]


# ---------- 3. Tệp thiếu hoặc hỏng: không mô hình nào ACTIVE ----------

GOOD = "models:\n  - id: M0\n    state: ACTIVE\n"
BROKEN = [
    ("yaml_hong", "models: [\n"),
    ("rong", ""),
    ("khong_co_models", "other:\n  - id: M0\n    state: ACTIVE\n"),
    ("models_khong_phai_danh_sach", "models: M0\n"),
    ("goc_khong_phai_dict", "- id: M0\n  state: ACTIVE\n"),
    ("dong_thieu_id", GOOD + "  - state: ACTIVE\n"),
    ("dong_thieu_state", GOOD + "  - id: M1\n"),
    ("state_chu_thuong", GOOD + "  - id: M1\n    state: active\n"),
    ("state_la", GOOD + "  - id: M1\n    state: LIVE\n"),
    ("dong_khong_phai_dict", GOOD + "  - M1\n"),
    ("id_lap", GOOD + "  - id: M0\n    state: WATCH\n"),
    ("id_khong_phai_chuoi", GOOD + "  - id: 7\n    state: ACTIVE\n"),
]


@pytest.mark.parametrize("name,text", BROKEN, ids=[b[0] for b in BROKEN])
def test_broken_approval_file_activates_nothing(tmp_path, name, text):
    """Tệp hỏng ở bất kỳ dòng nào thì cả tệp vô hiệu: M0 có dòng ACTIVE hợp lệ vẫn không được ACTIVE."""
    reg = _reg(2, state="ACTIVE")
    states, err = _rank(reg, tmp_path, text)
    assert err and set(states.values()) == {"WATCH"}, (name, err)


def test_valid_prefix_alone_does_activate(tmp_path):
    """Đối chứng cho test trên: chỉ phần hợp lệ thì M0 lên ACTIVE, nên lỗi nằm đúng ở dòng hỏng."""
    states, err = _rank(_reg(2, state="ACTIVE"), tmp_path, GOOD)
    assert err is None and states == {"M0": "ACTIVE", "M1": "WATCH"}


def test_missing_approval_file_activates_nothing(tmp_path):
    approved, err = knowledge.load_approved(tmp_path / "khong_co.yaml")
    assert approved == frozenset() and "không đọc được" in err
    reg = _reg(2, state="ACTIVE")
    knowledge.rank_active(reg, "2026-11-20", approved=approved)
    assert {v["state"] for v in reg.values()} == {"WATCH"}


def test_default_reads_the_file_under_root(tmp_path, monkeypatch):
    """rank_active không truyền tập duyệt thì đọc ROOT/state/MODEL_REGISTRY.yaml; thiếu tệp thì không ai ACTIVE."""
    monkeypatch.setattr(knowledge, "ROOT", tmp_path)
    reg = _reg(1, state="ACTIVE")
    knowledge.rank_active(reg, "2026-11-20")
    assert reg["M0"]["state"] == "WATCH"
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "MODEL_REGISTRY.yaml").write_text("models:\n  - id: M0\n    state: ACTIVE\n", encoding="utf-8")
    knowledge.rank_active(reg, "2026-11-21")
    assert reg["M0"]["state"] == "ACTIVE"


# ---------- 4. Sổ giấy giữ tiền mặt khi có 0 mô hình ACTIVE ----------

def _market():
    idx = pd.bdate_range("2026-01-05", periods=30)
    cols = [f"T{i}" for i in range(8)]
    close = pd.DataFrame(np.linspace(10_000, 12_000, len(idx))[:, None] * np.linspace(1, 2, len(cols)),
                         index=idx, columns=cols)
    return close, idx


def _paper(tmp_path, monkeypatch, reg):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(paper, "ROOT", tmp_path)
    close, idx = _market()
    as_of = idx[-1]
    preds = pd.DataFrame([(as_of, m, t, float(s)) for m in reg for s, t in enumerate(close.columns)],
                         columns=["date", "model_id", "ticker", "score"])
    nav, decision = paper.run(str(as_of.date()), close, preds, reg, idx)
    return nav, decision


def test_paper_holds_cash_when_no_model_is_approved(tmp_path, monkeypatch):
    reg = _reg(2)
    knowledge.rank_active(reg, "2026-11-20", approved=frozenset())
    nav, decision = _paper(tmp_path, monkeypatch, reg)
    assert decision["action"] == "NO_ACTION_CASH" and decision["targets"] == ""
    assert nav == config.CFG["paper"]["initial_cash"]


def test_paper_rebalances_only_with_an_approved_model(tmp_path, monkeypatch):
    """Có mô hình được duyệt thì sổ giấy cân bằng lại. Cổng rủi ro của R1 (engine/risk_gate.py) cần giá và khối lượng gốc
    trong kho giá dưới ROOT để đo thanh khoản: dựng một kho hợp lệ trong thư mục tạm, cùng giá với bảng `close` của test
    và khối lượng lớn. Cổng vẫn chạy đủ điều kiện như thật; test không tắt, không đi vòng, không nới cổng."""
    close, _ = _market()
    rows = [{"date": d.date().isoformat(), "ticker": t, "open": float(close.at[d, t]), "high": float(close.at[d, t]),
             "low": float(close.at[d, t]), "close": float(close.at[d, t]), "volume": 10_000_000.0,
             "observed_at": "2026-03-01", "source": "test"} for d in close.index for t in close.columns]
    store = tmp_path / config.CFG["data"]["store_dir"] / "2026-01.csv"
    store.parent.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(store, index=False)
    reg = _reg(2)
    knowledge.rank_active(reg, "2026-11-20", approved=frozenset({"M1"}))
    _, decision = _paper(tmp_path, monkeypatch, reg)
    assert decision["action"] == "REBALANCE" and decision["models"] == "M1"


def test_tests_do_not_touch_the_repo():
    out = subprocess.check_output(["git", "status", "--porcelain", "--", "state", "paper"], cwd=REPO)
    assert out == b""


# ---------- 5. Luồng chuẩn: cổng Owner chạy TRƯỚC quyết định sổ giấy (rà soát trước chấm, PR #79) ----------

def _empty_cycle_inputs(close):
    idx = pd.MultiIndex.from_product([close.index, close.columns], names=["date", "ticker"])
    ds = pd.DataFrame({"y": np.nan}, index=idx)
    allp = pd.DataFrame(columns=["date", "model_id", "ticker", "score"])
    return ds, allp


def test_stale_active_model_is_demoted_by_the_cycle_step_before_paper_decides(tmp_path, monkeypatch):
    """state/model_registry.json còn mô hình ACTIVE cũ, YAML của Owner là models: []. Bước run_cycle chạy ngay trước sổ
    giấy (knowledge.decay, gọi rank_active) phải hạ mô hình về WATCH; sổ giấy sau đó giữ tiền mặt."""
    monkeypatch.setattr(knowledge, "ROOT", tmp_path)
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "MODEL_REGISTRY.yaml").write_text("models: []\n", encoding="utf-8")
    reg = _reg(2, state="ACTIVE")
    close, idx = _market()
    ds, allp = _empty_cycle_inputs(close)
    knowledge.decay(reg, allp, ds, str(idx[-1].date()))
    assert {v["state"] for v in reg.values()} == {"WATCH"}
    nav, decision = _paper(tmp_path, monkeypatch, reg)
    assert decision["action"] == "NO_ACTION_CASH" and nav == config.CFG["paper"]["initial_cash"]


def test_cycle_runs_the_owner_gate_before_the_paper_decision():
    """Thứ tự trong engine.run_cycle.cycle: khi dữ liệu không đóng băng, decay (gọi rank_active, đọc YAML) chạy rồi lưu sổ
    đăng ký TRƯỚC paper.run; khi đóng băng thì paper.run nhận frozen=skip và không ra quyết định."""
    import inspect

    from engine import run_cycle

    src = inspect.getsource(run_cycle.cycle)
    i_decay = src.index("alerts = knowledge.decay(registry, allp, ds, as_of)")
    i_save = src.index("knowledge.save_registry(registry)")
    i_paper = src.index("paper.run(as_of, close, preds_today, registry, udates")
    assert i_decay < i_save < i_paper
    assert "frozen=skip)" in src[i_paper:i_paper + 200]
    assert "def decay(" in inspect.getsource(knowledge) and "rank_active(reg, as_of)" in inspect.getsource(knowledge.decay)


def test_frozen_data_makes_no_paper_decision_even_with_a_stale_active_model(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(paper, "ROOT", tmp_path)
    close, idx = _market()
    reg = _reg(1, state="ACTIVE")
    preds = pd.DataFrame([(idx[-1], "M0", t, 1.0) for t in close.columns], columns=["date", "model_id", "ticker", "score"])
    nav, decision = paper.run(str(idx[-1].date()), close, preds, reg, idx, frozen=True)
    assert decision["action"] == "NO_DECISION_DATA_QUALITY"
