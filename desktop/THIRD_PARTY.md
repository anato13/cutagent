# Open-source components

- Python: PSF license.
- PySide6 / Qt: LGPLv3/GPLv3/commercial options. This project uses the open-source
  distribution; retain the licenses/notices distributed with Qt when packaging.
- FFmpeg: LGPL/GPL depending on the installed build and enabled codecs. FFmpeg
  executables are installed separately, not included in this source distribution.
- sherpa-onnx: Apache 2.0. Optional speech inference package.
- OpenAI Whisper: MIT; converted models are distributed by the official
  sherpa-onnx project on GitHub.
- NumPy: BSD license.
- PyInstaller: GPL with its bootloader exception; a build-time tool.

Speech model weights and third-party Windows executables are not included in the
source package. Packaging tools preserve their own collected notices; distributors
should also retain the relevant dependency licenses alongside a built app.
