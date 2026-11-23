# Design Document: eSim Automated Tool Manager

## 1. Introduction

eSim is an open-source electronic design automation environment that relies on external applications and libraries. A user may need to install and maintain tools such as Ngspice and KiCad. Performing these tasks manually can be time-consuming and may lead to missing dependencies or inconsistent versions.

This project proposes a lightweight Python command-line **Automated Tool Manager**. The prototype delegates software installation and upgrades to trusted operating-system package managers instead of downloading and executing arbitrary installer scripts.

## 2. Objectives and scope

### Objectives

1. Detect the operating system and available package manager.
2. Identify whether supported eSim tools are installed.
3. Display detected executable version information.
4. Install or upgrade a selected tool after user confirmation.
5. Check basic dependencies and record actions in a log.

### Requirements addressed

- Requirement 1: Tool Installation Management.
- Requirement 2: Update and Upgrade System.
- Requirement 4: Dependency Checker.
- Requirement 5: User Interface and action logging.

The prototype focuses on Ngspice and KiCad. The tool registry is designed so additional tools can be added without rewriting the CLI.

## 3. High-level architecture

```text
                 +--------------------------+
                 |      User Interface      |
                 | CLI + Tkinter Dashboard  |
                 | list, status, install... |
                 +------------+-------------+
                              |
                              v
                 +--------------------------+
                 |       CLI Controller     |
                 | argument parsing, flow  |
                 +------------+-------------+
                              |
              +---------------+----------------+
              |               |                |
              v               v                v
      +---------------+ +-------------+ +--------------+
      | Tool Registry | | Environment | | Logging      |
      | Ngspice,      | | OS + package| | Action/error |
      | KiCad         | | manager     | | history      |
      +-------+-------+ +------+------+ +--------------+
              |                |
              +--------+-------+
                       |
                       v
              +-------------------+
              | Package Manager   |
              | apt / winget /    |
              | Homebrew          |
              +---------+---------+
                        |
                        v
              +-------------------+
              | External Tools    |
              | Ngspice / KiCad   |
              +-------------------+
```

## 4. Module breakdown

The proof of concept is kept in `src/tool_manager.py` for easy execution. Its functions are separated by responsibility:

| Component/function | Responsibility |
|---|---|
| `src/dashboard.py` | Tkinter desktop dashboard; launches manager actions, displays output, and asks before install/upgrade |
| `TOOLS` registry | Stores tool name, executable, version command, and package IDs by OS |
| `platform_key()` | Normalizes Linux, Windows, and macOS identifiers |
| `package_manager()` | Detects `apt-get`, `winget`, or `brew` |
| `installed_version()` | Finds the executable and runs its version command |
| `dependency_check()` | Checks package-manager and executable availability |
| `install_command()` | Builds the platform-specific install command |
| `update_command()` | Builds the platform-specific upgrade command |
| `perform()` | Confirms and executes installation/upgrade |
| `show_status()` / `show_updates()` | Displays tool status and package-manager update information |
| logging setup | Writes operations and errors to `tool_manager.log` |

## 5. Graphical dashboard

The optional desktop dashboard is implemented in `src/dashboard.py` using Python Tkinter. It contains an operating-system summary, a tool selector, status and dependency-check controls, install/update actions, update checking, and an activity output panel. It delegates operations to the existing CLI process so the command-line and graphical interfaces share the same manager logic and log file. System-changing actions require a confirmation dialog.

Launch it with `python src/dashboard.py` or double-click `run_dashboard.bat` on Windows.

## 6. Workflow

### 5.1 Tool status and version check

1. User runs `status` or `check <tool>`.
2. The manager reads the OS and checks the executable in `PATH`.
3. If present, it executes the tool's version command.
4. The result is displayed. Missing executables are reported clearly.

### 5.2 Installation

1. User selects a tool.
2. The manager detects the package manager.
3. It maps the tool to the package identifier for the current OS.
4. It displays the command and asks for confirmation.
5. The package manager performs the installation.
6. The result is displayed and logged.

### 5.3 Update check and upgrade

1. `updates` asks the detected package manager for its available-upgrade listing.
2. `update <tool>` constructs a package-specific upgrade command.
3. The user confirms before the command is executed.
4. The package manager handles package resolution and upgrade.

## 7. Platform mapping

| OS | Manager | Install example | Upgrade example |
|---|---|---|---|
| Debian/Ubuntu | apt-get | `sudo apt-get install -y ngspice` | `sudo apt-get install --only-upgrade -y ngspice` |
| Windows | winget | `winget install --id ngspice --exact` | `winget upgrade --id ngspice --exact` |
| macOS | Homebrew | `brew install ngspice` | `brew upgrade ngspice` |

The exact package identifier may change by package source or operating-system release. The registry is the single place to adjust mappings.

## 8. Error handling and safety

- Commands are passed as argument lists to `subprocess`; no shell interpolation is used.
- Installation and upgrade require an interactive confirmation by default.
- The package manager is responsible for signature checks, dependency resolution, and package installation.
- Unsupported operating systems and missing package managers produce an error message.
- Process timeouts and execution errors are caught and logged.
- The `--yes` option is available for automation but should be used deliberately.

## 9. Logging

The manager writes timestamped INFO, WARNING, and ERROR entries to `tool_manager.log` in the project root. The `logs` command displays the log. This supports basic auditing and troubleshooting.

## 10. Testing strategy

The included unit tests verify operating-system mapping, tool lookup, and command construction. These tests do not install or upgrade software. Manual integration testing should be performed on a disposable or non-critical machine for each supported OS.

## 11. Future enhancements

1. Add a graphical interface using Tkinter or PySide.
2. Store user preferences and custom tool paths in a configuration file.
3. Verify minimum and recommended tool versions against an eSim compatibility matrix.
4. Add checksum/signature verification for manually downloaded packages if package-manager support is unavailable.
5. Integrate with eSim to validate configured executable paths.
6. Add a per-tool update comparison view and structured JSON logs.
7. Add support for additional EDA tools and libraries.

## 12. Conclusion

The prototype provides a modular starting point for automating external-tool management in eSim. It demonstrates package-manager-based installation and upgrade, version detection, dependency checks, a CLI, and action logging while requiring user confirmation before system changes.
