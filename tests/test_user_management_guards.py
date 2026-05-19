"""Guard rails in user management persistence functions."""

import app.db as db


class _Result:
    def __init__(self, row=None, scalar_value=None):
        self._row = row
        self._scalar_value = scalar_value

    def fetchone(self):
        return self._row

    def scalar(self):
        return self._scalar_value


class _Conn:
    def __init__(self, role_row=("admin",), admin_count=1):
        self.role_row = role_row
        self.admin_count = admin_count
        self.statements = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, statement, *_args, **_kwargs):
        sql = str(statement)
        self.statements.append(sql)
        if "SELECT role FROM users" in sql:
            return _Result(row=self.role_row)
        if "SELECT COUNT(*) FROM users WHERE role = 'admin'" in sql:
            return _Result(scalar_value=self.admin_count)
        return _Result()

    def commit(self):
        self.committed = True


class _Engine:
    def __init__(self, conn):
        self.conn = conn

    def connect(self):
        return self.conn


def test_delete_user_blocks_self_delete():
    ok, err = db.delete_user(10, actor_id=10)
    assert ok is False
    assert err == "Cannot delete your own account"


def test_delete_user_blocks_last_admin(monkeypatch):
    conn = _Conn(role_row=("admin",), admin_count=1)
    monkeypatch.setattr(db, "engine", _Engine(conn))

    ok, err = db.delete_user(2, actor_id=1)

    assert ok is False
    assert err == "Cannot delete the last administrator"
    assert not any("DELETE FROM users" in stmt for stmt in conn.statements)


def test_delete_user_allows_non_last_admin(monkeypatch):
    conn = _Conn(role_row=("admin",), admin_count=2)
    monkeypatch.setattr(db, "engine", _Engine(conn))

    ok, err = db.delete_user(2, actor_id=1)

    assert ok is True
    assert err is None
    assert any("DELETE FROM users" in stmt for stmt in conn.statements)
    assert conn.committed is True


def test_update_role_blocks_demoting_last_admin(monkeypatch):
    conn = _Conn(role_row=("admin",), admin_count=1)
    monkeypatch.setattr(db, "engine", _Engine(conn))

    ok, err = db.update_user_role(1, "user")

    assert ok is False
    assert err == "Cannot demote the last administrator"
    assert not any("UPDATE users" in stmt for stmt in conn.statements)
