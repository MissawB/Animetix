import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from adapters.infrastructure.django_cache_adapter import DjangoCacheAdapter
from adapters.infrastructure.django_config_adapter import DjangoConfigAdapter
from adapters.infrastructure.django_notification_adapter import (
    DjangoNotificationAdapter,
)
from adapters.infrastructure.middleware_user_context_adapter import (
    MiddlewareUserContextAdapter,
)
from adapters.infrastructure.vertex_feature_store_client import VertexFeatureStoreClient
from adapters.infrastructure.vertex_pipelines_client import VertexPipelinesClient


# 1. DjangoCacheAdapter Tests
def test_django_cache_adapter():
    adapter = DjangoCacheAdapter()

    with patch("adapters.infrastructure.django_cache_adapter.cache") as mock_cache:
        # get
        mock_cache.get.return_value = "val"
        assert adapter.get("key", "default") == "val"
        mock_cache.get.assert_called_with("key", "default")

        # set
        adapter.set("key", "val", 100)
        mock_cache.set.assert_called_with("key", "val", timeout=100)

        # get_many
        mock_cache.get_many.return_value = {"k": "v"}
        assert adapter.get_many(["k"]) == {"k": "v"}
        mock_cache.get_many.assert_called_with(["k"])

        # set_many
        adapter.set_many({"k": "v"}, 100)
        mock_cache.set_many.assert_called_with({"k": "v"}, timeout=100)


# 2. DjangoConfigAdapter Tests
def test_django_config_adapter():
    adapter = DjangoConfigAdapter()

    class MockSettings:
        TEST_VAR = "hello"

    with patch("adapters.infrastructure.django_config_adapter.settings", MockSettings):
        assert adapter.get("TEST_VAR", "fallback") == "hello"
        assert adapter.get("NON_EXISTENT", "fallback") == "fallback"


# 3. DjangoNotificationAdapter Tests
def test_django_notification_adapter():
    adapter = DjangoNotificationAdapter()

    mock_user = MagicMock()
    mock_user.id = 123

    mock_notification = MagicMock()
    mock_notification.id = 456
    mock_notification.created_at = datetime(2026, 7, 7, 12, 0)

    mock_user_model = MagicMock()
    mock_user_model.objects.get.return_value = mock_user

    mock_notification_model = MagicMock()
    mock_notification_model.objects.create.return_value = mock_notification

    mock_channel_layer = MagicMock()

    with (
        patch("django.contrib.auth.get_user_model", return_value=mock_user_model),
        patch("animetix.models.Notification", mock_notification_model),
        patch("channels.layers.get_channel_layer", return_value=mock_channel_layer),
        patch("asgiref.sync.async_to_sync", lambda f: f),
        patch("adapters.infrastructure.django_notification_adapter.logger"),
    ):

        # Send simple notification
        res = adapter.send(
            user_id=123,
            title="Succès Débloqué !",
            message="You did it!",
            notification_type="achievement",
            link="/achievements",
        )

        assert res == mock_notification
        mock_user_model.objects.get.assert_called_with(id=123)
        mock_notification_model.objects.create.assert_called()
        mock_channel_layer.group_send.assert_called()


def test_django_notification_adapter_failure():
    adapter = DjangoNotificationAdapter()

    mock_user_model = MagicMock()
    mock_user_model.objects.get.side_effect = Exception("DB Error")

    with (
        patch("django.contrib.auth.get_user_model", return_value=mock_user_model),
        patch(
            "adapters.infrastructure.django_notification_adapter.logger"
        ) as mock_logger,
    ):
        res = adapter.send(user_id=1, title="t", message="m")
        assert res is None
        mock_logger.error.assert_called()


# 4. MiddlewareUserContextAdapter Tests
def test_middleware_user_context_adapter():
    adapter = MiddlewareUserContextAdapter()

    # When middleware is present and resolves user context
    mock_middleware = MagicMock()
    mock_middleware.get_current_user_id.return_value = 42
    mock_middleware.get_current_user_tier.return_value = "premium"

    with patch.dict("sys.modules", {"animetix.middleware": mock_middleware}):
        assert adapter.get_current_user_id() == 42
        assert adapter.get_current_user_tier() == "premium"


def test_middleware_user_context_adapter_missing():
    adapter = MiddlewareUserContextAdapter()

    # When middleware is not importable
    with patch(
        "builtins.__import__",
        side_effect=ImportError("No module named animetix.middleware"),
    ):
        assert adapter.get_current_user_id() is None
        assert adapter.get_current_user_tier() == "free"


