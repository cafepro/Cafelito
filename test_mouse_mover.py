import threading
from unittest.mock import MagicMock, call, patch

import pytest
from PIL import Image

import mouse_mover


class TestParseInterval:
    def test_valid_integer(self):
        assert mouse_mover._parse_interval("60") == 60

    def test_valid_small_value(self):
        assert mouse_mover._parse_interval("1") == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            mouse_mover._parse_interval("0")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            mouse_mover._parse_interval("-10")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            mouse_mover._parse_interval("not-a-number")

    def test_float_raises(self):
        with pytest.raises(ValueError):
            mouse_mover._parse_interval("3.5")


class TestBuildIconImage:
    def test_returns_pil_image(self):
        img = mouse_mover.build_icon_image()
        assert isinstance(img, Image.Image)

    def test_correct_size(self):
        img = mouse_mover.build_icon_image()
        assert img.size == (64, 64)

    def test_rgba_mode(self):
        img = mouse_mover.build_icon_image()
        assert img.mode == "RGBA"


class TestMoveMouse:
    def test_calls_move_rel_twice(self):
        with patch("mouse_mover.pyautogui") as mock_gui:
            mouse_mover.move_mouse()
            assert mock_gui.moveRel.call_count == 2

    def test_nudge_and_return(self):
        with patch("mouse_mover.pyautogui") as mock_gui:
            mouse_mover.move_mouse()
            calls = mock_gui.moveRel.call_args_list
            assert calls[0] == call(mouse_mover.MOVE_RADIUS, 0, duration=0.2)
            assert calls[1] == call(-mouse_mover.MOVE_RADIUS, 0, duration=0.2)


class TestRunMover:
    def test_does_not_move_when_already_stopped(self):
        stop_event = threading.Event()
        stop_event.set()
        with patch("mouse_mover.move_mouse") as mock_move:
            mouse_mover.run_mover(60, stop_event)
        mock_move.assert_not_called()

    def test_moves_once_then_stops(self):
        stop_event = threading.Event()

        def fake_move():
            stop_event.set()

        with patch("mouse_mover.move_mouse", side_effect=fake_move):
            mouse_mover.run_mover(0, stop_event)

        assert stop_event.is_set()


class TestMain:
    def test_exits_cleanly_on_cancel(self):
        with patch("mouse_mover.show_dialog", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                mouse_mover.main()
        assert exc_info.value.code == 0

    def test_starts_tray_with_chosen_interval(self):
        with patch("mouse_mover.show_dialog", return_value=30):
            with patch("mouse_mover.start_tray") as mock_tray:
                with patch("mouse_mover.pyautogui"):
                    mouse_mover.main()
        mock_tray.assert_called_once_with(30)

    def test_failsafe_is_disabled(self):
        with patch("mouse_mover.show_dialog", return_value=None):
            with patch("mouse_mover.pyautogui") as mock_gui:
                with pytest.raises(SystemExit):
                    mouse_mover.main()
        assert mock_gui.FAILSAFE is False
