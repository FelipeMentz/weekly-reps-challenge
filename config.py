# config.py
# Single source of truth for the Weekly Reps Challenge

CHALLENGE_CONFIG = {
    "squat": {
        "display_name": "Squats",
        "weekly_target": 400,
        "order": 1,
    },
    "push-up": {
        "display_name": "Push-ups",
        "weekly_target": 300,
        "order": 2,
    },
    "dip": {
        "display_name": "Dips",
        "weekly_target": 200,
        "order": 3,
    },
    "pull-up": {
        "display_name": "Pull-ups",
        "weekly_target": 100,
        "order": 4,
    },
}

# Optional helpers (we WILL use these later)
EXERCISE_KEYS = list(CHALLENGE_CONFIG.keys())

TOTAL_WEEKLY_REPS = sum(
    exercise["weekly_target"] for exercise in CHALLENGE_CONFIG.values()
)
