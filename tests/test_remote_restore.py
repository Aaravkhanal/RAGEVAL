import base64
import pytest
from scripts.restore_remote_artifacts import restore


def test_restore_round_trip_and_path_traversal(tmp_path):
    data=b'{"answer":"test"}\n'
    restore({'files':{'metrics/predictions.jsonl':base64.b64encode(data).decode()}},tmp_path/'restored')
    assert (tmp_path/'restored/metrics/predictions.jsonl').read_bytes()==data
    with pytest.raises(ValueError):
        restore({'files':{'../escape':'eA=='}},tmp_path/'unsafe')
    assert not (tmp_path/'unsafe').exists()
