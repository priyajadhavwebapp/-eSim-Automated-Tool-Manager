import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import tool_manager as tm


class ToolManagerTests(unittest.TestCase):
    def test_platform_mapping(self):
        self.assertEqual(tm.platform_key("Linux"), "linux")
        self.assertEqual(tm.platform_key("Windows"), "windows")
        self.assertEqual(tm.platform_key("Darwin"), "darwin")
        self.assertEqual(tm.platform_key("Plan9"), "unknown")

    def test_tool_registry(self):
        self.assertEqual(tm.get_tool("ngspice").executable, "ngspice")
        self.assertEqual(tm.get_tool("KICAD").key, "kicad")
        with self.assertRaises(ValueError):
            tm.get_tool("not-a-tool")

    def test_linux_install_command(self):
        tool = tm.get_tool("ngspice")
        self.assertEqual(
            tm.install_command(tool, "apt-get", "Linux"),
            ["sudo", "apt-get", "install", "-y", "ngspice"],
        )

    def test_windows_upgrade_command(self):
        tool = tm.get_tool("kicad")
        command = tm.update_command(tool, "winget", "Windows")
        self.assertIn("upgrade", command)
        self.assertIn("KiCad.KiCad", command)

    def test_macos_package_mapping(self):
        self.assertEqual(tm.package_for(tm.get_tool("ngspice"), "Darwin"), "ngspice")


if __name__ == "__main__":
    unittest.main()
