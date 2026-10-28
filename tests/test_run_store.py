"""Run directories refuse to overwrite."""

import os

import pytest

from rageval.benchmark.run_store import create_run_dir


def test_create_run_dir_unique(tmp_path):
    path = create_run_dir(str(tmp_path), run_id="run_a")
    assert os.path.isdir(path)
    with pytest.raises(FileExistsError):
        create_run_dir(str(tmp_path), run_id="run_a")
