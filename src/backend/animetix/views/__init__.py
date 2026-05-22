# All legacy base HTML views removed

from .classic import start_game, game_view, make_guess, start_ranked_mode, ranked_next_level, reveal_hint, abandon_game
from .vision import vision_quest_view, vision_quest_guess, spatial_view, generate_depth, manga_lab_view, process_manga_bubbles, translate_manga_bubbles
from .emoji import emoji_decode_view, emoji_decode_guess
from .animinator import animinator_view, animinator_ask, animinator_guess
from .akinetix import akinetix_view, akinetix_answer, akinetix_confirm
from .forge import archetypist_view, like_fusion
from .paradox import paradox_view, paradox_guess
from .social import leaderboard_view, achievements_view, profile_view, social_dashboard, toggle_follow, follow_user, toggle_collection, my_collection, notifications_list_view, mark_notifications_read
from .multiplayer import undercover_party_setup, undercover_party_play, undercover_online_join, undercover_online_room, codemanga_setup, codemanga_room, codemanga_game, create_duel, join_duel, duel_room_view, finish_duel, global_boss_view, global_boss_guess
from .media_games import blindtest_view, blindtest_guess, covertest_view, covertest_guess
from .vs_battle import vs_battle_view
from .mlops import health_check_view, ai_evaluation_dashboard, latent_space_view, submit_ai_feedback, gold_curation_view, validate_gold_entry, reject_gold_entry
from .audio import audio_lab_view, clone_voice_api
from .donation import donation_webhook
from .api import get_task_status, emoji_decode_stream, paradox_stream, agentic_rag_stream, sync_offline_data, animinator_stream
