# Anato12 Studio — start here

Anato12 Studio edits recordings **on your own computer**. There is no 32 MB upload
limit, paid API, subscription, or account requirement. Keep your original recording:
the app exports a new MP4.

This is a first working version, supplied as a Python desktop project with Windows
launchers. It is not a prebuilt or signed Windows installer.

## 1. Put the app in a folder

If you downloaded a ZIP, right-click it and choose **Extract All**. Do not run the
app from inside the ZIP. Put the extracted folder somewhere simple, such as
`Documents\Anato12 Studio`. It must contain `SETUP.bat`, `START_ANATO12.bat`,
and the `anato12_studio` folder.

## 2. Install Python once

Download **64-bit Python 3.12 or 3.13 for Windows** from
<https://www.python.org/downloads/windows/>.

Run the installer. On its first screen, check **Add python.exe to PATH**, then
choose **Install Now**. Close the installer when finished.

## 3. Double-click SETUP.bat

The setup window installs the free desktop components in a private `.venv` folder.
This first install needs an internet connection and can download several hundred
megabytes. It does not upload your recordings. Leave the window open until it says
setup has finished.

If prompted to install **FFmpeg**, press **Y**. Windows Package Manager downloads
the Gyan FFmpeg build. Accept any normal Windows installation prompts.

### FFmpeg: if the automatic step cannot run

Open **Windows Terminal** or **PowerShell**, paste this, and press Enter:

```powershell
winget install --id Gyan.FFmpeg --exact
```

After installation, close and reopen Anato12 Studio. It checks both `ffmpeg.exe`
and `ffprobe.exe`, including the standard WinGet links folder.

For a portable download, use a Windows build linked from
<https://ffmpeg.org/download.html>, extract it, and find the `bin` folder containing
**both** executables. In the app, choose **Settings → Choose FFmpeg folder** and
select that folder. You can also place them in `tools\ffmpeg\bin` beside the app.

## 4. Open the app

Double-click **START_ANATO12.bat**.

The small console window belongs to the launcher. Keep it open while editing. If
an error appears, leave the message visible so you can read it. Running
`SETUP.bat` again safely refreshes the dependencies.

## 5. Make your first edit — no AI needed

1. Click **Import recordings**, or drag an MP4 into the window.
2. Click **Play / pause** and move the seek slider to find a moment.
3. Click **Mark in** at the beginning and **Mark out** at the end. You can also
   type a time such as `35.5` or `00:01:12.500`.
4. Choose **YouTube · 16:9** for a regular video, or **Shorts · 9:16**.
5. Choose framing:
   - **Fit whole video** keeps the full recording visible, with bars when needed.
   - **Fill frame** crops edges. Move the framing sliders to keep the action or
     facecam visible.
   - **Zoom** adds a fixed punch-in to that clip. Watch the preview before exporting.
6. Give the range a name and click **Add clip**. Add more ranges if you like.
   Reorder clips with the up/down buttons. Only checked clips export.
7. To change an existing clip, select it, adjust its range/framing, and click
   **Update selected**.
8. Click **Export MP4**, choose a folder such as `Videos`, and choose a **new filename**.

The app joins checked clips into one MP4 in list order. If the clip list is empty,
it exports the current range. Export produces H.264 video at 30 fps with AAC audio:
1920×1080 for YouTube or 1080×1920 for Shorts. You can cancel an export.

Use **File → Save project** to save your clip list. Projects end in `.anato12.json`.
They contain edit decisions and captions, not copies of your recordings. Add your
chosen range to the clip list before saving. If a recording moves, use
**Relink selected** to locate the same recording again.

## 6. Optional: transcription

You can keep using import, preview, trim, and export without installing this.

1. Close the app and double-click **INSTALL_SPEECH.bat**.
2. Reopen the app, select a recording, and open **Dialogue & captions**.
3. Pick an English speech model:
   - **tiny.en**: smallest download, about 110 MB; fastest, less accurate.
   - **base.en**: about 200 MB; a sensible starting choice.
   - **small.en**: about 640 MB; slower and generally more accurate.
4. Click **Transcribe locally**. The first use downloads the chosen free model
   from the official sherpa-onnx GitHub release. Inference then runs on your CPU.
5. Review the timestamped lines. Double-click a dialogue cell to correct its text.
   Select a line and click **Use selected line** to frame a clip with some context.

Models are kept in `%LOCALAPPDATA%\Anato12Studio\models`. Once cached, they can
run offline. **Settings → Choose speech-model folder** lets you keep them on
another drive. Leave room for the model download and temporary audio.

No speech recognition is perfect. Quiet, overlapping voices and game audio can
produce mistakes; timestamps are approximate. Review and correct captions before
publishing. This version transcribes English; it does not identify speakers.

### Use captions you already have

Click **Import SRT** and select a UTF-8 `.srt` whose timestamps match the original
recording. An exported clip's SRT has already been retimed to the clip; do not import
that as though it were the full recording's transcript.

Check **Show & burn captions** to put captions onto the video. Check **Also save
.srt captions** for a separate subtitle file that YouTube can import. Exports retime
captions across the selected clips. Burned captions require FFmpeg with libass;
the app reports it clearly if the installed build lacks it.

## 7. Optional: find possible moments

After transcription or SRT import, click **Suggest moments**. The app looks for
text cues such as laughter, “no way,” or “what just happened,” and keeps some setup
around each hit. These are suggestions to review, not a guarantee that a clip is
funny. It does not yet understand gameplay, music, facial expressions, or speaker
intent. Preview a suggestion, then add the ones you want to your clip list.

## Common problems

- **Python opens Microsoft Store:** install Python from python.org and enable
  its PATH option; rerun setup.
- **The preview stays black:** pause/play once, seek to another point, and try a
  standard H.264 MP4. Windows needs working graphics/media drivers; some unusual
  source codecs may export with FFmpeg but not preview in Qt.
- **No preview sound:** check the app volume, Windows Volume Mixer, and output device.
- **Export looks cropped:** choose Fit whole video or adjust Fill frame's sliders.
- **Export looks blurry:** cropping or zooming cannot restore detail absent in the source.
- **Speech model download fails:** check internet access and free space. Downloads use
  verified HTTPS; do not disable certificate verification. If a manually copied
  model folder is incomplete, move it aside and retry.
- **My video moved:** select it and use Relink selected. Choose the same recording,
  not a different edit of it.
- **Export is slow:** CPU encoding/transcription takes time, particularly with Shorts,
  captions, or long recordings. Start with a 10-second range.
- **A file already exists:** choose a new name or confirm replacing the export.
  The app refuses to overwrite imported recordings.

## Optional: make an EXE on Windows

Once the source app works, double-click **BUILD_WINDOWS.bat**. If you want speech
inside the EXE, run `INSTALL_SPEECH.bat` first.

The result is `dist\Anato12Studio\Anato12Studio.exe`. Keep the **whole**
`Anato12Studio` folder together. The EXE does not need a separate Python installation,
but still needs FFmpeg. Speech models are downloaded separately and are not bundled.
To add speech to an EXE built without it, rebuild after installing speech support.

An EXE must be built and tested on Windows; the provided build script and Windows
CI workflow do that on a Windows machine. No prebuilt Windows EXE is included here.
