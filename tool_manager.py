#!/usr/bin/env python3
"""eSim Automated Tool Manager - safe package-manager based CLI prototype."""

from __future__ import annotations

import argparse
import logging
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / "tool_manager.log"


@dataclass(frozen=True)
class Tool:
    key: str
    display_name: str
    executable: str
    version_args: Sequence[str]
    packages: Dict[str, str]


TOOLS: Dict[str, Tool] = {
    "ngspice": Tool(
        key="ngspice",
        display_name="Ngspice",
        executable="ngspice",
        version_args=("-v",),
        packages={"linux": "ngspice", "windows": "ngspice", "darwin": "ngspice"},
    ),
    "kicad": Tool(
        key="kicad",
        display_name="KiCad",
        executable="kicad-cli",
        version_args=("version",),
        packages={"linux": "kicad", "windows": "KiCad.KiCad", "darwin": "kicad"},
    ),
}


def setup_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def platform_key(system: Optional[str] = None) -> str:
    system = (system or platform.system()).lower()
    if system == "linux":
        return "linux"
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "darwin"
    return "unknown"


def package_manager(system: Optional[str] = None) -> Optional[str]:
    key = platform_key(system)
    candidate = {"linux": "apt-get", "windows": "winget", "darwin": "brew"}.get(key)
    if candidate and shutil.which(candidate):
        return candidate
    return None


def get_tool(name: str) -> Tool:
    try:
        return TOOLS[name.lower()]
    except KeyError as exc:
        raise ValueError(
            f"Unknown tool '{name}'. Available tools: {', '.join(TOOLS)}"
        ) from exc


