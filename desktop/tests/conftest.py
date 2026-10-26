import shutil
import subprocess
import pytest


@pytest.fixture(scope="session")
def binaries():
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("FFmpeg and FFprobe are required for media integration tests")
    return ffmpeg, ffprobe


@pytest.fixture(scope="session")
def recording(tmp_path_factory, binaries):
    path = tmp_path_factory.mktemp("recordings") / "player's recording [test].mp4"
    subprocess.run([binaries[0], "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc2=size=320x180:rate=30:duration=4", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)
    return path

