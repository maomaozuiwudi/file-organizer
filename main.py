"""文件整理助手 v1.0 — 三合一文件管理: 归位整理+一键迁移+快速启动 FTS5"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os, sys, shutil, sqlite3, threading, time

class FileOrganizerApp:
    def __init__(self):
        self.root = tk.Tk(); self.root.title("文件整理助手 v1.0"); self.root.geometry("950x650")
        self.db = sqlite3.connect(":memory:"); self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(path, name)")
        self._build_ui()
    def _build_ui(self):
        h = tk.Frame(self.root, bg="#16a085", height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text=" 文件整理助手 v1.0", font=("Microsoft YaHei", 14, "bold"), fg="white", bg="#16a085").pack(side=tk.LEFT, padx=15, pady=8)
        nb = ttk.Notebook(self.root); nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        # Tab1: 归位整理
        t1 = tk.Frame(nb, bg="white"); nb.add(t1, text="归位整理")
        tk.Label(t1, text="按扩展名分类整理文件到子文件夹", font=("Microsoft YaHei", 11, "bold"), bg="white").pack(pady=10)
        f1 = tk.Frame(t1, bg="white"); f1.pack(fill=tk.X, padx=15, pady=5)
        self.dir1_var = tk.StringVar(); tk.Entry(f1, textvariable=self.dir1_var, font=("Microsoft YaHei", 10), width=50).pack(side=tk.LEFT, ipady=2)
        tk.Button(f1, text="浏览", font=("Microsoft YaHei", 9), command=lambda: self.dir1_var.set(filedialog.askdirectory() or "")).pack(side=tk.LEFT, padx=5)
        self.org_btn = tk.Button(f1, text="开始整理", font=("Microsoft YaHei", 10, "bold"), bg="#16a085", fg="white", relief="flat", padx=20, pady=5, command=lambda: threading.Thread(target=self._organize, daemon=True).start())
        self.org_btn.pack(side=tk.LEFT, padx=15)
        self.org_result = scrolledtext.ScrolledText(t1, font=("Microsoft YaHei", 10), relief="flat", borderwidth=1, padx=10, pady=10)
        self.org_result.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        # Tab2: 快速启动
        t2 = tk.Frame(nb, bg="white"); nb.add(t2, text="快速启动 FTS5")
        tk.Label(t2, text="秒搜文件 — FTS5全文索引", font=("Microsoft YaHei", 11, "bold"), bg="white").pack(pady=10)
        sf = tk.Frame(t2, bg="white"); sf.pack(fill=tk.X, padx=15, pady=5)
        self.search_var = tk.StringVar(); self.search_var.trace("w", lambda *a: self._search())
        tk.Entry(sf, textvariable=self.search_var, font=("Microsoft YaHei", 12), relief="solid", borderwidth=1, width=40).pack(side=tk.LEFT, ipady=4, padx=(0,5))
        tk.Button(sf, text="索引目录", font=("Microsoft YaHei", 9), bg="#2980b9", fg="white", relief="flat", padx=10, pady=4, command=self._index).pack(side=tk.LEFT)
        self.search_result = tk.Listbox(t2, font=("Microsoft YaHei", 10), relief="flat", borderwidth=1, selectbackground="#16a085")
        self.search_result.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5,10))
        self.search_result.bind("<Double-Button-1>", lambda e: self._open_file())
        # Tab3: 一键迁移
        t3 = tk.Frame(nb, bg="white"); nb.add(t3, text="一键迁移")
        tk.Label(t3, text="按规则批量迁移文件", font=("Microsoft YaHei", 11, "bold"), bg="white").pack(pady=10)
        df = tk.Frame(t3, bg="white"); df.pack(fill=tk.X, padx=15, pady=5)
        tk.Label(df, text="源:", font=("Microsoft YaHei", 9), bg="white").pack(side=tk.LEFT)
        self.src_var = tk.StringVar(); tk.Entry(df, textvariable=self.src_var, font=("Microsoft YaHei", 10), width=30).pack(side=tk.LEFT, ipady=2, padx=3)
        tk.Button(df, text="浏览", font=("Microsoft YaHei", 9), command=lambda: self.src_var.set(filedialog.askdirectory() or "")).pack(side=tk.LEFT, padx=3)
        tk.Label(df, text="  目标:", font=("Microsoft YaHei", 9), bg="white").pack(side=tk.LEFT, padx=(10,0))
        self.dst_var = tk.StringVar(); tk.Entry(df, textvariable=self.dst_var, font=("Microsoft YaHei", 10), width=30).pack(side=tk.LEFT, ipady=2, padx=3)
        tk.Button(df, text="浏览", font=("Microsoft YaHei", 9), command=lambda: self.dst_var.set(filedialog.askdirectory() or "")).pack(side=tk.LEFT, padx=3)
        tk.Label(df, text="  扩展名:", font=("Microsoft YaHei", 9), bg="white").pack(side=tk.LEFT, padx=(10,0))
        self.ext_var = tk.StringVar(value="*.jpg *.png *.pdf"); tk.Entry(df, textvariable=self.ext_var, font=("Microsoft YaHei", 10), width=15).pack(side=tk.LEFT, ipady=2, padx=3)
        tk.Button(df, text="迁移", font=("Microsoft YaHei", 10, "bold"), bg="#e67e22", fg="white", relief="flat", padx=15, pady=5, command=lambda: threading.Thread(target=self._migrate, daemon=True).start()).pack(side=tk.LEFT, padx=15)
        self.mig_result = scrolledtext.ScrolledText(t3, font=("Microsoft YaHei", 10), relief="flat", borderwidth=1, padx=10, pady=10)
        self.mig_result.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    def _organize(self):
        d = self.dir1_var.get()
        if not d or not os.path.exists(d): return
        self.org_btn.config(state=tk.DISABLED, text="整理中..."); self.org_result.delete("1.0", tk.END)
        moved = 0
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            if os.path.isfile(fp):
                ext = os.path.splitext(f)[1].lower().lstrip(".") or "other"
                td = os.path.join(d, ext)
                try: os.makedirs(td, exist_ok=True); shutil.move(fp, os.path.join(td, f)); moved += 1; self.org_result.insert(tk.END, f"  {f} → {ext}/\n")
                except: pass
        self.org_result.insert(tk.END, f"\n整理完成! 移动了 {moved} 个文件\n"); self.org_btn.config(state=tk.NORMAL, text="开始整理")
    def _index(self):
        d = filedialog.askdirectory()
        if not d: return
        self.db.execute("DELETE FROM fts")
        for root, dirs, files in os.walk(d):
            for f in files:
                fp = os.path.join(root, f)
                self.db.execute("INSERT INTO fts VALUES (?, ?)", (fp, f))
        self.db.commit(); messagebox.showinfo("索引完成", f"已索引目录: {d}")
    def _search(self):
        q = self.search_var.get().strip(); self.search_result.delete(0, tk.END)
        if len(q) < 2: return
        for row in self.db.execute("SELECT path FROM fts WHERE fts MATCH ? LIMIT 50", (q,)):
            self.search_result.insert(tk.END, row[0])
    def _open_file(self):
        sel = self.search_result.curselection()
        if sel: os.startfile(self.search_result.get(sel[0]))
    def _migrate(self):
        src, dst, exts = self.src_var.get(), self.dst_var.get(), self.ext_var.get().split()
        if not src or not dst: return
        self.mig_result.delete("1.0", tk.END); moved = 0
        for ext in exts:
            import glob
            for fp in glob.glob(os.path.join(src, "**", ext), recursive=True):
                try:
                    rel = os.path.relpath(fp, src); td = os.path.join(dst, os.path.dirname(rel))
                    os.makedirs(td, exist_ok=True); shutil.move(fp, os.path.join(td, os.path.basename(fp)))
                    moved += 1; self.mig_result.insert(tk.END, f"  {rel}\n")
                except: pass
            self.mig_result.insert(tk.END, f"\n迁移完成! {moved} 个文件\n")
    def run(self): self.root.mainloop()
if __name__ == "__main__": FileOrganizerApp().run()
App = FileOrganizerApp