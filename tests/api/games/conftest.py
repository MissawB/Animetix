"""Shared wiring guard for the game-mode coverage tests.

In this worktree the application-ready wiring leaves the ``@inject`` markers in the
game view modules bound to providers whose ``core -> persistence`` sub-container
link is stale, so resolving a real domain service raises
``Container.core.persistence.feedback_adapter is not defined``. Re-wiring the view
modules rebinds those markers to the live instance providers so that the
instance-level overrides applied inside each test take effect.

The wiring is re-applied *before every test* (autouse) so that the order in which
the game-mode test modules run cannot leave a stale binding behind. We never call
``container.reset_override()`` -- on this dependency_injector version that call
detaches the ``core -> persistence`` DependenciesContainer link and re-triggers the
bug. Each test scopes its overrides with ``with`` blocks, which clean themselves up.

NOTE: these game tests must NOT be run in the same pytest process as
``--cov=animetix.views.api``. Coverage-instrumenting ``animetix.views.api`` forces a
re-import of the ``animetix.api.dependencies`` graph whose ``@inject`` markers then
stay in an unwired ``_Marker`` state that re-wiring cannot repair, which makes the
game views fall through to the real (unmocked) services. Measure ``views.api``
coverage in a separate invocation (see test_views_api_coverage.py / test_sync.py).
"""

import pytest


@pytest.fixture(autouse=True)
def _rewire_game_modules():
    import animetix.api.dependencies as dependencies_mod
    import animetix.api.games.archetypist as archetypist_mod
    import animetix.api.games.classic as classic_mod
    import animetix.api.games.covertest as covertest_mod
    import animetix.api.games.emoji as emoji_mod
    import animetix.api.games.paradox as paradox_mod
    from animetix.containers import container

    container.wire(
        modules=[
            dependencies_mod,
            classic_mod,
            archetypist_mod,
            emoji_mod,
            paradox_mod,
            covertest_mod,
        ]
    )

    # Other test modules (e.g. the routed sync_offline view) can instantiate the
    # *real* domain-service Singletons and leave them cached on the container. A
    # cached real instance shadows the per-test ``providers.Object`` override, so the
    # view ends up calling the real service with mock arguments (TypeError). Clearing
    # the cached Singletons here -- ``reset()`` only drops the memoised instance, it
    # does NOT touch the sub-container wiring the way ``reset_override()`` does -- keeps
    # each test hermetic regardless of what ran before it.
    for name in (
        "catalog_service",
        "game_service",
        "guardrail_service",
        "emoji_service",
        "paradox_service",
        "cover_test_service",
    ):
        getattr(container.core, name).reset()
    yield