# 5. VertexFeatureStoreClient Tests
def test_vertex_feature_store_simulation():
    # Force simulation mode
    with (
        patch.dict("os.environ", {"VERTEX_AI_FEATURE_STORE_SIMULATION": "true"}),
        patch(
            "adapters.infrastructure.vertex_feature_store_client.HAS_PLATFORM", False
        ),
        patch(
            "adapters.infrastructure.vertex_feature_store_client.os.path.exists",
            return_value=True,
        ),
        patch(
            "builtins.open",
            mock_open(read_data=json.dumps({"123": {"shonen_hero": 0.9}})),
        ),
        patch("adapters.infrastructure.vertex_feature_store_client.logger"),
    ):

        client = VertexFeatureStoreClient()
        assert client.simulation_mode is True

        # Read
        feats = client.get_online_features("123")
        assert feats == {"shonen_hero": 0.9}

        # Write
        with patch.object(client, "_save_mock_store") as mock_save:
            client.write_online_features("123", {"seinen_rebel": 0.8})
            mock_save.assert_called()


def test_vertex_feature_store_real_mode():
    mock_aiplatform = MagicMock()
    mock_entity_type = MagicMock()
    mock_row = MagicMock()
    mock_row.shonen_hero = 0.95
    mock_entity_type.read_manual_features.return_value = [mock_row]

    mock_fs = MagicMock()
    mock_fs.get_entity_type.return_value = mock_entity_type
    mock_aiplatform.Featurestore.return_value = mock_fs

    with (
        patch.dict("os.environ", {"VERTEX_AI_FEATURE_STORE_SIMULATION": "false"}),
        patch("adapters.infrastructure.vertex_feature_store_client.HAS_PLATFORM", True),
        patch(
            "adapters.infrastructure.vertex_feature_store_client.aiplatform",
            mock_aiplatform,
        ),
        patch("adapters.infrastructure.vertex_feature_store_client.logger"),
    ):

        client = VertexFeatureStoreClient()
        assert client.simulation_mode is False

        # Get
        feats = client.get_online_features("123")
        assert feats.get("shonen_hero") == 0.95

        # Write
        client.write_online_features("123", {"seinen_rebel": 0.8})
        mock_entity_type.write_feature_values.assert_called()


# 6. VertexPipelinesClient Tests
def test_vertex_pipelines_simulation():
    # Force simulation mode
    with (
        patch.dict("os.environ", {"VERTEX_AI_SIMULATION": "true"}),
        patch("adapters.infrastructure.vertex_pipelines_client.HAS_PLATFORM", False),
        patch("adapters.infrastructure.vertex_pipelines_client.HAS_KFP", True),
        patch("adapters.infrastructure.vertex_pipelines_client.compiler"),
        patch(
            "adapters.infrastructure.vertex_pipelines_client.os.path.exists",
            return_value=True,
        ),
        patch("builtins.open", mock_open(read_data=json.dumps([]))),
        patch("adapters.infrastructure.vertex_pipelines_client.logger"),
    ):

        client = VertexPipelinesClient()
        assert client.simulation_mode is True

        # Mock pipeline function
        def mock_pipeline_func():
            pass

        with patch.object(client, "_save_mock_run") as mock_save:
            res = client.submit_pipeline(
                mock_pipeline_func, "test-pipeline", {"param": 1}
            )
            assert "name" in res
            assert res["state"] == "PIPELINE_STATE_RUNNING"
            mock_save.assert_called()

        # Get pipeline run (transition to succeeded in simulation)
        with (
            patch.object(client, "_load_mock_runs", return_value=[res]),
            patch.object(client, "_save_mock_run") as mock_save,
        ):
            run_status = client.get_pipeline_run(res["name"])
            assert run_status["state"] == "PIPELINE_STATE_SUCCEEDED"
            mock_save.assert_called()


def test_vertex_pipelines_real_mode():
    mock_aiplatform = MagicMock()
    mock_job = MagicMock()
    mock_job.resource_name = "projects/123/locations/europe-west1/pipelineJobs/456"
    mock_job.state = "PIPELINE_STATE_SUCCEEDED"
    mock_job.create_time = datetime(2026, 7, 7, 12, 0)

    mock_aiplatform.PipelineJob.return_value = mock_job
    mock_aiplatform.PipelineJob.get.return_value = mock_job
    mock_aiplatform.PipelineJob.list.return_value = [mock_job]

    with (
        patch.dict("os.environ", {"VERTEX_AI_SIMULATION": "false"}),
        patch("adapters.infrastructure.vertex_pipelines_client.HAS_PLATFORM", True),
        patch("adapters.infrastructure.vertex_pipelines_client.HAS_KFP", True),
        patch("adapters.infrastructure.vertex_pipelines_client.compiler"),
        patch(
            "adapters.infrastructure.vertex_pipelines_client.aiplatform",
            mock_aiplatform,
        ),
        patch("adapters.infrastructure.vertex_pipelines_client.logger"),
    ):

        client = VertexPipelinesClient()
        assert client.simulation_mode is False

        def mock_pipeline_func():
            pass

        res = client.submit_pipeline(mock_pipeline_func, "test-pipeline", {"param": 1})
        assert res["name"] == mock_job.resource_name
        mock_job.submit.assert_called()

        # Get run
        run_status = client.get_pipeline_run(mock_job.resource_name)
        assert run_status["state"] == "PIPELINE_STATE_SUCCEEDED"

        # List runs
        runs = client.list_pipeline_runs()
        assert len(runs) == 1
        assert runs[0]["name"] == mock_job.resource_name
