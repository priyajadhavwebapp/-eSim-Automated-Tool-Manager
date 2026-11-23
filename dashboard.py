#!/usr/bin/env python3
"""Tkinter dashboard for the eSim Automated Tool Manager."""
from __future__ import annotations

import platform
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "tool_manager.py"


class ToolManagerDashboard(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("eSim Automated Tool Manager")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.configure(bg="#f3f6fb")
        self.selected_tool = tk.StringVar(value="ngspice")
        self.status_text = tk.StringVar(value="Ready. Select an action to begin.")
        self._build_ui()
        self.refresh_status()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#172b4d", foreground="white")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), background="#172b4d", foreground="#dce6f5")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"), background="white", foreground="#172b4d")
        style.configure("Action.TButton", font=("Segoe UI", 10), padding=8)

        header = tk.Frame(self, bg="#172b4d", height=105)
        header.pack(fill="x")
        header.pack_propagate(False)
        ttk.Label(header, text="eSim Automated Tool Manager", style="Title.TLabel").pack(anchor="w", padx=24, pady=(18, 2))
        ttk.Label(header, text="Dashboard  |  Installation • Versions • Updates • Logs", style="Sub.TLabel").pack(anchor="w", padx=25)

        body = tk.Frame(self, bg="#f3f6fb", padx=20, pady=18)
        body.pack(fill="both", expand=True)

        info = ttk.Frame(body, style="Card.TFrame", padding=14)
        info.pack(fill="x", pady=(0, 14))
        ttk.Label(info, text=f"Operating system: {platform.system()} {platform.release()}", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(info, text="Supported tools: Ngspice and KiCad   |   Python standard library GUI (Tkinter)", background="white").pack(anchor="w", pady=(5, 0))

        controls = ttk.Frame(body, style="Card.TFrame", padding=14)
        controls.pack(fill="x", pady=(0, 14))
        ttk.Label(controls, text="Tool management", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", columnspan=4, pady=(0, 10))
        ttk.Label(controls, text="Select tool:", background="white").grid(row=1, column=0, sticky="w", padx=(0, 8))
        tool_box = ttk.Combobox(controls, textvariable=self.selected_tool, values=("ngspice", "kicad"), state="readonly", width=18)
        tool_box.grid(row=1, column=1, sticky="w", padx=(0, 18))
        ttk.Button(controls, text="Refresh status", style="Action.TButton", command=self.refresh_status).grid(row=1, column=2, padx=4)
        ttk.Button(controls, text="Check selected tool", style="Action.TButton", command=self.check_tool).grid(row=1, column=3, padx=4)

        actions = ttk.Frame(body, style="Card.TFrame", padding=14)
        actions.pack(fill="x", pady=(0, 14))
        ttk.Label(actions, text="Actions", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(actions, style="Card.TFrame")
        row.pack(fill="x")
        for label, command in (("Install selected", self.install_tool), ("Update selected", self.update_tool), ("Check updates", self.check_updates), ("View logs", self.view_logs)):
            ttk.Button(row, text=label, style="Action.TButton", command=command).pack(side="left", padx=(0, 8))

        output_frame = ttk.Frame(body, style="Card.TFrame", padding=12)
        output_frame.pack(fill="both", expand=True)
        ttk.Label(output_frame, text="Activity / Output", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.output = tk.Text(output_frame, wrap="word", height=12, font=("Consolas", 10), bg="#fbfcfe", fg="#243247", relief="solid", borderwidth=1)
        self.output.pack(fill="both", expand=True)
        self.output.insert("end", "Welcome! Use Refresh status to inspect Ngspice and KiCad.\n")
        self.output.configure(state="disabled")

        footer = tk.Frame(body, bg="#f3f6fb")
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(footer, textvariable=self.status_text, background="#f3f6fb", foreground="#52627a").pack(side="left")
        ttk.Label(footer, text="Actions requiring system changes ask for confirmation", background="#f3f6fb", foreground="#52627a").pack(side="right")

    def _append(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _run_cli(self, *args: str) -> None:
        self.status_text.set("Working…")
        self._append("> python src/tool_manager.py " + " ".join(args))

        def worker() -> None:
            try:
                result = subprocess.run(
                    [sys.executable, str(CLI), *args], cwd=str(ROOT),
                    capture_output=True, text=True, timeout=1900, check=False
                )
                output = (result.stdout or "") + (result.stderr or "")
                if not output.strip():
                    output = f"Command finished with exit code {result.returncode}."
                self.after(0, lambda: self._finish(output, result.returncode))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._finish("The command timed out.", 1))
            except OSError as exc:
                self.after(0, lambda: self._finish(f"Could not start the manager: {exc}", 1))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, output: str, code: int) -> None:
        self._append(output)
        self.status_text.set("Completed successfully." if code == 0 else f"Finished with an issue (exit code {code}). See output above.")

    def refresh_status(self) -> None:
        self._run_cli("status")

    def check_tool(self) -> None:
        self._run_cli("check", self.selected_tool.get())

    def check_updates(self) -> None:
        self._run_cli("updates")

    def view_logs(self) -> None:
        self._run_cli("logs")

    def install_tool(self) -> None:
        tool = self.selected_tool.get()
        if messagebox.askyesno("Confirm installation", f"Install {tool}? This will use the detected system package manager and may require administrator permission."):
            self._run_cli("install", tool, "--yes")

    def update_tool(self) -> None:
        tool = self.selected_tool.get()
        if messagebox.askyesno("Confirm update", f"Update {tool}? This will modify installed software and may require administrator permission."):
            self._run_cli("update", tool, "--yes")


if __name__ == "__main__":
    ToolManagerDashboard().mainloop()
