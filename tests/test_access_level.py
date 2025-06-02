from gitlab.const import AccessLevel

from src.gitlab_users.gitlab_users import ACCESS_LEVEL


def test_access_level_mapping():
    assert ACCESS_LEVEL["guest"] == AccessLevel.GUEST
    assert ACCESS_LEVEL["reporter"] == AccessLevel.REPORTER
    assert ACCESS_LEVEL["developer"] == AccessLevel.DEVELOPER
    assert ACCESS_LEVEL["maintainer"] == AccessLevel.MAINTAINER
    assert ACCESS_LEVEL["master"] == AccessLevel.MAINTAINER
    assert ACCESS_LEVEL["owner"] == AccessLevel.OWNER
