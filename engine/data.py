"""Data Engine: kho du lieu append-only, giu ban quan sat dau tien (point-in-time).
Kho giu GIA GOC lam bang chung. Moi tinh toan (feature, nhan, paper, Ledger) dung GIA DIEU CHINH tu load_market().

Ghi TANG DAN (ADR-0006, C2): kho cu `data.store` (prices.csv.gz) DONG BANG — khong ghi lai nua. Dong moi vao
`data.store_dir`, moi thang giao dich mot tep CSV `YYYY-MM.csv`; chi NOI THEM vao cuoi tep (thu tu = thu tu quan sat),
khong bao gio viet lai dong cu. tools/ledger_audit.py kiem: kho cu khong doi, moi tep thang cu la tien to cua ban moi."""
import datetime as dt
import hashlib
import json
import pathlib
import numpy as np, pandas as pd
from . import config
from .config import CFG, path
from . import adjust
from . import verified_adjust as va

COLS = ["date", "ticker", "open", "high", "low", "close", "volume", "observed_at", "source"]

def _root(root):
    return pathlib.Path(root) if root is not None else config.ROOT

def load_store(root=None):
    """Kho cu (dong bang) + moi tep thang; trung (date, ticker) thi giu ban quan sat DAU TIEN."""
    r, parts = _root(root), []
    legacy = r / CFG["data"]["store"]
    if legacy.exists():
        parts.append(pd.read_csv(legacy))
    d = r / CFG["data"]["store_dir"]
    if d.is_dir():
        parts += [pd.read_csv(f) for f in sorted(d.glob("*.csv"))]
    parts = [x for x in parts if len(x)]
    if not parts:
        return pd.DataFrame(columns=COLS)
    s = pd.concat(parts, ignore_index=True)[COLS]
    for c in ("date", "observed_at"):     # mot tep co the co ca "YYYY-MM-DD" lan "YYYY-MM-DD HH:MM:SS.ffffff"
        s[c] = pd.to_datetime(s[c], format="ISO8601")
    s = s.sort_values("observed_at", kind="stable").drop_duplicates(["date", "ticker"], keep="first")
    return s.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)

def save_store(df, root=None):
    """Ghi TANG DAN (ADR-0006): chi them dong (date, ticker) chua co trong kho, noi vao cuoi tep thang cua ngay giao dich.
    Dong da co thi GIU NGUYEN ban cu (diem-thoi-gian: ban quan sat dau tien) — truyen vao gia da sua cung khong ghi de.
    Tra ve so dong da them."""
    if df is None or len(df) == 0:
        return 0
    r = _root(root)
    have = load_store(r)
    keys = set(zip(have["date"], have["ticker"])) if len(have) else set()
    df = df[COLS].copy()
    df["date"], df["observed_at"] = pd.to_datetime(df["date"]), pd.to_datetime(df["observed_at"])
    new = df[[(d, t) not in keys for d, t in zip(df["date"], df["ticker"])]]
    new = new.sort_values("observed_at", kind="stable").drop_duplicates(["date", "ticker"], keep="first")
    if new.empty:
        return 0
    d = r / CFG["data"]["store_dir"]
    d.mkdir(parents=True, exist_ok=True)
    new = new.sort_values(["observed_at", "date", "ticker"], kind="stable")
    for month, g in new.groupby(new["date"].dt.strftime("%Y-%m"), sort=True):
        f = d / f"{month}.csv"
        g.to_csv(f, mode="a", header=not f.exists(), index=False)
    return len(new)

def append_rows(store, new):
    """Append-only: neu mot (date, ticker) da co, giu ban quan sat DAU TIEN, khong ghi de qua khu."""
    if new is None or new.empty:
        return store
    allr = pd.concat([store, new[COLS]], ignore_index=True) if len(store) else new[COLS].copy()
    return allr.sort_values("observed_at").drop_duplicates(["date", "ticker"], keep="first")

def _norm(q, t):
    """Chuan hoa bang gia tu moi nguon ve cot date/open/high/low/close/volume."""
    if q is None or len(q) == 0:
        return None
    q = q.copy()
    if isinstance(q.columns, pd.MultiIndex):
        q.columns = q.columns.get_level_values(0)
    q = q.reset_index() if not any(str(c).lower() in ("time", "date", "tradingdate") for c in q.columns) else q
    q.columns = [str(c).lower() for c in q.columns]
    for k in ("time", "tradingdate", "index"):
        if k in q.columns and "date" not in q.columns:
            q = q.rename(columns={k: "date"})
    need = ["date", "open", "high", "low", "close", "volume"]
    if not all(c in q.columns for c in need):
        raise RuntimeError(f"thieu cot, nhan duoc {list(q.columns)}")
    q = q[need].dropna(subset=["close"])
    q["date"] = pd.to_datetime(q["date"]).dt.tz_localize(None).dt.normalize()
    q["ticker"] = t
    return q

def _fetch_vnstock(t, start, end, src):
    import vnstock
    if hasattr(vnstock, "Vnstock"):
        return vnstock.Vnstock().stock(symbol=t, source=src).quote.history(start=start, end=end, interval="1D")
    if hasattr(vnstock, "Quote"):
        return vnstock.Quote(symbol=t, source=src).history(start=start, end=end, interval="1D")
    if hasattr(vnstock, "stock_historical_data"):
        return vnstock.stock_historical_data(symbol=t, start_date=start, end_date=end, resolution="1D", type="stock")
    raise RuntimeError("khong nhan ra API cua phien ban vnstock nay")

