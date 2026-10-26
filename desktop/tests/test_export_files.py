import os
from pathlib import Path
import pytest
from anato12_studio.export_files import publish_outputs
from anato12_studio.video import Runner, Cancelled


def files(tmp_path, existing):
    pairs = []
    for ext in ['mp4', 'srt']:
        staged, target = tmp_path/f'staged.{ext}', tmp_path/f'output.{ext}'
        staged.write_bytes(b'new '+ext.encode())
        if existing:
            target.write_bytes(b'old '+ext.encode())
        pairs.append((staged, target))
    return pairs


@pytest.mark.parametrize('existing', [True, False])
@pytest.mark.parametrize('failure', ['error', 'cancel'])
def test_second_publication_failure_restores_pair(tmp_path, monkeypatch, existing, failure):
    pairs = files(tmp_path, existing)
    replace = os.replace
    def fail_second(src, dst):
        if Path(src) == pairs[1][0]:
            if failure == 'cancel':
                raise Cancelled('cancelled during publication')
            raise OSError('injected disk error')
        return replace(src, dst)
    monkeypatch.setattr(os, 'replace', fail_second)
    with pytest.raises((OSError, Cancelled)):
        publish_outputs(pairs, Runner(), overwrite=existing)
    for _, target in pairs:
        if existing:
            assert target.read_bytes() == b'old '+target.suffix[1:].encode()
        else:
            assert not target.exists()
    assert not list(tmp_path.glob('.anato12-backup-*'))


def test_recovery_failure_preserves_original_backup(tmp_path, monkeypatch):
    pairs = files(tmp_path, True)
    replace = os.replace
    def fail(src, dst):
        if Path(src) == pairs[1][0] or Path(src).name.startswith('.anato12-backup-'):
            raise OSError('injected locked destination')
        return replace(src, dst)
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(RuntimeError, match='automatic recovery could not finish') as error:
        publish_outputs(pairs, Runner(), overwrite=True)
    backups = list(tmp_path.glob('.anato12-backup-*'))
    assert sorted(p.read_bytes() for p in backups) == [b'old mp4', b'old srt']
    assert all(str(p) in str(error.value) for p in backups)


def test_success_replaces_both_and_removes_backups(tmp_path):
    pairs = files(tmp_path, True)
    assert publish_outputs(pairs, Runner(), overwrite=True) == []
    for staged, target in pairs:
        assert target.read_bytes() == b'new '+target.suffix[1:].encode()
        assert not staged.exists()
    assert not list(tmp_path.glob('.anato12-backup-*'))


def test_unapproved_overwrite_preserves_existing_files(tmp_path):
    pairs = files(tmp_path, True)
    with pytest.raises(FileExistsError):
        publish_outputs(pairs, Runner())
    assert pairs[0][1].read_bytes() == b'old mp4'
    assert pairs[1][1].read_bytes() == b'old srt'


def test_cancel_after_both_installed_restores_originals(tmp_path, monkeypatch):
    pairs = files(tmp_path, True)
    runner = Runner()
    replace = os.replace
    def cancel_after_last(src, dst):
        result = replace(src, dst)
        if Path(src) == pairs[-1][0]:
            runner.cancel()
        return result
    monkeypatch.setattr(os, 'replace', cancel_after_last)
    with pytest.raises(Cancelled):
        publish_outputs(pairs, runner, overwrite=True)
    assert pairs[0][1].read_bytes() == b'old mp4'
    assert pairs[1][1].read_bytes() == b'old srt'


def test_backup_cleanup_failure_keeps_new_pair_and_reports_old_files(tmp_path, monkeypatch):
    pairs = files(tmp_path, True)
    unlink = Path.unlink
    def locked_backup(path, *args, **kwargs):
        if path.name.startswith('.anato12-backup-'):
            raise PermissionError('injected locked backup')
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'unlink', locked_backup)
    retained = publish_outputs(pairs, Runner(), overwrite=True)
    assert len(retained) == 2 and all(p.exists() for p in retained)
    assert pairs[0][1].read_bytes() == b'new mp4'
    assert pairs[1][1].read_bytes() == b'new srt'
