from gitlab_users.models import Group, User


def test_user_dataclass():
    user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    assert user.id == 1
    assert user.username == "bob"
    assert user.email == "bob@example.com"
    assert user.name == "Bob"
    assert user.state == "active"


def test_group_dataclass():
    group = Group(id=42, name="devs", path="devs-path")
    assert group.id == 42
    assert group.name == "devs"
    assert group.path == "devs-path"
