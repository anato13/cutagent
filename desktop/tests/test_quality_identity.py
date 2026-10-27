"""Installed code fingerprints must work without loose Python source files."""
from types import SimpleNamespace

import pytest

from anato12_studio.quality import engine_identity


def test_archive_loader_code_is_stable_and_changes_invalidate_capabilities(tmp_path, monkeypatch):
    engine = tmp_path / 'engine'
    engine.write_bytes(b'fixture executable metadata')
    absent_source = tmp_path / 'archive-only.py'
    code = [compile('VALUE = 1', str(absent_source), 'exec')]
    requests = []
    def get_code(name):
        requests.append(name)
        return code[0]
    spec = SimpleNamespace(loader=SimpleNamespace(get_code=get_code))
    monkeypatch.setattr('anato12_studio.quality.find_spec', lambda name: spec)
    first = engine_identity(engine, engine)
    assert engine_identity(engine, engine) == first
    assert not absent_source.exists()
    assert 'anato12_studio.drafts' in requests and 'anato12_studio.export_files' in requests
    code[0] = compile('VALUE = 2', str(absent_source), 'exec')
    assert engine_identity(engine, engine) != first


@pytest.mark.parametrize('spec', [None, SimpleNamespace(loader=None),
                                SimpleNamespace(loader=SimpleNamespace(get_code=lambda name: None))])
def test_missing_code_identity_refuses_to_reuse_capability_passes(tmp_path, monkeypatch, spec):
    engine = tmp_path / 'engine'
    engine.write_bytes(b'fixture executable metadata')
    monkeypatch.setattr('anato12_studio.quality.find_spec', lambda name: spec)
    with pytest.raises(ValueError, match='Reinstall Studio'):
        engine_identity(engine, engine)
