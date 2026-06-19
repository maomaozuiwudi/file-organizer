import tkinter as tk
from tkinter import messagebox
import sys, os

# 直接导入main，跳过加密loader
try:
    from main import App
    App().run()
except Exception as e:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Error", f"Launch failed: {e}\n\nPlease contact support.")
    root.destroy()