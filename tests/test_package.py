import foreman


def test_package_exposes_cli_entry_point() -> None:
    assert callable(foreman.main)
