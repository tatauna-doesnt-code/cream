"""Run the current project/template UI integration checks."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/check_template_workflow.py"), run_name="__main__")
