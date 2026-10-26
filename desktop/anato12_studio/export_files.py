"""Recoverable publication of an MP4 and its optional caption sidecar.

This handles ordinary errors/cancellation, not process termination or power loss.
"""
import os
from pathlib import Path
import uuid


def publish_outputs(pairs, runner, overwrite=False):
    backups, installed = {}, []
    try:
        for _, destination in pairs:
            runner.check()
            if destination.exists() or destination.is_symlink():
                if not overwrite:
                    raise FileExistsError("An output appeared while exporting. Choose a new filename.")
                if destination.is_dir():
                    raise ValueError("An export destination is a folder. Choose a filename.")
                backup = destination.with_name(f".anato12-backup-{uuid.uuid4().hex}-{destination.name}")
                os.replace(destination, backup)
                backups[destination] = backup
        for staged, destination in pairs:
            runner.check()
            os.replace(staged, destination)
            installed.append(destination)
        runner.check()
    except BaseException as error:
        failures = []
        # Restore even destinations whose original was moved but whose new file
        # was never installed. Never delete a backup that could not be restored.
        for destination in reversed(list(dict.fromkeys([*backups, *installed]))):
            try:
                if destination in backups:
                    os.replace(backups[destination], destination)
                elif destination in installed:
                    destination.unlink(missing_ok=True)
            except OSError:
                recovery = backups.get(destination)
                failures.append(f"{destination} (original: {recovery})" if recovery else str(destination))
        if failures:
            raise RuntimeError("Export failed and automatic recovery could not finish. "
                               "Keep these files and recover the saved originals before retrying:\n" +
                               "\n".join(failures)) from error
        raise
    retained = []
    for backup in backups.values():
        try:
            backup.unlink()
        except OSError:
            retained.append(Path(backup))
    return retained
