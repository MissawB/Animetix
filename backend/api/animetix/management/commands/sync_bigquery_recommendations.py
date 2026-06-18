from animetix.models import MediaItem, UserRecommendation
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Trains the BigQuery ML matrix factorization recommender model and syncs top 10 recommendations to AlloyDB."

    def handle(self, *args, **options):
        is_prod = getattr(settings, "IS_PRODUCTION", False)
        dataset_id = getattr(settings, "GCP_BIGQUERY_DATASET", "telemetry")

        self.stdout.write("Initializing BigQuery sync process...")

        recs = []
        if is_prod:
            from google.cloud import bigquery  # noqa: E402

            client = bigquery.Client()

            # 1. Execute BigQuery ML Model Training
            train_query = (
                f"CREATE OR REPLACE MODEL `{client.project}.{dataset_id}.recommender_model` "  # nosec
                "OPTIONS("
                "  model_type='matrix_factorization',"
                "  user_col='user_id',"
                "  item_col='media_item_id',"
                "  rating_col='rating_weight'"
                ") AS "
                "SELECT "
                "  user_id, "
                "  media_item_id, "
                "  SUM(weight) as rating_weight "
                "FROM "
                f"  `{client.project}.{dataset_id}.user_interactions` "  # nosec
                "GROUP BY "
                "  user_id, "
                "  media_item_id"
            )  # nosec B608
            self.stdout.write("Training BigQuery ML Model...")
            client.query(train_query).result()

            # 2. Get recommendations
            rec_query = (
                "SELECT "
                "  user_id, "
                "  media_item_id, "
                "  predicted_rating_weight as score, "
                "  ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY predicted_rating_weight DESC) as rank "
                "FROM "
                f"  ML.RECOMMEND(MODEL `{client.project}.{dataset_id}.recommender_model`) "  # nosec
                "WHERE "
                "  predicted_rating_weight IS NOT NULL "
                "QUALIFY "
                "  rank <= 10"
            )
            self.stdout.write("Fetching top 10 recommendations...")
            query_job = client.query(rec_query)
            results = query_job.result()

            for row in results:
                recs.append(
                    {
                        "user_id": row["user_id"],
                        "media_item_id": row["media_item_id"],
                        "score": row["score"],
                        "rank": row["rank"],
                    }
                )
        else:
            self.stdout.write("Local dev mode: generating mock recommendations.")
            # Generate mock recommendations for testing/dev
            users = User.objects.all()
            items = MediaItem.objects.all()[:10]
            for user in users:
                for idx, item in enumerate(items):
                    recs.append(
                        {
                            "user_id": user.id,
                            "media_item_id": item.id,
                            "score": 4.5 - (idx * 0.2),
                            "rank": idx + 1,
                        }
                    )

        # 3. Transaction-safe database synchronization
        self.stdout.write(
            f"Syncing {len(recs)} recommendations to AlloyDB/PostgreSQL..."
        )

        with transaction.atomic():
            # Clear old recommendations
            UserRecommendation.objects.all().delete()

            # Bulk Insert new ones
            new_objs = []
            for item in recs:
                try:
                    # Verify user and media item exist to avoid foreign key issues
                    user = User.objects.get(id=item["user_id"])
                    media_item = MediaItem.objects.get(id=item["media_item_id"])
                    new_objs.append(
                        UserRecommendation(
                            user=user,
                            media_item=media_item,
                            score=item["score"],
                            rank=item["rank"],
                        )
                    )
                except (User.DoesNotExist, MediaItem.DoesNotExist):
                    continue

            UserRecommendation.objects.bulk_create(new_objs)

        self.stdout.write(self.style.SUCCESS("Successfully synced recommendations!"))
