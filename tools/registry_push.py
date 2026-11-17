"""Ghi bền sổ đăng ký thử lên nhánh main TRƯỚC khi chạy backtest (governance/LAWS.md L-06, ADR-0003).

engine/research.register_trial gọi tệp này khi biến môi trường TTC_REGISTRY_PUSH=1 (workflow daily_cycle.yml đặt). Nếu
không đẩy được, register_trial báo lỗi và backtest KHÔNG chạy. Nhờ đó một vòng học hỏng giữa chừng vẫn để lại dòng đăng
ký trên main: lần chạy sau không dùng lại mã thử (research.next_trial_number đếm cả đăng ký chưa có kết quả), nên số lần
thử dùng cho ngưỡng Bonferroni và Deflated Sharpe không bị đếm thiếu.

Cách ghi: dựng một commit chỉ đổi research/trial_registry.jsonl trên đầu origin/main bằng lệnh git cấp thấp (chỉ mục tạm),
không đụng thư mục làm việc và chỉ mục của vòng học đang chạy. Sổ trên main phải là tiền tố của bản đang chạy (chỉ ghi
thêm); main đổi giữa chừng (workflow nhận dự báo vừa đẩy) thì lấy lại và thử lại. Bản trên main trùng từng byte với bản
đang chạy KHÔNG tính là đã đẩy xong: hai vòng học đăng ký cùng một giây ra cùng một dòng, vòng thua sẽ thấy trùng và
nếu coi là thành công thì vẫn chạy backtest — thành hai kết quả cho một mã thử. Đóng lại: chỉ thoát 0 khi chính lần gọi
này đẩy được.

Dùng: python tools/registry_push.py --root <thư mục kho> <mã thử>        Thoát 0 chỉ khi chính lần gọi này đẩy được dòng lên main.
"""
import argparse, os, pathlib, subprocess, sys, tempfile, time

REG = "research/trial_registry.jsonl"


def _git(root, *args, env=None, data=None):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=env, input=data)


def push(root, trial_id, remote="origin", branch="main", tries=6, wait=5.0) -> str:
    root = pathlib.Path(root)
    local = (root / REG).read_bytes()
    ident = {**os.environ, "GIT_AUTHOR_NAME": "ttc-engine", "GIT_AUTHOR_EMAIL": "ttc-engine@users.noreply.github.com",
             "GIT_COMMITTER_NAME": "ttc-engine", "GIT_COMMITTER_EMAIL": "ttc-engine@users.noreply.github.com"}
    last = ""
    for i in range(tries):
        if i:
            time.sleep(wait * i)
        r = _git(root, "fetch", "-q", remote, branch)
        if r.returncode != 0:
            last = "git fetch: " + r.stderr.decode("utf-8", "replace").strip(); continue
        tip = _git(root, "rev-parse", "FETCH_HEAD").stdout.decode().strip()
        shown = _git(root, "show", f"{tip}:{REG}")
        on_main = shown.stdout if shown.returncode == 0 else b""
        if on_main == local:
            # Trùng từng byte trước khi CHÍNH lần gọi này đẩy xong. Hai vòng học trong cùng một giây ra cùng một dòng JSON
            # (registered_at chỉ tới giây): vòng đẩy sau thấy sổ đã trùng và không được chạy backtest. Lần đẩy trước đã tới
            # kho mà máy này không nhận được cũng dừng — mã thử đã nằm trên main, lần sau lấy số tiếp theo, không đếm thiếu.
            raise RuntimeError(f"sổ đăng ký trên {branch} đã trùng bản đang chạy trước khi vòng này đẩy xong — hai vòng học "
                               "đăng ký cùng nội dung, hoặc lần đẩy trước đã tới kho mà máy này không nhận được; dừng, không "
                               "ghi đè, không chạy backtest")
        if not local.startswith(on_main):
            raise RuntimeError(f"sổ đăng ký trên {branch} không phải tiền tố của bản đang chạy — có dòng trên {branch} mà "
                               "vòng học này không có (hai vòng học chạy cùng lúc, hoặc sổ bị sửa); dừng, không ghi đè")
        blob = _git(root, "hash-object", "-w", "--", REG).stdout.decode().strip()
        with tempfile.TemporaryDirectory() as tmp:
            env = {**ident, "GIT_INDEX_FILE": str(pathlib.Path(tmp) / "index")}
            steps = (("read-tree", tip), ("update-index", "--add", "--cacheinfo", f"100644,{blob},{REG}"))
            bad = next((s for s in steps if _git(root, *s, env=env).returncode != 0), None)
            if bad or not blob:
                last = f"git {bad[0] if bad else 'hash-object'} lỗi"; continue
            tree = _git(root, "write-tree", env=env).stdout.decode().strip()
        c = _git(root, "commit-tree", tree, "-p", tip, "-m", f"L-06: dang ky thu {trial_id} truoc khi chay", env=ident)
        commit = c.stdout.decode().strip()
        if c.returncode != 0 or not commit:
            last = "git commit-tree: " + c.stderr.decode("utf-8", "replace").strip(); continue
        r = _git(root, "push", "-q", remote, f"{commit}:refs/heads/{branch}")
        if r.returncode == 0:
            return f"{trial_id}: đã đẩy đăng ký lên {branch} ({commit[:7]})"
        last = "git push: " + r.stderr.decode("utf-8", "replace").strip()
    raise RuntimeError(f"không đẩy được sổ đăng ký lên {branch} sau {tries} lần ({last})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trial_id")
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--tries", type=int, default=6)
    ap.add_argument("--wait", type=float, default=5.0)
    a = ap.parse_args()
    try:
        print(push(a.root, a.trial_id, tries=a.tries, wait=a.wait))
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"LỖI L-06: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