def run_command(command: Sequence[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a package-manager or version command without invoking a shell."""
    return subprocess.run(
        list(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def installed_version(tool: Tool) -> Optional[str]:
    executable = shutil.which(tool.executable)
    if not executable:
        return None
    try:
        result = run_command([executable, *tool.version_args], timeout=15)
        output = (result.stdout or "").strip()
        if result.returncode == 0 and output:
            # Keep the first useful line concise; preserve full detail in the log.
            first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
            return first_line[:160] if first_line else "Installed (version not reported)"
        return "Installed (version command unavailable)"
    except (OSError, subprocess.TimeoutExpired) as exc:
        logging.warning("Could not read version for %s: %s", tool.key, exc)
        return "Installed (version check failed)"


def is_installed(tool: Tool) -> bool:
    return shutil.which(tool.executable) is not None


def package_for(tool: Tool, system: Optional[str] = None) -> str:
    key = platform_key(system)
    if key not in tool.packages:
        raise RuntimeError(f"Unsupported operating system: {platform.system()}")
    return tool.packages[key]


def dependency_check(name: str) -> List[str]:
    tool = get_tool(name)
    problems = []
    manager = package_manager()
    if manager is None:
        problems.append("No supported package manager found (apt-get, winget, or brew).")
    if not is_installed(tool):
        problems.append(f"{tool.display_name} executable '{tool.executable}' was not found in PATH.")
    return problems


def install_command(tool: Tool, manager: str, system: Optional[str] = None) -> List[str]:
    package = package_for(tool, system)
    if manager == "apt-get":
        return ["sudo", "apt-get", "install", "-y", package]
    if manager == "winget":
        return ["winget", "install", "--id", package, "--exact", "--silent",
                "--accept-package-agreements", "--accept-source-agreements"]
    if manager == "brew":
        return ["brew", "install", package]
    raise RuntimeError(f"Unsupported package manager: {manager}")


def update_command(tool: Tool, manager: str, system: Optional[str] = None) -> List[str]:
    package = package_for(tool, system)
    if manager == "apt-get":
        return ["sudo", "apt-get", "install", "--only-upgrade", "-y", package]
    if manager == "winget":
        return ["winget", "upgrade", "--id", package, "--exact",
                "--accept-package-agreements", "--accept-source-agreements"]
    if manager == "brew":
        return ["brew", "upgrade", package]
    raise RuntimeError(f"Unsupported package manager: {manager}")


def confirm(action: str, assume_yes: bool = False) -> bool:
    if assume_yes:
        return True
    answer = input(f"{action} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def perform(name: str, action: str, assume_yes: bool = False) -> int:
    tool = get_tool(name)
    manager = package_manager()
    if not manager:
        print("ERROR: Supported package manager not found.")
        return 1

    if action == "install" and is_installed(tool):
        print(f"{tool.display_name} is already installed: {installed_version(tool)}")
        return 0
    if action == "update" and not is_installed(tool):
        print(f"{tool.display_name} is not installed. Install it first.")
        return 1

    command = install_command(tool, manager) if action == "install" else update_command(tool, manager)
    print("Command:", " ".join(command))
    if not confirm(f"Proceed to {action} {tool.display_name}?", assume_yes):
        print("Cancelled.")
        logging.info("User cancelled %s for %s", action, tool.key)
        return 0

    logging.info("Starting %s for %s: %s", action, tool.key, command)
    try:
        result = run_command(command, timeout=1800)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}")
        logging.exception("%s failed for %s", action, tool.key)
        return 1

    print(result.stdout or "(No output)")
    if result.returncode == 0:
        print(f"{action.title()} command completed.")
        logging.info("%s completed for %s", action, tool.key)
        return 0

    print(f"ERROR: package manager exited with code {result.returncode}.")
    logging.error("%s failed for %s (exit %s)", action, tool.key, result.returncode)
    return result.returncode or 1


def show_status() -> None:
    manager = package_manager()
    print(f"Operating system: {platform.system()} ({platform.release()})")
    print(f"Package manager: {manager or 'Not found'}")
    print("\nTool status:")
    for tool in TOOLS.values():
        version = installed_version(tool)
        state = version if version else "Not installed / executable not in PATH"
        print(f"  {tool.display_name:10} : {state}")


def show_updates() -> None:
    manager = package_manager()
    if not manager:
        print("No supported package manager found.")
        return
    print(f"Update check via {manager}:")
    try:
        if manager == "apt-get":
            command = ["apt", "list", "--upgradable"]
        elif manager == "winget":
            command = ["winget", "upgrade"]
        else:
            command = ["brew", "outdated"]
        result = run_command(command, timeout=120)
        print(result.stdout or "No update information returned.")
        if result.returncode != 0:
            print(f"Package manager returned exit code {result.returncode}.")
        logging.info("Update check executed: %s", command)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Update check failed: {exc}")
        logging.exception("Update check failed")


def show_logs() -> None:
    if not LOG_FILE.exists():
        print("No actions logged yet.")
        return
    print(LOG_FILE.read_text(encoding="utf-8", errors="replace"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage eSim external tools (Ngspice and KiCad)."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List tools supported by this prototype.")
    sub.add_parser("status", help="Show installed tools and detected versions.")
    sub.add_parser("updates", help="Ask the package manager for available updates.")
    sub.add_parser("logs", help="Display the action log.")

    for action in ("check", "install", "update"):
        item = sub.add_parser(action, help=f"{action.title()} or inspect one tool.")
        item.add_argument("tool", choices=sorted(TOOLS))
        if action in ("install", "update"):
            item.add_argument("-y", "--yes", action="store_true",
                              help="Skip confirmation (use only when intended).")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        for tool in TOOLS.values():
            print(f"{tool.key}: {tool.display_name} ({tool.executable})")
        return 0
    if args.command == "status":
        show_status()
        return 0
    if args.command == "updates":
        show_updates()
        return 0
    if args.command == "logs":
        show_logs()
        return 0
    if args.command == "check":
        problems = dependency_check(args.tool)
        if not problems:
            tool = get_tool(args.tool)
            print(f"OK: {tool.display_name} detected. Version: {installed_version(tool)}")
            return 0
        print("Dependency check:")
        for problem in problems:
            print(f" - {problem}")
        return 1
    if args.command in ("install", "update"):
        return perform(args.tool, args.command, getattr(args, "yes", False))
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