def _fetch_yahoo(t, start, end):
    import yfinance as yf
    e = (pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat()
    return yf.download(f"{t}.VN", start=start, end=e, auto_adjust=False, progress=False)

FETCHERS = {"vnstock": lambda t, s, e: _fetch_vnstock(t, s, e, CFG["data"]["vnstock_source"]),
            "yahoo": _fetch_yahoo}

def ingest_tickers():
    """Mã được tải giá và sự kiện quyền: `universe` rồi `data.ingest_extra` (E2b, QĐ-4), không trùng, giữ thứ tự."""
    out = []
    for t in list(CFG["universe"]) + list(CFG["data"].get("ingest_extra") or []):
        if t not in out:
            out.append(t)
    return out

def ingest(end=None):
    """Tai gia theo thu tu nguon trong config (data.sources); nguon sau chi dung khi nguon truoc loi.
    Ghi ro nguon cua tung dong. Tra ve nhat ky DAY DU: loi tung ma, tung nguon (khong chi in ra log)."""
    store = load_store()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    end = (end or dt.date.today()).isoformat()
    sources = list(CFG["data"]["sources"])
    frames, errors, no_new = [], [], []
    for t in ingest_tickers():
        last = store.loc[store.ticker == t, "date"].max() if len(store) else pd.NaT
        start = (last + pd.Timedelta(days=1)).date().isoformat() if pd.notna(last) else CFG["data"]["start"]
        if start > end:
            continue
        q, used = None, None
        for name in sources:
            try:
                q = _norm(FETCHERS[name](t, start, end), t)
                if q is not None and len(q):
                    used = name
                    break
            except Exception as e:
                errors.append({"ticker": t, "source": name, "error": str(e)[:300]})
        if q is None or not len(q):
            no_new.append(t)
            continue
        q["observed_at"], q["source"] = now, used
        frames.append(q)
    new = pd.concat(frames, ignore_index=True) if frames else None
    store = append_rows(store, new)
    errors += fetch_yahoo_actions()
    if store.empty:
        raise RuntimeError("Khong lay duoc du lieu tu nguon nao.\n" + "\n".join(map(str, errors[:20])))
    save_store(store)
    return {"at": now.isoformat(), "end": end, "sources": sources,
            "new_rows": 0 if new is None else len(new),
            "rows_by_source": {} if new is None else new.source.value_counts().to_dict(),
            "tickers_no_new_data": no_new, "errors": errors,
            "last_date_by_ticker": {t: str(d.date()) for t, d in store.groupby("ticker").date.max().items()}}

ingest_vnstock = ingest          # ten cu, giu de tuong thich

def fetch_yahoo_actions():
    """Tai lai TOAN BO lich su co tuc tien / chia tach tu Yahoo (du lieu dan xuat, ghi de moi lan, ghi ngay tai)."""
    try:
        import yfinance as yf
    except Exception as e:
        return [{"ticker": "*", "source": "yahoo_actions", "error": f"khong co yfinance ({e})"}]
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).isoformat()
    rows, errors = [], []
    for t in ingest_tickers():
        try:
            a = yf.Ticker(f"{t}.VN").actions
        except Exception as e:
            errors.append({"ticker": t, "source": "yahoo_actions", "error": str(e)[:300]}); continue
        if a is None or a.empty:
            continue
        for d, r in a.iterrows():
            ex = pd.Timestamp(d).tz_localize(None).normalize() if pd.Timestamp(d).tzinfo else pd.Timestamp(d).normalize()
            if r.get("Dividends", 0) > 0:
                rows.append({"ticker": t, "ex_date": ex.date(), "type": adjust.CASH, "ratio": None,
                             "cash_per_share": float(r["Dividends"]), "source": "yahoo", "source_status": "TU_DONG",
                             "note": "", "fetched_at": now})
            if r.get("Stock Splits", 0) > 0:
                rows.append({"ticker": t, "ex_date": ex.date(), "type": "stock_split", "ratio": float(r["Stock Splits"]),
                             "cash_per_share": None, "source": "yahoo", "source_status": "TU_DONG",
                             "note": "", "fetched_at": now})
    if rows or not errors:
        pd.DataFrame(rows, columns=adjust.EV_COLS + ["fetched_at"]).to_csv(
            path(CFG["corporate_actions"]["yahoo_cache"]), index=False)
    return errors

RESEARCH_INPUTS = ("legacy", "verified")
EVIDENCE_DIR = ("data", "evidence", "corporate_actions")
NOT_IN_CHAIN = "KHONG_VAO_CHUOI_KIEM_CHUNG"


def evidence_docs(root=None):
    """Mọi bản gốc trong các tệp EVIDENCE_MANIFEST*.json dưới data/evidence/corporate_actions/, đọc theo thứ tự tên tệp.
    Đây là nơi DUY NHẤT đầu vào nghiên cứu đọc bản gốc (không dùng DEFAULT_EVIDENCE của tools/build_verified_derivation.py,
    vốn chỉ có manifest đầu)."""
    d = _root(root).joinpath(*EVIDENCE_DIR)
    return va.load_evidence(sorted(d.glob("EVIDENCE_MANIFEST*.json"), key=lambda p: p.name)) if d.is_dir() else []


def window_bounds():
    """(trước, sau) của cửa sổ loại mã QĐ-3 (ADR-0016): trước = horizon_days + 1 (nhãn tại t nhìn tới t + 1 + h, nên mọi
    nhãn chạm phiên sự kiện bị loại); sau = quality.feature_lookback − 1 (đặc trưng nhìn lại ngần ấy phiên kể cả t)."""
    return int(CFG["horizon_days"]) + 1, int(CFG["quality"]["feature_lookback"]) - 1


