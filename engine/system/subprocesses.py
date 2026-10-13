import sys
from pathlib import Path

def engine_cmd(subcommand: str, *args, module: str | None = None) -> list[str]:
    """Returns the command list to run an internal engine task,
    whether in frozen PyInstaller mode or dev python mode."""
    str_args = [str(a) for a in args]
    if getattr(sys, 'frozen', False):
        return [sys.executable, subcommand, *str_args]
    mod = module or f"engine.{subcommand.replace('-', '_')}"
    return [sys.executable, '-X', 'utf8', '-m', mod, *str_args]
