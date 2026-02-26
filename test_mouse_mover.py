import sys
from unittest.mock import call, patch, MagicMock

import pytest

import mouse_mover


class TestParseInterval:
    def test_default_when_no_args_no_env(self):
        with patch.object(sys, "argv", ["mouse_mover.py"]):
            with patch.dict("os.environ", {}, clear=True):
                assert mouse_mover.parse_interval() == mouse_mover.DEFAULT_INTERVAL

    def test_cli_arg_long(self):
        with patch.object(sys, "argv", ["mouse_mover.py", "--interval", "45"]):
            assert mouse_mover.parse_interval() == 45

    def test_cli_arg_short(self):
        with patch.object(sys, "argv", ["mouse_mover.py", "-i", "90"]):
            assert mouse_mover.parse_interval() == 90

    def test_env_var(self):
        with patch.object(sys, "argv", ["mouse_mover.py"]):
            with patch.dict("os.environ", {"MOUSE_MOVER_INTERVAL": "120"}):
                assert mouse_mover.parse_interval() == 120

    def test_cli_takes_priority_over_env(self):
        with patch.object(sys, "argv", ["mouse_mover.py", "--interval", "30"]):
            with patch.dict("os.environ", {"MOUSE_MOVER_INTERVAL": "999"}):
                assert mouse_mover.parse_interval() == 30

    def test_invalid_env_var_falls_back_to_default(self, capsys):
        with patch.object(sys, "argv", ["mouse_mover.py"]):
            with patch.dict("os.environ", {"MOUSE_MOVER_INTERVAL": "not-a-number"}):
                result = mouse_mover.parse_interval()
        assert result == mouse_mover.DEFAULT_INTERVAL
        assert "not a valid number" in capsys.readouterr().out


class TestMoveMouse:
    def test_calls_move_rel_twice(self):
        with patch("mouse_mover.pyautogui") as mock_gui:
            mouse_mover.move_mouse()
            assert mock_gui.moveRel.call_count == 2

    def test_nudge_and_return(self):
        with patch("mouse_mover.pyautogui") as mock_gui:
            mouse_mover.move_mouse()
            calls = mock_gui.moveRel.call_args_list
            # First call moves right, second call moves back left
            assert calls[0] == call(mouse_mover.MOVE_RADIUS, 0, duration=0.2)
            assert calls[1] == call(-mouse_mover.MOVE_RADIUS, 0, duration=0.2)


class TestMain:
    def test_stops_on_keyboard_interrupt(self):
        with patch("mouse_mover.pyautogui"):
            with patch("mouse_mover.parse_interval", return_value=1):
                with patch("mouse_mover.move_mouse", side_effect=KeyboardInterrupt):
                    with pytest.raises(SystemExit) as exc_info:
                        mouse_mover.main()
        assert exc_info.value.code == 0

    def test_failsafe_is_disabled(self):
        with patch("mouse_mover.pyautogui") as mock_gui:
            with patch("mouse_mover.parse_interval", return_value=1):
                with patch("mouse_mover.move_mouse", side_effect=KeyboardInterrupt):
                    with pytest.raises(SystemExit):
                        mouse_mover.main()
        assert mock_gui.FAILSAFE is False