def window_exclude(index, columns, checks, before, after):
    """Mặt nạ QĐ-3: ô (t, mã) là True khi vị trí của t trên trục ngày `index` thuộc [k − before, k + after], với k là vị trí
    phiên áp dụng của một sự kiện có `taints` của mã đó. Sự kiện lệch ngày: hợp của cửa sổ quanh ngày engine (`trade_date`)
    và quanh ngày chính thức (`official_trade_date`, không có thì `official_ex_date`). Vị trí của một ngày là phiên đầu tiên
    trên trục không sớm hơn ngày đó; ngày sau phiên cuối có vị trí len(index)."""
    index = pd.DatetimeIndex(index)
    m = np.zeros((len(index), len(columns)), dtype=bool)
    col = {t: j for j, t in enumerate(columns)}
    for r in checks[checks["taints"].astype(bool)].itertuples(index=False):
        j = col.get(r.ticker)
        if j is None:
            continue
        days = [r.trade_date, r.official_trade_date if pd.notna(r.official_trade_date) else r.official_ex_date]
        for k in {pd.Timestamp(x) for x in days if pd.notna(x)}:
            pos = int(index.searchsorted(k))
            lo, hi = max(0, pos - before), min(len(index) - 1, pos + after)
            if lo <= hi:
                m[lo:hi + 1, j] = True
    return pd.DataFrame(m, index=index, columns=columns)


CODE_FILES = tuple(pathlib.Path(__file__).resolve().parent / n for n in ("data.py", "adjust.py", "verified_adjust.py"))


def code_fingerprint(files=None):
    """Dấu vân tay xác định của mã tạo đầu vào nghiên cứu: sha256 theo tên tệp và NỘI DUNG từng tệp trong CODE_FILES
    (engine/data.py, engine/adjust.py, engine/verified_adjust.py). Không phụ thuộc đường dẫn hay git; đổi một byte mã (kể cả
    chú thích) thì dấu vân tay đổi."""
    h = hashlib.sha256()
    for f in files or CODE_FILES:
        f = pathlib.Path(f)
        h.update(f"{f.name}:{hashlib.sha256(f.read_bytes()).hexdigest()}\n".encode())
    return "code-sha256:" + h.hexdigest()


UNIVERSE_MODES = ("config", "historical")
UNIVERSE_BY_BASIS = {"CURRENT": "config", "HISTORICAL": "historical"}
VN30_HISTORY = "data/vn30_history.csv"
VN30_COLUMNS = ["effective_date", "ticker", "action", "source_id"]
VN30_MANIFEST = "data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json"
VN30_SIZE = 30
MIN_HISTORY_ROWS = 250                              # bảng chỉ giữ mã có HƠN ngần ấy dòng giá (ngưỡng cũ, giữ nguyên)
# Nhãn `source` của kho THỬ NGHIỆM: chỉ engine.synthetic ("synthetic") và fixture test ("fixture") ghi các nhãn này; ingest
# ghi tên nguồn thật (data.sources). Kho mà MỌI dòng mang một trong các nhãn này là kho thử nghiệm. Chỉ kho thử nghiệm được
# hai ngoại lệ: chế độ "config" khi kho không có mã nào của `universe`, và hợp đồng rổ lịch sử rút gọn (xem load_vn30_history).
TEST_SOURCES = ("synthetic", "fixture")


def is_test_store(store):
    """True khi kho có dòng và mọi dòng đều có `source` ∈ TEST_SOURCES (kho tổng hợp hay fixture test). Nhãn là định danh,
    so không phân biệt hoa thường; một dòng mang nhãn khác (ví dụ "yahoo") là đủ để kho được coi là kho vận hành."""
    return len(store) > 0 and bool(store["source"].astype(str).str.strip().str.lower().isin(TEST_SOURCES).all())


def universe_mode(universe=None):
    """Chế độ rổ (E2b, QĐ-1, QĐ-4): None → theo `universe_basis` (CURRENT → "config", HISTORICAL → "historical")."""
    if universe is None:
        basis = CFG.get("universe_basis", "CURRENT")
        if basis not in UNIVERSE_BY_BASIS:
            raise ValueError(f"universe_basis phải là một trong {tuple(UNIVERSE_BY_BASIS)}, không phải {basis!r}")
        return UNIVERSE_BY_BASIS[basis]
    if universe not in UNIVERSE_MODES:
        raise ValueError(f"universe phải là None hoặc một trong {UNIVERSE_MODES}, không phải {universe!r}")
    return universe


def _vn30_states(h):
    """Phát lại tệp rổ theo ngày (REMOVE trước ADD) → [(ngày, tập thành viên sau ngày đó)]; REMOVE mã vắng hay ADD mã đang
    có là tệp hỏng."""
    members, states = set(), []
    for d, g in h.groupby("effective_date", sort=True):
        for t in g.loc[g["action"] == "REMOVE", "ticker"]:
            if t not in members:
                raise ValueError(f"{VN30_HISTORY} hỏng: REMOVE mã không có mặt {t} {d.date()}")
            members.remove(t)
        for t in g.loc[g["action"] == "ADD", "ticker"]:
            if t in members:
                raise ValueError(f"{VN30_HISTORY} hỏng: ADD mã đang có mặt {t} {d.date()}")
            members.add(t)
        states.append((d, set(members)))
    return states


