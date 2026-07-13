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

from unittest.mock import MagicMock

import pytest
from dependency_injector import providers


@pytest.fixture(autouse=True)
def _rewire_game_modules():
    import animetix.api.dependencies as dependencies_mod
    import animetix.api.games.akinetix as akinetix_mod
    import animetix.api.games.archetypist as archetypist_mod
    import animetix.api.games.blindtest as blindtest_mod
    import animetix.api.games.classic as classic_mod
    import animetix.api.games.covertest as covertest_mod
    import animetix.api.games.emoji as emoji_mod
    import animetix.api.games.paradox as paradox_mod
    import animetix.api.games.vision as vision_mod
    import animetix.api.games.world_boss as world_boss_mod
    from animetix.containers import container

    container.wire(
        modules=[
            dependencies_mod,
            classic_mod,
            archetypist_mod,
            emoji_mod,
            paradox_mod,
            covertest_mod,
            vision_mod,
            akinetix_mod,
            blindtest_mod,
            world_boss_mod,
        ]
    )

    # Other test modules (e.g. the routed sync_offline view) can instantiate the
    # *real* domain-service Singletons and leave them cached on the container. A
    # cached real instance shadows the per-test ``providers.Object`` override, so the
    # view ends up calling the real service with mock arguments (TypeError). Clearing
    # the cached Singletons here -- ``reset()`` only drops the memoised instance, it
    # does NOT touch the sub-container wiring the way ``reset_override()`` does -- keeps
    # each test hermetic regardless of what ran before it.
    guarded = (
        "catalog_service",
        "game_service",
        "guardrail_service",
        "emoji_service",
        "paradox_service",
        "cover_test_service",
        "vision_service",
        "akinetix_service",
        "blind_test_service",
        "world_boss_quiz_service",
        "proximity_service",
    )
    for name in guarded:
        getattr(container.core, name).reset()

    # Baseline: overrides already in place (e.g. session-scoped ones) are none of
    # this test's business. What must never happen is a test ADDING an override
    # and not removing it.
    before = {name: len(getattr(container.core, name).overridden) for name in guarded}

    yield

    # Tripwire: a game test that leaves a provider overridden poisons the whole
    # session — a leaked MagicMock catalog_service reached tests/api/test_explore
    # and hung CI forever (DRF's JSON encoder recurses on a MagicMock: it calls
    # .tolist(), gets another MagicMock, and tries to encode that one too, so the
    # job died on SIGTERM with no usable error). Fail HERE, on the test that
    # actually leaked, instead of somewhere unrelated hundreds of tests later.
    leaked = {}
    for name in guarded:
        provider = getattr(container.core, name)
        extra = len(provider.overridden) - before[name]
        if extra > 0:
            leaked[name] = extra
            # Unpoison the container so the *other* tests still run clean.
            for _ in range(extra):
                provider.reset_last_overriding()
    assert not leaked, (
        f"This test leaked container overrides: {leaked}. Scope every override "
        "(a `with` block or a fixture teardown) so it is always reset."
    )


@pytest.fixture(autouse=True)
def _default_proximity_service():
    """Classic's start/guess views now depend on ``proximity_service``.

    Every OTHER test in this package -- and most of ``test_classic_coverage.py``'s
    own tests -- overrides ``catalog_service``/``game_service`` with a bare
    ``MagicMock`` and never touches proximity at all. That is a problem: the real
    ``ProximityService`` calls ``catalog_service.load_data(media_type)``, and an
    unconfigured ``MagicMock`` answers with another ``MagicMock`` whose default
    ``__iter__`` yields nothing -- so ``build_index`` sees an EMPTY catalogue and
    ``ProximityService`` correctly (and deliberately) raises ``GameLogicError``.
    Without this fixture, that would 503 every unmodified classic test.

    So: give every test a harmless default ranking. ``test_classic_proximity.py``
    pushes its OWN ``providers.Object`` override on top of this one and pops only
    that layer (its own ``with`` block, via ``reset_last_overriding()``) well
    before this fixture's teardown runs -- so this default is always the last
    thing pushed and the last thing popped, in the well-behaved case.

    What is NOT guaranteed: this fixture's own ``with`` block only pops whatever
    is on TOP of the override stack when it exits -- ``reset_last_overriding()``
    has no notion of "pop MY override specifically". If some future test also
    overrides ``proximity_service`` and forgets to clean up, this fixture's exit
    pops the LEAK instead of its own stub, stranding the stub on the stack. That
    is exactly the "leaked MagicMock poisons the whole session" failure
    ``_rewire_game_modules``'s tripwire exists to catch -- so ``proximity_service``
    is now IN the ``guarded`` tuple above: the stranded stub still shows up as an
    unexpected extra override there, fails the leaking test loudly, and gets
    popped clean for every test that runs after it.
    """
    from animetix.containers import container

    stub = MagicMock()
    stub.rank.return_value = []
    stub.report.return_value = {
        "percent": 0.0,
        "rank": 0,
        "total": 0,
        "reasons": [],
    }
    with container.core.proximity_service.override(providers.Object(stub)):
        yield
