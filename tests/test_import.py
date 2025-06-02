def test_import_package():
    import gitlab_users

    assert hasattr(gitlab_users, "__version__")