def _vn30_provenance(root, h, states):
    """Hợp đồng nguồn của rổ lịch sử (như tests/test_vn30_history.py): manifest bản gốc đã ghim đọc được, source_id duy nhất;
    mọi source_id của tệp rổ có trong manifest và cùng ngày hiệu lực; mọi bản gốc trong manifest có tệp, đúng số byte và
    sha256; rổ dựng từ tệp tại ngày hiệu lực của từng bản gốc trùng `members_after` của bản đó."""
    mf = _root(root) / VN30_MANIFEST
    if not mf.is_file():
        raise ValueError(f"{VN30_HISTORY}: thiếu manifest bản gốc {VN30_MANIFEST}")
    try:
        docs = json.loads(mf.read_text(encoding="utf-8"))["source_documents"]
        by_id = {d["source_id"]: d for d in docs}
    except Exception as e:                                       # noqa: BLE001 — mọi lỗi đọc đều là manifest hỏng
        raise ValueError(f"{VN30_MANIFEST} hỏng: {e}") from e
    if len(by_id) != len(docs):
        raise ValueError(f"{VN30_MANIFEST} hỏng: source_id trùng")
    for r in h.itertuples(index=False):
        d = by_id.get(r.source_id)
        if d is None:
            raise ValueError(f"{VN30_HISTORY}: source_id {r.source_id!r} ({r.ticker} {r.effective_date.date()}) không có "
                             f"trong {VN30_MANIFEST}")
        if d.get("effective_date") != str(r.effective_date.date()):
            raise ValueError(f"{VN30_HISTORY}: {r.ticker} {r.effective_date.date()} khác ngày hiệu lực của bản gốc "
                             f"{r.source_id} ({d.get('effective_date')})")
    for d in docs:
        f = _root(root) / str(d.get("path", ""))
        if not d.get("path") or not f.is_file():
            raise ValueError(f"{VN30_MANIFEST}: thiếu tệp bản gốc {d.get('path')!r} ({d['source_id']})")
        blob = f.read_bytes()
        if len(blob) != d.get("bytes") or hashlib.sha256(blob).hexdigest() != d.get("sha256"):
            raise ValueError(f"{VN30_MANIFEST}: bản gốc {d['source_id']} lệch số byte hoặc sha256")
        at = [m for day, m in states if str(day.date()) <= str(d.get("effective_date"))]
        if not at or at[-1] != set(d.get("members_after") or []):
            raise ValueError(f"{VN30_HISTORY}: rổ tại {d.get('effective_date')} không khớp members_after của {d['source_id']}")


