# Anato12 Studio — start here

Anato12 Studio edits recordings **on your own computer**. There is no 32 MB upload
limit, paid API, subscription, or account requirement. Keep your original recording:
the app exports a new MP4.

This is version 0.4 alpha, supplied as a Python desktop project with Windows
launchers. It is not a prebuilt or signed Windows installer.

## New: Auto Edit and the learning library

Finish the setup steps below first. For **Auto Edit**:

1. Import your raw recording and select it in **Recordings**.
2. In **AI Clip Finder**, connect to your local Ollama installation and select a
   downloaded model. Install the optional speech tools below if you need automatic
   transcription. An existing transcript or imported SRT also works.
3. Open **Auto Edit**, choose maximum lengths, clip count and optional captions,
   then click **Auto Edit selected recording** and choose an output folder.
4. Studio selects and exports without asking you to mark clips. The finished
   folder contains a YouTube MP4, Shorts MP4s, editable projects and a check report.
   If no usable complete exchanges are found, it explains why and creates no bundle.

This is an experimental editor. Its file checks do not establish that the choices
are funny or tell a good story. Main clips stay in recording order. No video is
uploaded to YouTube. First-run operation checks and local inference can take time.
Cancel is available; **Jobs & clip feedback → Resume** retries using analysis
caches, with rendering starting again. See LEARNING_SYSTEM.md for recovery limits.

In alpha 2, **AI Clip Finder** shows the quoted setup, payoff and reaction behind
new suggestions. Model explanations are labeled unverified. Auto Edit skips
suggestions missing those references or asking for more context. If an older
unreviewed suggestion has no exchange map, run analysis again. Your approvals,
rejections and manually changed clips stay intact. New automatic clip labels
quote your transcript rather than using the model's headline. Transcription errors
can still appear in those quotes.

In alpha 3, Auto Edit reserves room for one complete Short if its first choices
are all too long. This can replace a longer selected exchange when the clip count
or main-video limit is tight. It keeps whole dialogue and records skipped choices
in the output report. If nothing fits, it stops with an explanation.

The built-in initial [humor profile](PERSONAL_STYLE.md) describes the kinds of
conversation you enjoy. Model taste scores are subjective 1–5 suggestions, not
proof a clip is funny. Save corrections and confirmed own-video notes in the
Learning library to refine future suggestions.

In AI Clip Finder, **Connect local model** now chooses Local Ollama for Analyze.
The result message tells you whether the app used Ollama or basic context cues,
how many timestamped lines and model sections it checked, and why zero results
may need a more specific search. A connection by itself only lists models.
Use **Ask AI** for a simple conversation with the selected local model. Chat is
session-only and does not send your recording or transcript automatically.

For **Learning library**, import a tutorial, authorized creator video or your own
finished video; select its type and click **Index selected recording**. Search
its dialogue, inspect sampled frames and possible scene changes, preview examples,
and save corrections. A saved YouTube URL is only a bookmark, not an analyzed video.
Drag the divider above the tabs upward or scroll inside the tab to see all controls.

To guide future edits, confirm an own-video example, write your preference and
check **Use this own-video note in Auto Edit**. You can revoke this later. For
original/finished comparison, index both, choose the finished source in the main
dropdown and the original in **Original for comparison**, then click Compare.
This finds unique matching dialogue; it does not yet identify every retained joke.
See [LEARNING_SYSTEM.md](LEARNING_SYSTEM.md) for exactly what is implemented.

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

When replacing an MP4 and its SRT, Studio prepares both files before replacing
either. If a normal save error or cancellation interrupts replacement, it attempts
to restore the previous pair. If a locked file prevents recovery, the error names
the saved originals. Keep those .anato12-backup-... files until you recover them.
A computer crash or forced shutdown can leave backups/partial outputs; automatic
recovery after those interruptions is not implemented.

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

## 7. Find and review possible clips

1. Select a recording, then open **AI Clip Finder**.
   Scroll that panel or drag the divider above the tabs upward for more space.
2. Start with **Context cues · limited**, then click **Analyze recording**. Existing
   edited/imported dialogue is used; if none exists, optional local transcription
   runs first. For recordings without speech tools, import a matching SRT first.
3. Select a result to see its source frame, exact source evidence and timestamps.
   Cue analysis combines context or repeated phrases. It does not prove something
   is funny and can miss good moments. An empty result is valid.
4. Click **Preview** to play that range. Adjust the start/end seconds and title,
   then click **Save adjustment**. Click **Approve** or **Reject** to retain your
   decision. Reanalysis preserves saved decisions and adjustments.
5. **Export MP4** in this tab exports only that highlighted candidate, using the
   current framing/caption options. **Add to main video** or **Add to Shorts**
   appends it to the existing editor and changes the project's output ratio.
   Use separate saved projects for separate main/Shorts edits.
