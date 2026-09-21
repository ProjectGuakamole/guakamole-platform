import pytest

from main import main


def test_main_outputs_backend_message(capsys: pytest.CaptureFixture[str]) -> None:
    main()

    captured = capsys.readouterr()

    assert captured.out == "Hello from backend!\n"