def load_vn30_history(root=None, strict=True):
    """data/vn30_history.csv → bảng (effective_date, ticker, action, source_id), đã kiểm. Tệp thiếu hoặc hỏng thì ném lỗi:
    chế độ "historical" không tự chuyển sang "config".
    Luôn kiểm: đúng bốn cột VN30_COLUMNS theo thứ tự, có ít nhất một dòng, không ô trống (kể cả source_id), ngày YYYY-MM-DD,
    mã ba ký tự [A-Z0-9], action ∈ {ADD, REMOVE}, một mã không có hai dòng trong cùng ngày, phát lại hợp lệ.
    strict=True (mặc định; mọi kho vận hành): thêm rổ đúng 30 mã sau mỗi ngày hiệu lực và hợp đồng nguồn (_vn30_provenance).
    strict=False chỉ dành cho kho thử nghiệm (is_test_store): rổ giả của fixture không có 30 mã hay bản gốc ghim."""
    f = _root(root) / VN30_HISTORY
    if not f.is_file():
        raise FileNotFoundError(f"thiếu {VN30_HISTORY}: chế độ universe='historical' cần rổ VN30 theo kỳ")
    try:
        h = pd.read_csv(f, dtype=str, keep_default_na=False)
    except Exception as e:                                       # noqa: BLE001 — mọi lỗi đọc đều là tệp hỏng
        raise ValueError(f"{VN30_HISTORY} hỏng: {e}") from e
    if list(h.columns) != VN30_COLUMNS or h.empty:
        raise ValueError(f"{VN30_HISTORY} hỏng: cần đúng cột {VN30_COLUMNS} và ít nhất một dòng, có {list(h.columns)}")
    h = h.fillna("").apply(lambda c: c.astype(str).str.strip())
    if (h == "").any().any():
        raise ValueError(f"{VN30_HISTORY} hỏng: có ô trống (mọi dòng cần đủ effective_date, ticker, action, source_id)")
    if not h["effective_date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError(f"{VN30_HISTORY} hỏng: effective_date không theo YYYY-MM-DD")
    try:
        h["effective_date"] = pd.to_datetime(h["effective_date"], format="%Y-%m-%d")
    except (ValueError, TypeError) as e:
        raise ValueError(f"{VN30_HISTORY} hỏng: effective_date không phải ngày ({e})") from e
    if not h["ticker"].str.fullmatch(r"[A-Z0-9]{3}").all():
        raise ValueError(f"{VN30_HISTORY} hỏng: mã không phải ba ký tự [A-Z0-9]")
    odd = sorted(set(h["action"]) - {"ADD", "REMOVE"})
    if odd:
        raise ValueError(f"{VN30_HISTORY} hỏng: action lạ {odd}")
    if h.duplicated(["effective_date", "ticker"]).any():
        raise ValueError(f"{VN30_HISTORY} hỏng: một mã có hai dòng trong cùng ngày hiệu lực")
    states = _vn30_states(h)
    if strict:
        bad = [(str(d.date()), len(m)) for d, m in states if len(m) != VN30_SIZE]
        if bad:
            raise ValueError(f"{VN30_HISTORY} hỏng: rổ phải đúng {VN30_SIZE} mã sau mỗi ngày hiệu lực, có {bad}")
        _vn30_provenance(root, h, states)
    return h.sort_values(["effective_date", "ticker"], kind="stable").reset_index(drop=True)


def membership(index, hist):
    """Ma trận thành viên (ngày × mã có trong tệp lịch sử). ADD có hiệu lực từ ngày ghi, tính cả ngày đó; REMOVE cũng vậy
    (từ ngày ghi mã không còn là thành viên). Trước ngày hiệu lực đầu tiên của tệp: không mã nào là thành viên."""
    index = pd.DatetimeIndex(index)
    M = pd.DataFrame(False, index=index, columns=sorted(hist["ticker"].unique()))
    for e in hist.sort_values("effective_date", kind="stable").itertuples(index=False):
        M.loc[index >= e.effective_date, e.ticker] = e.action == "ADD"
    return M


def _universe_columns(columns, mode, hist, test_store):
    """Cột (mã) của bảng giá theo chế độ rổ → (cột, ghi chú pit_gaps).
      - "config": chỉ mã thuộc `universe`; mã `data.ingest_extra` hay mã bất kỳ ngoài `universe` không lọt vào. Kho không
        có mã nào của `universe` thì DỪNG (ValueError), trừ kho thử nghiệm (is_test_store: mọi dòng có source ∈
        TEST_SOURCES) — kho đó giữ mã của nó trừ mã `ingest_extra` ngoài `universe`, và ghi chú điều đó.
      - "historical": mọi mã từng có tên trong data/vn30_history.csv (lọc theo ngày làm ở bước sau)."""
    if mode == "historical":
        names = set(hist["ticker"])
        return [c for c in columns if c in names], []
    u = set(CFG["universe"])
    cols = [c for c in columns if c in u]
    if cols:
        return cols, []
    if not test_store:
        raise ValueError("chế độ universe='config': kho không có mã nào thuộc universe của config — dừng, không nghiên cứu "
                         f"trên tập mã ngoài universe (mã trong kho: {sorted(columns)[:10]})")
    extra = set(CFG["data"].get("ingest_extra") or []) - u
    return [c for c in columns if c not in extra], [
        f"kho thử nghiệm (mọi dòng có source ∈ {list(TEST_SOURCES)}) không có mã nào của universe: bảng giữ mã của kho, "
        "trừ data.ingest_extra"]


SESSION_MODES = ("keep", "calendar")
UNANNOUNCED = "CHUA_CO_THONG_BAO"           # source_id của ngày lịch HOSE chưa có thông báo nghỉ lễ
PIT_MODES_ONLY = "PIT_MODES_ONLY"           # đủ ba chế độ kỹ thuật và có lịch; KHÔNG phải chứng nhận point-in-time
# Mã đọc lịch phiên (risk_gate.load_calendar): vào derivation_id của chế độ sessions="calendar"
CALENDAR_CODE_FILES = (pathlib.Path(__file__).resolve().parent / "risk_gate.py",)
PIT_EVIDENCE_GAPS = (
    "giá lịch sử không có vintage: observed_at của kho là lúc tải về, không phải lúc giá được biết (ADR-0009 mục 4)",
    "PIT-001 NOT_READY (tools/pit001_audit.py): chưa đủ điều kiện tuyên bố point-in-time",
)


def non_session_days(dates, volume, basket=None, root=None):
    """Phân loại ngày trên trục `dates` (E2c, QĐ-1 và QĐ-11a của ADR-0016; Owner xác nhận 22/11/2026) → dict.

    «Có giá» của một ngày: ít nhất một thành viên rổ có dòng giá với khối lượng > 0 ở ngày đó (dòng khối lượng 0, ví dụ
    Yahoo lặp giá phiên trước vào ngày nghỉ, coi như không có giá). `volume`: bảng khối lượng của cả kho (ngày × mã).
    `basket(index)` → bảng bool (ngày × mã) các thành viên rổ; None = mọi mã của `volume`.
    Lịch data/trading_calendar.csv đọc bằng risk_gate.load_calendar: tệp hỏng thì ValueError đi tiếp, không dự phòng âm
    thầm; không có tệp thì mọi ngày theo quy tắc ngoài vùng lịch.
      - "calendar": ngày trong vùng lịch phủ, lịch ghi is_session=0 → không phải phiên;
      - "unannounced_no_price": ngày lịch ghi is_session=1 với source_id=CHUA_CO_THONG_BAO mà không có giá → không phải phiên;
      - "zero_volume": ngày ngoài vùng lịch phủ (hoặc không có tệp lịch) mà không có giá → không phải phiên;
      - "missing": phiên chính thức (lịch ghi is_session=1, nguồn là thông báo HOSE hoặc HOSE_DEFAULT) trong khoảng dữ
        liệu [ngày đầu, ngày cuối của `dates`] mà không có giá, kể cả ngày kho không có dòng nào. Vẫn là phiên;
      - "unannounced": mọi ngày lịch ghi CHUA_CO_THONG_BAO trong khoảng dữ liệu;
      - "coverage": [ngày đầu, ngày cuối] của lịch, hoặc None khi không có tệp lịch."""
    from . import risk_gate                     # risk_gate không import data: import tại chỗ, không tạo vòng
    dates = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(dates))))
    cal = risk_gate.load_calendar(_root(root))
    out = {"calendar": [], "unannounced_no_price": [], "zero_volume": [], "missing": [], "unannounced": [],
           "coverage": None}
    if not len(dates):
        return out
    src, official = {}, []
    if cal:
        lo, hi = pd.Timestamp(min(cal)), pd.Timestamp(max(cal))
        out["coverage"] = [lo, hi]
        t = pd.read_csv(_root(root).joinpath(*risk_gate.CALENDAR), dtype=str, keep_default_na=False)
        src = dict(zip(t["date"], t["source_id"])) if "source_id" in t.columns else {}
        official = [pd.Timestamp(d) for d, x in cal.items() if x == 1 and src.get(d) != UNANNOUNCED
                    and dates[0] <= pd.Timestamp(d) <= dates[-1]]
        out["unannounced"] = sorted(pd.Timestamp(d) for d, x in src.items() if x == UNANNOUNCED
                                    and dates[0] <= pd.Timestamp(d) <= dates[-1])
    days = dates.union(pd.DatetimeIndex(official))
    v = volume.reindex(index=days)
    m = (basket(days) if basket is not None else pd.DataFrame(True, index=days, columns=v.columns))
    m = m.reindex(index=days, columns=v.columns, fill_value=False).astype(bool)
    priced = ((v > 0) & m).any(axis=1)          # NaN > 0 là False: thiếu dòng = không có giá
    for d in days:
        iso = d.date().isoformat()
        if cal and lo <= d <= hi:
            if cal[iso] == 0:
                out["calendar"].append(d)
            elif not bool(priced.loc[d]):
                out["unannounced_no_price" if src.get(iso) == UNANNOUNCED else "missing"].append(d)
        elif not bool(priced.loc[d]):
            out["zero_volume"].append(d)
    return out


