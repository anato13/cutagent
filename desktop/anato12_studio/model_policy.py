"""Conservative routing among downloaded local Ollama models.

Routing is a preference, not a claim that a larger model is funnier. The selected
model is always displayed and saved with a job; no cloud or implicit pull occurs.
"""
import shutil
import subprocess
import sys
import re
import os
from pathlib import Path

from .video import NO_WINDOW


MODES = ("Automatic", "Fast", "Balanced", "Maximum intelligence")
OFFERED = {
    "qwen3:8b": {"purpose": "Fast chat and everyday editing help", "approx_gb": 5.3},
    "qwen3:14b": {"purpose": "Complex reasoning and exchange review; may use system RAM", "approx_gb": 9.5},
    "gemma3:12b": {"purpose": "Single-frame image understanding; video analysis is not yet connected", "approx_gb": 8.5},
}


def choose_model(installed, mode="Automatic", task="chat", question="", selected=None):
    """Return (installed model, explanation); never pull or silently choose cloud."""
    if mode not in MODES or task not in {"chat", "analysis", "visual"}:
        raise ValueError("Choose a valid AI mode and task.")
    available = [name for name in installed if isinstance(name, str) and
                 not name.casefold().endswith(("-cloud", ":cloud"))]
    if selected:
        if selected not in available:
            raise ValueError("The manually selected local model is not installed. Reconnect to Ollama.")
        return selected, "Using your manually selected local model."
    complex_chat = len(question) > 220 or any(term in question.casefold() for term in
        ("compare", "analyz", "reason", "explain why", "story", "humor", "clip"))
    if task == "visual":
        order = ["gemma3:12b"]
    elif mode == "Maximum intelligence" or (mode == "Automatic" and
                                               (task == "analysis" or complex_chat)):
        order = ["qwen3:14b", "qwen3:8b", "qwen2.5:7b", "qwen2.5:3b"]
    elif mode == "Fast":
        order = ["qwen2.5:3b", "qwen3:8b", "qwen2.5:7b", "qwen3:14b"]
    else:
        order = ["qwen3:8b", "qwen2.5:7b", "qwen3:14b", "qwen2.5:3b"]
    name = next((item for item in order if item in available), None)
    if name is None and task != "visual" and available:
        name = available[0]  # Preserve compatibility with other installed local models.
    if not name:
        raise ValueError("No compatible local model is installed for this task. Connect to Ollama or install one.")
    note = f"{mode} chose {name} for {task}."
    if name != order[0]:
        note += f" Preferred {order[0]} is not installed; using a downloaded model instead."
    if name == "qwen3:14b":
        note += " This model can exceed 8 GB VRAM; Ollama may use system RAM and run more slowly."
    return name, note


def model_speed(metrics):
    count, duration = metrics.get("eval_count"), metrics.get("eval_duration")
    if type(count) is int and type(duration) is int and count >= 0 and duration > 0:
        return round(count * 1_000_000_000 / duration, 1)
    return None


def context_tokens(name):
    # The transcript payload is bounded to 6 KB; 4096 tokens leaves room for
    # schema and output while reducing KV-cache pressure on 8 GB GPUs.
    return 4096 if name in {"qwen3:14b", "gemma3:12b"} else 8192


def resource_snapshot():
    """Measured host availability; GPU fields are absent when nvidia-smi is unavailable."""
    model_dir = Path(os.environ.get("OLLAMA_MODELS") or Path.home() / ".ollama" / "models")
    existing = next((p for p in (model_dir, *model_dir.parents) if p.exists()), Path.home())
    result = {"disk_free_gb": round(shutil.disk_usage(existing).free / 1e9, 1),
              "model_storage": str(model_dir)}
    try:
        if sys.platform == "win32":
            import ctypes
            class Memory(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                            ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                            ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
                            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                            ("available_extended", ctypes.c_ulonglong)]
            memory = Memory()
            memory.length = ctypes.sizeof(memory)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                result["ram_available_gb"] = round(memory.available / 1e9, 1)
        else:
            with open("/proc/meminfo", encoding="ascii") as info:
                values = {a.strip(): int(b.strip().split()[0]) for a, b in
                          (line.split(":", 1) for line in info if ":" in line)}
            result["ram_available_gb"] = round(values["MemAvailable"] * 1024 / 1e9, 1)
    except (OSError, ValueError, KeyError):
        pass
    executable = shutil.which("nvidia-smi")
    if not executable and sys.platform == "win32":
        candidate = (Path(os.environ.get("ProgramW6432", "C:/Program Files")) /
                     "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe")
        if candidate.is_file():
            executable = str(candidate)
    if executable:
        try:
            check = subprocess.run([executable, "--query-gpu=memory.used,memory.free", "--format=csv,noheader,nounits"],
                                   capture_output=True, text=True, timeout=3)
            if check.returncode == 0:
                used, free = [int(part.strip()) for part in check.stdout.splitlines()[0].split(",")[:2]]
                result.update(gpu_vram_used_mb=used, gpu_vram_free_mb=free)
        except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
            pass
    return result


def installation_check(name, resources):
    if name not in OFFERED:
        raise ValueError("Choose a verified model tag from the installation list.")
    required = OFFERED[name]["approx_gb"]
    free = resources.get("disk_free_gb")
    if isinstance(free, (int, float)) and free < required + 2:
        raise ValueError(f"Only {free:.1f} GB is free. {name} needs about {required:.1f} GB "
                         "plus 2 GB working space. Free storage before downloading.")
    note = (f"About {required:.1f} GB download/storage. This is an estimate, not a hardware benchmark. "
            "Keep qwen2.5:7b installed. Progress appears in Ollama's pull output.")
    ram = resources.get("ram_available_gb")
    if isinstance(ram, (int, float)) and ram < required + 2:
        note += " Available system RAM is low for this model; it may fail or run slowly."
    vram = resources.get("gpu_vram_free_mb")
    if isinstance(vram, (int, float)) and vram < required * 1024:
        note += " It will not fit wholly in current free VRAM; Ollama may offload to system RAM."
    return note


def install_model(name, runner, progress):
    """Explicit user-requested Ollama pull with cancellable progress; never deletes models."""
    check = installation_check(name, resource_snapshot())
    executable = shutil.which("ollama")
    if not executable:
        raise ValueError("Ollama's command-line tool was not found. Open Ollama and run "
                         f"'ollama pull {name}' in Command Prompt instead. {check}")
    runner.check()
    proc = subprocess.Popen([executable, "pull", name], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                            bufsize=0, creationflags=NO_WINDOW,
                            env={**os.environ, "OLLAMA_HOST": "127.0.0.1:11434"})
    runner.process = proc
    latest = "Starting model download"
    fragment = ""
    try:
        assert proc.stdout is not None
        while True:
            runner.check()
            char = proc.stdout.read(1)
            if not char:
                break
            if char in "\r\n":
                line, fragment = fragment.strip(), ""
                if not line:
                    continue
                latest = line[-160:]
                match = re.search(r"\b(\d{1,3})%", line)
                progress(min(.99, int(match.group(1)) / 100) if match else 0, latest)
            else:
                fragment = (fragment + char)[-300:]
        code = proc.wait()
        runner.check()
        if code:
            raise RuntimeError(f"Ollama could not install {name}: {latest}. "
                               f"Try 'ollama pull {name}' in Command Prompt for details.")
        progress(1, f"{name} downloaded; verifying with local Ollama")
        return name
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        if proc.stdout:
            proc.stdout.close()
        runner.process = None
