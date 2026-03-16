from pathlib import Path

from PyQt6.QtCore import QSettings

from user_info import (
    ensure_user_info,
    is_user_info_complete,
    load_user_info,
    save_user_info,
)

from RoiEditor.tests._helpers import fail


def _make_settings(tmp_path: Path) -> QSettings:
    settings_path = tmp_path / "user_info.ini"
    return QSettings(str(settings_path), QSettings.Format.IniFormat)


def test_user_info_roundtrip(tmp_path):
    try:
        settings = _make_settings(tmp_path)
        user_info = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "organization": "Analytical Engine Lab",
        }

        save_user_info(user_info, settings)
        loaded = load_user_info(settings)

        assert loaded == user_info
        assert is_user_info_complete(loaded)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")


def test_ensure_user_info_uses_dialog_result(monkeypatch, tmp_path, qapp):
    try:
        settings = _make_settings(tmp_path)
        expected = {
            "first_name": "Grace",
            "last_name": "Hopper",
            "organization": "US Navy",
        }

        class FakeDialog:
            def __init__(self, parent=None):
                self.parent = parent

            def exec(self):
                return 1

            def get_values(self):
                return dict(expected)

        monkeypatch.setattr("user_info.UserInfoDialog", FakeDialog)

        actual, ok = ensure_user_info(parent=None, settings=settings)

        assert ok is True
        assert actual == expected
        assert load_user_info(settings) == expected
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