def _basket(mode, hist, cols):
    """Thành viên rổ từng ngày cho non_session_days: "config" = các mã của bảng; "historical" = thành viên theo
    data/vn30_history.csv. Trước ngày hiệu lực đầu tiên của tệp chưa biết rổ: dùng các mã của bảng."""
    def f(index):
        index = pd.DatetimeIndex(index)
        if mode != "historical":
            return pd.DataFrame(True, index=index, columns=cols)
        M = membership(index, hist).reindex(columns=cols, fill_value=False)
        M.loc[index < hist["effective_date"].min()] = True
        return M
    return f


def _iso(days):
    return [str(pd.Timestamp(d).date()) for d in days]


def _session_gaps(ns, dates, sessions):
    """Ghi chú pit_gaps về trục phiên."""
    out = ["trục ngày chưa lọc ngày nghỉ theo lịch phiên HOSE"] if sessions == "keep" else []
    if ns["coverage"] is None:
        out.append("không có data/trading_calendar.csv: không có lịch phiên HOSE; ngày chỉ là phiên khi một thành viên "
                   "rổ có khối lượng > 0")
    elif sessions == "calendar":
        lo, hi = ns["coverage"]
        if len(dates) and (dates[0] < lo or dates[-1] > hi):
            out.append(f"lịch phiên HOSE đã ghim chỉ phủ {lo.date()} – {hi.date()}: ngoài vùng đó ngày chỉ là phiên khi một "
                       "thành viên rổ có khối lượng > 0 (quy tắc thay thế, không phải lịch chính thức)")
    if sessions == "calendar" and ns["unannounced"]:
        out.append(f"{len(ns['unannounced'])} ngày trong khoảng dữ liệu lịch còn ghi {UNANNOUNCED} (chưa có thông báo "
                   "nghỉ lễ của HOSE)")
    if sessions == "calendar" and ns["missing"]:
        out.append(f"{len(ns['missing'])} phiên chính thức trong khoảng dữ liệu không thành viên rổ nào có khối lượng > 0: "
                   + ", ".join(_iso(ns["missing"])))
    return out