6. Enter optional feedback. Personalization is **off by default**; check the box
   only when you want that approved/rejected category to affect future ordering.
   This is a simple, reversible preference adjustment, not AI retraining.

### Use feedback notes to guide your local model

There are two separate, unchecked options when saving feedback:

- **Use this feedback to personalize future ranks** adjusts category ordering.
- **Share this note with my local model** lets a downloaded local model consider
  the note during future analysis/search. Approve or reject the highlight first.

For example, you can write “keep the setup and reaction” or “this category is
usually not my style.” Shared notes are preferences, not proof that something
happened in the recording. The model still needs valid transcript evidence.

Open **Jobs & clip feedback**, select a saved entry, edit its note/options and
click **Save feedback changes**. The **Personalization preview** shows the actual
category preferences and note text included in future local-model requests.
At most eight recent shared notes are included, with 240 characters from each.
Older saved notes remain visible but may fall outside that recent-note window.
The complete saved note remains available in the editor/data export.
Shared preferences apply across recordings in this app-data profile. The Decision
column records the review when feedback was saved. To change that recorded vote,
delete the entry, review the clip again, then save new feedback.

Unchecking note sharing keeps the note private in the app. Deleting feedback
removes it from future personalization. Changes to shared/ranking feedback clear
cached model responses; speech transcripts remain cached. Private-note edits do
not force reanalysis. Existing clips, drafts and exported videos are not rewritten.
The independent CHECK_LOCAL_AI evaluator uses no app feedback, so its reports
remain a baseline model check. Actual improvement in humor selection is unverified.

Upgrading to this version adds a separate sharing flag to the local database
(schema 2). **All existing notes stay unshared.** Keep using this version or newer
with that data folder; older releases refuse a newer database. For a rollback
copy, close Studio and back up its app-data folder before upgrading.

**Search** matches transcript words in cue mode. It cannot infer which exchange
is “weirdest” or verify a story claim. A configured local model is required for
semantic search. **All saved highlights** clears the current search-result filter.
The older **Potential moments** tab remains available with its original text cues.

### Create separate YouTube and Shorts drafts

After approving your favorite highlights for one recording, click
**Create YouTube + Shorts drafts from approved highlights…** in AI Clip Finder.
The button uses every approved highlight for that recording, including ones
outside the current search or decision filter.

Choose a maximum Short length (default 60 seconds, adjustable from 1–180) and
portrait framing. **Keep whole frame** adds bars; **Fill portrait** crops the
center and needs careful preview if your facecam sits near an edge.
Choose optional captions and check **Also render MP4s now** if you want finished
videos as well as editable projects. Otherwise creation is much quicker.

Choose a destination folder. Studio creates a uniquely named **Anato12-drafts-...**
folder containing:

- **YouTube.anato12.json** — approved ranges in recording order. Overlapping
  ranges merge so the main edit does not repeat the same footage.
- **Short-001.anato12.json**, etc. — one complete approved range per independent
  portrait project. Exact duplicate frame ranges are included once.
- **draft-manifest.json** — source, included highlights, outputs and reasons for
  skipped Shorts. A range over your chosen limit stays in the main draft and is
  skipped for Shorts; it is not automatically cut in half.
- MP4s and optional SRTs if you chose to render immediately.

Click **Open folder** when creation finishes. Open each project using
**File → Open project**, save your current edit when prompted, and review framing,
captions and clip boundaries. The open edit is unchanged while drafts are created.
Projects reference the original recording, so keep it at its current location.
Each project stores editable captions; burned captions are permanent only in
finished MP4s. Caption options in a project-only bundle apply when you export later.

Cancellation or a processing error removes that attempt's temporary bundle.
A forced app/computer shutdown can leave a hidden .anato12-drafts-... temporary
folder; it is not a completed bundle. Draft batches currently restart from scratch.
Rendering needs disk space for every output and FFmpeg's temporary intermediates.
The completion message reports any skipped Shorts; inspect the manifest before
assuming every approved range became a Short.

This builds drafts from your decisions. It does not choose an opening hook,
understand a story arc or automatically track faces. The older **Add to main video**
and **Add to Shorts** buttons still append to the currently open project and
switch its ratio; use the new draft button for independent edits.

### Optional: connect a downloaded local model

This step is separate from speech recognition. The app does not install or start
Ollama for you, and you can keep editing without it.

1. Install Ollama for Windows from <https://ollama.com/download/windows>.
2. Open Windows Terminal. For example, `ollama pull qwen2.5:3b` downloads a small
   local conversational model (several GB of disk space may be needed). This is
   an example to try, not a model-quality or GPU-performance guarantee.
