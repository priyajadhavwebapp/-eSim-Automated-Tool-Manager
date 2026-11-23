# eSim Automated Tool Manager

A Python command-line prototype for managing external tools used by eSim, including **Ngspice** and **KiCad**.

## Implemented requirements

- **Tool installation management:** detects the operating system and installs tools through its package manager.
- **Update and upgrade system:** checks package-manager upgrade information and can upgrade a selected tool.
- **Dependency checker:** checks package-manager availability and whether the selected tool is installed.
- **User interface and logging:** CLI commands, readable status output, and an action log.

> Safety: installation and upgrade commands require explicit confirmation. The program uses the operating system's package manager; it does not download arbitrary installers or run unverified scripts.

## Supported platforms

| Platform | Package manager | Example packages |
|---|---|---|
| Ubuntu/Debian Linux | `apt` | `ngspice`, `kicad` |
| Windows | `winget` | `ngspice`, `KiCad.KiCad` |
| macOS | `brew` | `ngspice`, `kicad` |

Package identifiers and availability can vary by OS release and package-manager source. If a package is unavailable, use the package manager's search command and adjust `src/tool_manager.py`.

## Requirements

- Python 3.9 or newer
- A supported package manager (`apt`, `winget`, or `brew`)
- Administrator privileges may be required for installation

No third-party Python packages are required.

## Run the graphical dashboard (VS Code / Windows)

From the project root, open the VS Code terminal and run:

```powershell
python src/dashboard.py
```

Alternatively, double-click `run_dashboard.bat`. The dashboard provides buttons for status refresh, dependency checks, installation, upgrades, update checks, and logs. Installation and upgrade actions display a confirmation dialog first.

The dashboard uses Python's built-in Tkinter library; no extra pip package is required. If Tkinter is missing from your Python installation, install a Python distribution that includes Tcl/Tk.

## Run the command-line interface

From the project root:

```bash
python src/tool_manager.py list
python src/tool_manager.py status
python src/tool_manager.py check ngspice
python src/tool_manager.py check kicad
```

Install a tool (the program asks for confirmation):

```bash
python src/tool_manager.py install ngspice
python src/tool_manager.py install kicad
```

Check for updates and upgrade:

```bash
python src/tool_manager.py updates
python src/tool_manager.py update ngspice
```

View the action log:

```bash
python src/tool_manager.py logs
```

Show help:

```bash
python src/tool_manager.py --help
```

### Platform notes

- **Ubuntu/Debian:** package metadata may need refreshing. Run `sudo apt update` if `apt` reports stale package information. The manager invokes `apt` and may request your password in the terminal.
- **Windows:** install and configure Windows Package Manager (`winget`) first. The current prototype maps Ngspice to a Winget package ID that may not exist in every source; check `winget search ngspice` before using the Install button. The dashboard will show the package-manager error rather than silently claiming success. Run with suitable permissions if required.
- **macOS:** install Homebrew first. The manager invokes `brew`.

## Example workflow for a demo

1. Run `python src/tool_manager.py list`.
2. Run `python src/tool_manager.py status` to show detected tools and versions.
3. Run `python src/tool_manager.py check ngspice` to demonstrate dependency checking.
4. Run `python src/tool_manager.py install ngspice` if it is not installed. Confirm when prompted.
5. Run `python src/tool_manager.py updates` and demonstrate the update-check output.
6. Run `python src/tool_manager.py logs` to show the audit log.

You can run the status/check commands without installing anything.

## Project structure

```text
esim_automated_tool_manager/
├── README.md
├── run_dashboard.bat
├── requirements.txt
├── .gitignore
├── src/
│   ├── tool_manager.py
│   └── dashboard.py
├── docs/
│   └── DESIGN_DOCUMENT.md
└── tests/
    └── test_tool_manager.py
```

## Testing

Run the unit tests:

```bash
python -m unittest discover -s tests -v
```

The tests do not install software or modify the system.

## Limitations

- This is a proof of concept, not an official eSim component.
- Package manager output and package identifiers can change over time.
- Update availability is inferred from the package manager's upgrade listing; some managers may not expose a reliable per-package result.
- The prototype reports detected executable versions. Exact version command output differs across tool releases.
- The manager does not yet edit eSim's own configuration files. It provides a safe starting point for adding eSim-specific path configuration.

## GitHub submission checklist

1. Create a new GitHub repository and set it to **Private**.
2. Extract this ZIP and upload the project files.
3. Add collaborator `Eyantra698Sumanto` (GitHub account).
4. Verify the collaborator invitation/access.
5. Copy the private repository URL.
6. Email the repository URL and design document to `contact-esim@fossee.in` with the subject:

   `eSim Semester Long Internship - Autumn 2026 Submission Task 5`

Do not put passwords, tokens, or personal credentials in the repository.
