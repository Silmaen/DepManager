"""
End-to-end tests for ``depmanager.api.internal.database_local.LocalDatabase``.

These tests build a real on-disk cache (via the ``make_package`` fixture),
instantiate a LocalDatabase pointing at it, then exercise query, reload, and
delete.
"""

from __future__ import annotations

from depmanager.api.internal.database_local import LocalDatabase


class TestLocalDatabaseLoading:
    def test_empty_database(self, tmp_edm_home):
        db = LocalDatabase(tmp_edm_home / "data")
        assert db.valid_shape is True
        assert db.dependencies == []

    def test_invalid_path_marks_database_invalid(self, tmp_path):
        db = LocalDatabase(tmp_path / "does_not_exist")
        assert db.valid_shape is False

    def test_file_instead_of_dir(self, tmp_path):
        f = tmp_path / "not_a_dir"
        f.write_text("hi")
        db = LocalDatabase(f)
        assert db.valid_shape is False

    def test_loads_single_package(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        assert len(db.dependencies) == 1
        assert db.dependencies[0].properties.name == "libfoo"

    def test_loads_multiple_packages(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        make_package(name="libbar", version="2.1.0")
        db = LocalDatabase(tmp_edm_home / "data")
        names = {d.properties.name for d in db.dependencies}
        assert names == {"libfoo", "libbar"}


class TestLocalDatabaseQuery:
    def test_query_by_name(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        make_package(name="libbar", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        hits = db.query({"name": "libfoo"})
        assert len(hits) == 1
        assert hits[0].properties.name == "libfoo"

    def test_query_wildcard(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        make_package(name="libfoobar", version="1.0.0")
        make_package(name="other", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        hits = db.query({"name": "libfoo*"})
        assert {d.properties.name for d in hits} == {"libfoo", "libfoobar"}

    def test_query_latest_by_name(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        make_package(name="libfoo", version="1.1.0")
        make_package(name="libfoo", version="0.9.0")
        db = LocalDatabase(tmp_edm_home / "data")
        hits = db.query({"name": "libfoo", "latest": True})
        assert len(hits) == 1
        assert hits[0].properties.version == "1.1.0"

    def test_query_no_match(self, tmp_edm_home, make_package):
        make_package(name="libfoo", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        assert db.query({"name": "nonexistent"}) == []


class TestLocalDatabaseDelete:
    def test_delete_removes_package_directory(self, tmp_edm_home, make_package):
        pkg_path = make_package(name="libfoo", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        assert pkg_path.exists()
        db.delete({"name": "libfoo"})
        assert not pkg_path.exists()

    def test_delete_only_matching(self, tmp_edm_home, make_package):
        keep = make_package(name="libbar", version="1.0.0")
        rm = make_package(name="libfoo", version="1.0.0")
        db = LocalDatabase(tmp_edm_home / "data")
        db.delete({"name": "libfoo"})
        assert keep.exists()
        assert not rm.exists()


class TestLocalDatabaseReload:
    def test_reload_picks_up_new_packages(self, tmp_edm_home, make_package):
        db = LocalDatabase(tmp_edm_home / "data")
        assert db.dependencies == []
        make_package(name="libfoo", version="1.0.0")
        db.reload()
        assert len(db.dependencies) == 1