def _derivation_id(research_input, cut, docs, ev, universe=None, sessions=None):
    """Định danh dẫn xuất chỉ phụ thuộc đầu vào và phiên bản mã: chế độ, ngày cắt, hash kho giá, hash CSV sự kiện, metadata
    các bản gốc đã dùng (chế độ legacy không dùng bản gốc nên không có), config (tệp và giá trị đang dùng), và dấu vân tay mã
    (code_fingerprint) ở trường code_commit của verified_adjust.derivation_manifest (ADR-0009). Chế độ rổ "historical" thêm
    `universe` (chế độ và sha256 của data/vn30_history.csv); chế độ "config" giữ khóa cũ (universe nằm trong config).
    Chế độ trục phiên "calendar" thêm `sessions` (chế độ, sha256 của data/trading_calendar.csv và dấu vân tay mã đọc lịch
    CALENDAR_CODE_FILES); "keep" giữ khóa cũ."""
    m = va.derivation_manifest(root=config.ROOT, cfg=CFG, as_of=cut, docs=docs, ev=ev, code_commit=code_fingerprint())
    cfg_now = hashlib.sha256(json.dumps(CFG, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    key = {"research_input": research_input, "verified_derivation_id": m["derivation_id"], "config_values": cfg_now}
    if universe is not None:
        key["universe"] = universe
    if sessions is not None:
        key["sessions"] = sessions
    return "RI-" + hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]


def load_market(as_of=None, research_input="legacy", universe=None, sessions="keep"):
    """Bang gia DIEU CHINH point-in-time + co loi du lieu + bao cao chat luong.
    Tra ve dict: close, volume (dieu chinh), raw_close, bad (co loi), events, quality, flags.

    research_input (E2a, QĐ-1 và QĐ-3 của ADR-0016):
      - "legacy" (mặc định): chuỗi điều chỉnh hiện hành của engine.adjust; mọi khóa cũ không đổi từng byte;
      - "verified": chỉ sự kiện cổ phiếu vào chuỗi kiểm chứng (engine.verified_adjust, bản gốc từ evidence_docs, ngày cắt là
        as_of hoặc phiên cuối) được áp hệ số; sự kiện không vào chuỗi không mang trạng thái APPLIED trong `events`. Thêm
        `exclude` (mặt nạ cửa sổ QĐ-3), `eligible` (có giá và không bị loại) và `event_checks` (bảng kiểm sự kiện).
    Cả hai chế độ thêm: research_input, derivation_id, pit_label, pit_gaps (xem cuối).
    Chế độ legacy không đọc manifest bản gốc, nên manifest hỏng không làm nó dừng; chế độ verified thì dừng.

    universe (E2b, QĐ-1 và QĐ-4 của ADR-0016) — rổ mã của bảng:
      - None (mặc định): theo `universe_basis` (CURRENT → "config", HISTORICAL → "historical");
      - "config": chỉ mã thuộc `universe` của config; mã `data.ingest_extra` có trong kho không lọt vào (xem _universe_columns);
      - "historical": theo data/vn30_history.csv. Tại mỗi ngày chỉ giữ thành viên của ngày đó: ô của mã không phải thành
        viên có close, volume, raw_close là NaN và `eligible` False. Trước ngày hiệu lực đầu tiên của tệp không mã nào
        eligible (`quality.universe_unknown_before`). Tệp thiếu hoặc hỏng thì ném lỗi. Thêm khóa `eligible` (cả ở legacy)
        và `members`; `quality` thêm `universe_mode`, `members_without_prices`, `members_last_session`.
    Mọi chế độ: mã bị loại vì không có HƠN 250 dòng giá được liệt kê (mã → số dòng) ở `quality.dropped_short_history`
    (khóa chỉ có khi danh sách khác rỗng); sự kiện quyền được lọc theo các mã có trong bảng trước adjust.build_events.

    sessions (E2c, QĐ-1 và QĐ-11a của ADR-0016) — trục ngày của bảng. Ngày không phải phiên và phiên chính thức thiếu giá:
    xem non_session_days («có giá» = một thành viên rổ có khối lượng > 0). Lịch hỏng thì ném lỗi ở cả hai chế độ.
      - "keep" (mặc định): trục ngày không đổi; `quality.sessions` chỉ liệt kê (`dropped` = 0, `inserted` rỗng);
      - "calendar": bỏ ngày không phải phiên và thêm (giá NaN) phiên chính thức kho không có dòng nào, TRƯỚC khi tính hệ số,
        mặt nạ cửa sổ QĐ-3 (đếm phiên trên trục này) và báo cáo chất lượng. Phiên chính thức thiếu giá vẫn ở trên trục.
    `quality.sessions` = {mode, calendar_coverage, non_session_calendar, non_session_unannounced, non_session_zero_volume,
    missing_sessions, inserted, dropped, unannounced}. Khóa này không vào state/ENGINE_STATE.json (engine/report.py).
    pit_label (Owner xác nhận 22/11/2026): "PIT_MODES_ONLY" chỉ khi đủ research_input="verified", rổ "historical",
    sessions="calendar" VÀ có data/trading_calendar.csv đọc được; khi đó thêm `pit_from` = ngày hiệu lực đầu tiên của
    data/vn30_history.csv. Mọi trường hợp khác là "RETROSPECTIVE". PIT_MODES_ONLY chỉ nói ba chế độ kỹ thuật đang bật, KHÔNG
    chứng nhận dữ liệu point-in-time; không mã nào trả "POINT_IN_TIME" (để dành cho khi PIT-001 READY và có quyết định
    riêng). pit_gaps luôn có, gồm PIT_EVIDENCE_GAPS (giá không có vintage; PIT-001 NOT_READY)."""
    if research_input not in RESEARCH_INPUTS:
        raise ValueError(f"research_input phải là một trong {RESEARCH_INPUTS}, không phải {research_input!r}")
    if sessions not in SESSION_MODES:
        raise ValueError(f"sessions phải là một trong {SESSION_MODES}, không phải {sessions!r}")
    umode = universe_mode(universe)
    s = load_store()
    if s.empty:
        raise RuntimeError("Kho du lieu trong. Chay ingest hoac tao du lieu synthetic.")
    test_store = is_test_store(s)                    # cả kho, trước khi cắt as_of
    # rổ lịch sử thiếu/hỏng: dừng trước khi dựng bảng; hợp đồng đầy đủ trừ kho thử nghiệm
    hist = load_vn30_history(strict=not test_store) if umode == "historical" else None
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
    obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    cols, ugaps = _universe_columns(list(raw.columns), umode, hist, test_store)
    ns = non_session_days(raw.index, vol, _basket(umode, hist, cols))       # lịch hỏng: lỗi ở cả hai chế độ
    dropped, inserted = 0, []
    if sessions == "calendar":                      # trục phiên dựng TRƯỚC mọi phép tính sau
        off = set(ns["calendar"]) | set(ns["unannounced_no_price"]) | set(ns["zero_volume"])
        inserted = [d for d in ns["missing"] if d not in raw.index]
        axis = raw.index[~raw.index.isin(list(off))].union(pd.DatetimeIndex(inserted))
        raw, vol, obs = raw.reindex(axis), vol.reindex(axis), obs.reindex(axis)
        dropped = len(off)
        if not raw.notna().any().any():
            raise RuntimeError("sessions='calendar': không còn phiên nào có giá sau khi dựng trục phiên")
    raw, vol, obs = raw[cols], vol[cols], obs[cols]
    n_rows = raw.notna().sum()
    keep = raw.columns[n_rows > MIN_HISTORY_ROWS]
    short = {t: int(n_rows[t]) for t in raw.columns if t not in keep}
    raw, vol, obs = raw[keep], vol[keep], obs[keep]
    man, yah = adjust.load_manual(), adjust.load_yahoo()             # sự kiện của mã không có trong bảng: bỏ trước khi xét
    events = adjust.build_events(raw, obs, man[man["ticker"].isin(keep)], yah[yah["ticker"].isin(keep)])
    cut = pd.Timestamp(as_of) if as_of is not None else raw.index[-1]
    docs, checks = [], None                          # legacy không đọc manifest bản gốc nào (QĐ-1: mặc định giữ hành vi cũ)
    if research_input == "verified":
        docs = evidence_docs()                       # manifest hỏng thì ném lỗi: chế độ đã kiểm không chạy với bản gốc hỏng
        checks = va.verify_events(events, raw, docs, evidence_root=config.ROOT, as_of=cut)
        F, S = va.verified_factors(raw.index, raw.columns, checks)
        events = checks[list(events.columns)].copy()
        events.loc[(events["status"] == "APPLIED") & ~checks["in_verified_chain"].astype(bool), "status"] = NOT_IN_CHAIN
    else:
        F, S = adjust.factors(raw.index, raw.columns, events)
    adj = raw * F
    members = None
    if umode == "historical":                       # chất lượng dữ liệu chỉ xét ô thành viên: biến động của mã lúc ngoài rổ
        members = membership(raw.index, hist).reindex(columns=raw.columns, fill_value=False)   # không gắn cờ, không dừng
        adj = adj.where(members)
    bad, rep, flags = adjust.quality(adj)
    rep["sessions"] = {"mode": sessions, "calendar_coverage": None if ns["coverage"] is None else _iso(ns["coverage"]),
                       "non_session_calendar": _iso(ns["calendar"]),
                       "non_session_unannounced": _iso(ns["unannounced_no_price"]),
                       "non_session_zero_volume": _iso(ns["zero_volume"]), "missing_sessions": _iso(ns["missing"]),
                       "inserted": _iso(inserted), "dropped": dropped, "unannounced": _iso(ns["unannounced"])}
    rep["events"] = events.status.value_counts().to_dict() if len(events) else {}
    rep["events_not_applied"] = [f"{e.ticker} {e.ex_date.date()} {e.type} ({e.source}): {e.status}"
                                 for e in events.itertuples() if e.status not in ("APPLIED", "CHUA_DEN_HAN",
                                                                                  "DA_NAM_TRONG_GIA_NGUON")]
    rep["events_applied"] = [f"{e.ticker} {e.trade_date.date()} {e.type} ({e.source}, {e.source_status}): "
                             f"gốc {e.raw_return:+.2%} → điều chỉnh {e.adj_return:+.2%}"
                             for e in events.itertuples() if e.status == "APPLIED"]
    if short:
        rep["dropped_short_history"] = short
    close, volume, raw_out = adj.ffill(limit=5), (vol / S).fillna(0), raw
    if umode == "historical":
        close, volume, raw_out = close.where(members), volume.where(members), raw.where(members)
        ever = membership(raw.index, hist).any()
        last = membership(raw.index[-1:], hist).iloc[0]
        rep["universe_mode"] = "historical"
        rep["universe_unknown_before"] = str(hist["effective_date"].min().date())
        rep["members_without_prices"] = {
            t: (f"bị loại vì thiếu lịch sử ({short[t]} dòng)" if t in short else "không có dòng giá trong kho")
            for t in sorted(ever[ever].index) if t not in raw.columns}
        n_last = int(last.sum())
        with_px = [t for t in last[last].index if t in raw.columns and pd.notna(raw.at[raw.index[-1], t])]
        rep["members_last_session"] = {"date": str(raw.index[-1].date()), "members": n_last, "with_prices": len(with_px)}
    out = {"close": close, "volume": volume, "raw_close": raw_out, "bad": bad,
           "events": events, "quality": rep, "flags": flags}
    sgaps = _session_gaps(ns, raw.index, sessions)
    if umode == "historical":
        gaps = [f"rổ theo thành viên VN30 từng ngày ({VN30_HISTORY}), chỉ có từ {rep['universe_unknown_before']}: trước "
                "ngày đó không mã nào eligible", *sgaps]
    else:
        gaps = ["rổ theo cấu hình hiện tại (universe), chưa theo thành viên VN30 từng ngày", *ugaps, *sgaps]
    if research_input == "legacy":
        gaps.append("sự kiện quyền chưa kiểm: hệ số theo chuỗi điều chỉnh hiện hành, gồm sự kiện chưa đối chiếu bản gốc")
    gaps += list(PIT_EVIDENCE_GAPS)
    uid = None if umode == "config" else {
        "mode": umode, "vn30_history_sha256": va.sha256_file(config.ROOT / VN30_HISTORY),
        "vn30_manifest_sha256": va.sha256_file(config.ROOT / VN30_MANIFEST) if (config.ROOT / VN30_MANIFEST).is_file() else None}
    sid = None if sessions == "keep" else {
        "mode": sessions, "trading_calendar_sha256": va.sha256_file(config.ROOT / "data/trading_calendar.csv")
        if (config.ROOT / "data/trading_calendar.csv").is_file() else None,
        "calendar_code": code_fingerprint(CALENDAR_CODE_FILES)}
    pit = (research_input == "verified" and umode == "historical" and sessions == "calendar"
           and ns["coverage"] is not None)          # đủ ba chế độ VÀ có lịch đọc được (lịch hỏng đã ném lỗi ở trên)
    out.update(research_input=research_input, derivation_id=_derivation_id(research_input, cut, docs,
                                                                             events if checks is None else checks, uid, sid),
               pit_label=PIT_MODES_ONLY if pit else "RETROSPECTIVE", pit_gaps=gaps)
    if pit:
        out["pit_from"] = rep["universe_unknown_before"]
    if checks is not None:
        exclude = window_exclude(raw.index, raw.columns, checks, *window_bounds())
        out.update(exclude=exclude, eligible=raw_out.notna() & ~exclude, event_checks=checks)
    if members is not None:
        out.update(members=members, eligible=out.get("eligible", raw_out.notna()) & members)
        rep["members_last_session"]["eligible"] = int(out["eligible"].iloc[-1].sum())
    return out

def write_derived(mk=None):
    """Ghi du lieu DAN XUAT (tinh lai toan bo, ghi de, co ngay tinh): he so dieu chinh + co loi du lieu."""
    mk = mk or load_market()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).isoformat()
    ev = mk["events"].copy()
    ev["computed_at"] = now
    ev.to_csv(path(CFG["corporate_actions"]["derived"]), index=False)
    fl = pd.DataFrame(mk["flags"], columns=["date", "ticker", "return", "allowed"])
    fl["computed_at"] = now
    fl.to_csv(path(CFG["quality"]["flags_file"]), index=False)
    return now

def load_panel(as_of=None):
    """Tuong thich nguoc: (close, volume) DA DIEU CHINH."""
    mk = load_market(as_of)
    return mk["close"], mk["volume"]
