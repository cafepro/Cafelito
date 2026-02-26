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
            with patch("mouse_mover.pyautogui.position", return_value=(0, 0)):
                mouse_mover.run_mover(60, stop_event)
        mock_move.assert_not_called()

    def test_nudges_after_idle_interval(self):
        stop_event = threading.Event()
        nudged = threading.Event()

        def fake_move():
            nudged.set()
            stop_event.set()

        # Mouse stays at same position the whole time → should nudge
        with patch("mouse_mover.move_mouse", side_effect=fake_move):
            with patch("mouse_mover.pyautogui.position", return_value=(100, 100)):
                with patch("mouse_mover.time.monotonic", side_effect=[0, 0, 61, 61, 62]):
                    mouse_mover.run_mover(60, stop_event)

        assert nudged.is_set()

    def test_does_not_nudge_while_mouse_is_moving(self):
        stop_event = threading.Event()
        call_count = 0

        positions = [(0, 0), (10, 10), (20, 20)]

        def moving_position():
            nonlocal call_count
            pos = positions[min(call_count, len(positions) - 1)]
            call_count += 1
            if call_count >= 3:
                stop_event.set()
            return pos

        with patch("mouse_mover.move_mouse") as mock_move:
            with patch("mouse_mover.pyautogui.position", side_effect=moving_position):
                mouse_mover.run_mover(60, stop_event)

        mock_move.assert_not_called()


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