3. Start Ollama. Leave the app URL at `http://127.0.0.1:11434`. Click
   **Connect local model** and choose an installed model name.
4. Choose **Local Ollama · contextual** and analyze or search. Transcript windows
   go to that local server. Use downloaded models; known cloud-backed Ollama
   models and non-loopback endpoints are rejected. There is no cloud fallback.
5. Review every result. Genuine-dialogue tests with Qwen2.5 3B/7B found invented
   explanations despite valid source references. Qwen3 8B was more conservative
   and missed exchanges. None is a validated automatic humor detector.
   A specific search can help locate an exchange, but its explanation still needs review.

Ollama controls its own hardware use. The editor's FFmpeg and speech paths
currently use CPU; RTX acceleration is not verified. If connection fails, check
that Ollama is running and a local model has finished downloading, or use cue mode.
Cancel now closes an active local request and stops waiting for generation. A slow
CPU inference request may run for up to five minutes before timing out; metadata
requests have a one-minute limit. Completed analysis sections remain cached.

Dense dialogue now uses smaller overlapping sections automatically. Each section
keeps complete transcript lines with their original IDs and timestamps.
If one line is too large, Studio names its ID and source time so you can shorten
it or split it at real timestamps in an SRT and reimport. Long search text or
shared notes also consume the input budget; shortening them may resolve the error.
Studio does not silently cut a dialogue line or invent replacement times.

The adapter requests 8,192 context tokens with up to 1,200 output tokens, and
limits the combined system/transcript/search/feedback content to 6,000 UTF-8 bytes.
For models advertising thinking support, Studio disables that mode to leave the
output budget for clip suggestions. This is separate from Codex reasoning settings.
This is a conservative size limit, not an exact tokenizer measurement or a
guarantee that every model/template fits. GPU memory use remains unmeasured.
Up to four earlier callback links are included when space allows. The model-check
report lists each section's input size and omitted callback-link count, so omitted
earlier conversational context is visible during evaluation. Dense transcripts can require
more requests; section-planning speed does not predict model-inference speed.

### Check your installed model and save evidence

After transcribing one recording, save its Studio project. Start Ollama, then
double-click **CHECK_LOCAL_AI.bat**. Paste the saved .anato12.json path and choose
an installed model number. Use a project with one transcribed recording.

The check creates a new **Anato12-model-check-...** folder beside the project.
Its **model-evaluation.json** records model identity, actual processing times,
candidate timestamps and source quotations. Each section also retains the original
proposals, including rejected ones, and any token counts/timings reported by Ollama.
Those measurements describe model processing, not how funny a clip is. Duration
fields inside server_metrics use nanoseconds; wall_seconds uses seconds.
Missing server measurements stay absent rather than being estimated.
An outcome of invalid_evidence means the model proposed clips that failed the
source checks; no_proposals means it returned an empty list. Neither is a humor rating.
Review the clips against your video;
human_decision and human_notes fields are blank for your assessment. The tool
does not calculate a humor score. Reports contain dialogue; keep them private.

If a request fails or you press Ctrl+C, completed evidence remains in that folder.
The check does not modify the project or the application's review database.
Use the app's Clip Finder for resumable jobs; this evaluation starts fresh each time.

Advanced command, from the app folder:

```powershell
.\.venv\Scripts\python.exe -m anato12_studio.evaluate_model --project "My edit.anato12.json" --model "qwen2.5:3b" --output "Model review"
```

Add --media-id followed by the recording ID from the project JSON for projects
with several transcribed recordings, or --query followed by quoted search text.
The output folder must be new. Analysis checks installed model digests before
reusing cached answers. If a model changes during processing or has no reported
digest, reconnect and choose a stable downloaded model.

### Jobs, storage and your data

Open **Jobs & clip feedback** to inspect processing state, resume an interrupted
job, view/delete feedback, clear processing caches or export local application
data as JSON. Resume is manual. Completed transcript chunks/model windows are
reused; a partial transcription currently prepares temporary audio again.
The complete prepared WAV is on disk, with small chunks read into RAM.
For two hours, the temporary WAV alone needs about 220 MiB free space.

The app stores its database under `%LOCALAPPDATA%\Anato12Studio` on Windows.
Models are separate. `ANATO12_DATA_DIR` can select another writable app-data
folder. Saved project files and finished exports stay where you chose to save them.

**Clear processing caches** keeps highlights, feedback and source recordings.
**Delete current recording's app data** removes its cached dialogue, highlights,
feedback, job history and thumbnails. Original recordings, saved project files and
finished exports stay. Save your project before closing to retain the editor timeline.
The JSON data export contains local paths, evidence and feedback; keep it private.
Close the app before backing up the complete app-data folder.

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
