"""Run a real local model against saved project dialogue; write reviewable evidence."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from .finder import callbacks, deduplicate, model_proposals, rows_for
from .model_context import bounded_windows, response_schema, MAX_INPUT_BYTES, CONTEXT_TOKENS, OUTPUT_TOKENS, PROMPT_VERSION
from .local_model import LocalModel
from .model import Project
from .video import Runner


def evaluate(project_path, output, client, media_id=None, query="", progress=print):
    project = Project.load(Path(project_path))
    choices = [m for m in project.media.values() if m.transcript and (not media_id or m.id == media_id)]
    if len(choices) != 1:
        raise ValueError("Choose a project with one transcribed recording, or pass --media-id for one recording.")
    media = choices[0]
    rows = rows_for(media.transcript)
    runner = Runner()
    chunks = list(bounded_windows(rows, callbacks(rows), query, {}, runner))
    # Refuse to overwrite any existing file/folder, including user projects.
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {"version": 1, "started_utc": datetime.now(timezone.utc).isoformat(),
              "status": "running", "model": client.model, "endpoint": client.base,
              "recording": media.name, "duration_seconds": media.duration,
              "transcript_lines": len(rows), "query": query, "windows": [],
              "candidates": [], "humor_quality": "NOT_EVALUATED",
              "note": "Real model proposals require human review. No accuracy or humor score is inferred.",
              "gpu_measurement": "NOT_MEASURED",
              "input_budget_bytes": MAX_INPUT_BYTES, "requested_context_tokens": CONTEXT_TOKENS,
              "prompt_version": PROMPT_VERSION,
              "maximum_output_tokens": OUTPUT_TOKENS,
              "input_token_count": "See per-window server_metrics when supplied by the server",
              "server_metrics_units": "Token counts are integers; duration fields are nanoseconds."}
    candidates = []
    started = time.monotonic()
    destination = output / "model-evaluation.json"
    def save():
        report["wall_seconds"] = round(time.monotonic()-started, 3)
        temporary = output / "report.tmp"
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(destination)
    save()
    try:
        identity = client.identity(runner)
        report["model_identity"] = identity
        for i, chunk in enumerate(chunks):
            window, context = chunk.rows, chunk.callbacks
            if client.identity(runner) != identity:
                raise ValueError("Model changed during this evaluation; run again with stable installed weights.")
            progress(f"Evaluating context {i+1}/{len(chunks)}")
            tick = time.monotonic()
            raw = client.analyze(window, context, query, {}, runner)
            elapsed = time.monotonic()-tick
            if client.identity(runner) != identity:
                raise ValueError("Model changed while generating a response.")
            valid = model_proposals(raw, window, context, media.duration)
            candidates.extend(valid)
            report["windows"].append({"first_segment_id": window[0]["id"],
                "last_segment_id": window[-1]["id"], "wall_seconds": round(elapsed, 3),
                "content_bytes": chunk.content_bytes, "omitted_callback_links": chunk.omitted_callback_links,
                "response_schema_bytes": len(json.dumps(response_schema(window, context),
                    ensure_ascii=False, separators=(',', ':')).encode('utf-8')),
                "server_metrics": dict(getattr(client, "last_metrics", {})),
                "raw_proposals": raw,
                "outcome": "invalid_evidence" if raw and not valid else "candidates" if valid else "no_proposals",
                "returned_proposals": len(raw), "valid_evidence_proposals": len(valid),
                "rejected_proposals": len(raw)-len(valid)})
            report["windows_with_invalid_evidence"] = sum(
                w["outcome"] == "invalid_evidence" for w in report["windows"])
            report["candidates"] = [{**asdict(p), "human_decision": None,
                "human_checks": {name: None for name in ('setup_complete', 'payoff_complete',
                    'reaction_complete', 'explanation_supported', 'worth_keeping')},
                "human_notes": "", "excerpt": "\n".join(r["text"] for r in rows
                    if r["end"] > p.start and r["start"] < p.end)}
                for p in deduplicate(candidates)]
            save()
        report["status"] = "completed"
    except KeyboardInterrupt:
        report["status"] = "cancelled"
        report["error"] = "Interrupted by user; completed window evidence is retained."
        raise
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        save()
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--media-id")
    parser.add_argument("--query", default="")
    parser.add_argument("--url", default="http://127.0.0.1:11434")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.interactive:
            print("Save a Studio project after transcribing or importing captions. Start Ollama first.")
            args.project = Path(input("Project file (.anato12.json): ").strip().strip('"'))
            client = LocalModel(args.url)
            installed = client.models()
            if not installed:
                raise ValueError("No downloaded local models found. Download a model in Ollama first.")
            for i, name in enumerate(installed, 1):
                print(f"{i}. {name}")
            selection = int(input("Model number: "))
            if not 1 <= selection <= len(installed):
                raise ValueError("Select one of the listed model numbers.")
            args.model = installed[selection-1]
            args.output = args.project.parent / ("Anato12-model-check-" +
                datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        if not args.project or not args.output or not args.model:
            parser.error("--project, --output and --model are required unless --interactive is used.")
        destination = evaluate(args.project, args.output, LocalModel(args.url, args.model),
                               args.media_id, args.query)
        print(f"Report saved: {destination}\nReview candidates against the recording; humor quality is not scored.")
        return 0
    except KeyboardInterrupt:
        print("Cancelled. Completed evidence remains in the report folder.")
        return 130
    except Exception as error:
        print(f"Evaluation did not finish: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
