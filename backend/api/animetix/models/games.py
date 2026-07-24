from django.contrib.auth.models import User
from django.db import models


class GlobalBoss(models.Model):
    week_key = models.CharField(
        max_length=32, unique=True, null=True, blank=True, default=None
    )
    title = models.CharField(max_length=255)
    secret_title = models.CharField(max_length=255)
    media_type = models.CharField(max_length=20)
    total_hp = models.IntegerField(default=10000)
    current_hp = models.IntegerField(default=10000)
    community_hints = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    reward_xp = models.IntegerField(default=1000)
    reward_distributed = models.BooleanField(default=False)
    current_phase = models.IntegerField(default=1)
    phase_modifiers = models.JSONField(default=dict)

    def update_phase(self) -> bool:
        old_phase = self.current_phase
        hp_percent = (self.current_hp / self.total_hp) * 100 if self.total_hp > 0 else 0
        if hp_percent < 10:
            self.current_phase = 3
        elif hp_percent < 50:
            self.current_phase = 2
        else:
            self.current_phase = 1
        return old_phase != self.current_phase


class BossParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    boss = models.ForeignKey(GlobalBoss, on_delete=models.CASCADE)
    points_contributed = models.IntegerField(default=0)
    best_tier = models.IntegerField(default=0)
    limiter_breaks = models.IntegerField(default=0)
    last_participation = models.DateTimeField(auto_now=True)

    tier = models.IntegerField(default=1)
    streak = models.IntegerField(default=0)
    limiter_break = models.BooleanField(default=False)
    run_damage = models.IntegerField(default=0)

    pending_index = models.IntegerField(null=True, blank=True)
    pending_label = models.CharField(max_length=255, blank=True, default="")
    pending_subject = models.CharField(max_length=255, blank=True, default="")
    pending_options = models.JSONField(default=list, blank=True)
    pending_prompt = models.TextField(blank=True, default="")
    pending_archetype = models.CharField(max_length=64, blank=True, default="")
    pending_image = models.TextField(blank=True, null=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "boss"], name="unique_bossparticipation_user_boss"
            )
        ]


class DuelRoom(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    player1 = models.ForeignKey(User, related_name="duels_p1", on_delete=models.CASCADE)
    player2 = models.ForeignKey(
        User, related_name="duels_p2", on_delete=models.CASCADE, null=True, blank=True
    )
    media_type = models.CharField(max_length=20)
    secret_title = models.CharField(max_length=255)
    winner = models.ForeignKey(
        User, related_name="duels_won", on_delete=models.SET_NULL, null=True, blank=True
    )
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DailyChallenge(models.Model):
    date = models.DateField(unique=True)
    media_type = models.CharField(max_length=20)
    game_mode = models.CharField(max_length=20, default="classic")
    secret_title = models.CharField(max_length=255)


class ChallengeResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)
    attempts = models.IntegerField()
    time_taken = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)


class DailyResult(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_results"
    )
    date = models.DateField()
    media_type = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date", "media_type")


class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    xp_reward = models.IntegerField(default=100)
    rarity = models.CharField(max_length=20, default="Common")

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class GameplaySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    game_mode = models.CharField(max_length=50)
    media_type = models.CharField(max_length=20)
    target_item = models.CharField(max_length=255)
    history = models.JSONField()
    was_won = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.game_mode} - {self.target_item}"


class CreativeFusion(models.Model):
    title_a = models.CharField(max_length=255)
    title_b = models.CharField(max_length=255)
    media_type_a = models.CharField(max_length=50)
    media_type_b = models.CharField(max_length=50)

    scenario_text = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)

    chaos_level = models.IntegerField(default=50)
    universe_balance = models.IntegerField(default=50)
    art_style = models.CharField(max_length=100, default="Cyberpunk")

    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="fusions"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="remixes"
    )
    likes = models.ManyToManyField(User, related_name="liked_fusions", blank=True)
    vn_script = models.JSONField(null=True, blank=True)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title_a} x {self.title_b} by {self.creator}"


class VsBattle(models.Model):
    char_a_name = models.CharField(max_length=255)
    char_b_name = models.CharField(max_length=255)
    char_a_franchise = models.CharField(max_length=255, null=True, blank=True)
    char_b_franchise = models.CharField(max_length=255, null=True, blank=True)

    char_a_data = models.JSONField()
    char_b_data = models.JSONField()

    winner = models.CharField(max_length=255)
    verdict_summary = models.TextField()
    debate_history = models.JSONField()

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vs_battles",
    )
    likes = models.ManyToManyField(User, related_name="liked_vs_battles", blank=True)

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.char_a_name} vs {self.char_b_name}"
