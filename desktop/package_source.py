"""Create a source/launcher ZIP without recordings, caches, weights or environments."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
FILES = [
    "FIRST_READ_ME.txt", "START_HERE.html", "START_HERE.md", "README.md", "THIRD_PARTY.md",
    "VALIDATION.md", "LICENSE", "pyproject.toml", "uv.lock", "requirements.txt",
    "requirements-speech.txt", "SETUP.bat", "START_ANATO12.bat", "INSTALL_SPEECH.bat",
    "BUILD_WINDOWS.bat", "Anato12Studio.spec", "launch.py", ".gitignore", "package_source.py",
    "AGENTS.md", "PROJECT_AUDIT.md", "LESSONS_LEARNED.md", "BUG_LOG.md",
    "TEST_RESULTS.md", "DEVELOPMENT_ROADMAP.md",
    "CHECK_LOCAL_AI.bat",
    "LEARNING_SYSTEM.md", "PERSONAL_STYLE.md",
]


def main():
    destination = ROOT / "dist" / "Anato12-Studio-Source.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(f"Missing distribution file: {name}")
            archive.write(source, f"Anato12-Studio/{name}")
        for folder in ("anato12_studio", "tests"):
            for source in sorted((ROOT / folder).rglob("*.py")):
                if "__pycache__" not in source.parts:
                    archive.write(source, "Anato12-Studio/" + source.relative_to(ROOT).as_posix())
        standalone = ROOT / ".github" / "workflows" / "windows.yml"
        repository = ROOT.parent / ".github" / "workflows" / "desktop-windows.yml"
        if standalone.is_file():
            workflow = standalone.read_text(encoding="utf-8")
        else:
            workflow = repository.read_text(encoding="utf-8")
            workflow = workflow.replace('["desktop/**", ".github/workflows/desktop-windows.yml"]', '["**"]')
            workflow = workflow.replace("working-directory: desktop", "working-directory: .")
            workflow = workflow.replace("desktop/requirements*.txt", "requirements*.txt")
            workflow = workflow.replace("desktop/dist/Anato12Studio/", "dist/Anato12Studio/")
        archive.writestr("Anato12-Studio/.github/workflows/windows.yml", workflow)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert not any(x in name.split("/") for name in archive.namelist()
                       for x in (".venv", ".verification", "__pycache__", ".git"))
        print(f"{destination}\n{len(archive.namelist())} source/setup files · {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
