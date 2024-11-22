from scipy.stats import poisson


def calculate_expected_goals(gsrh, gcrh, gsra, gcra, gsrlh, gsrla):
    home_att_strength = gsrh / gsrlh
    home_def_strength = gcrh / gsrla

    away_att_strength = gsra / gsrla
    away_def_strength = gcra / gsrlh

    xgh = home_att_strength * away_def_strength * gsrlh
    xga = away_att_strength * home_def_strength * gsrla

    return {"home": round(xgh, 2), "away": round(xga, 2)}


def calculate_probabilities_with_odds(home_expected_goals, away_expected_goals):
    max_goals = 10  # Calculate probabilities for up to 10 goals (can be adjusted)

    # Calculate Poisson probabilities for home and away goals
    home_goal_probs = [
        (poisson.pmf(i, home_expected_goals)) for i in range(max_goals + 1)
    ]
    away_goal_probs = [
        (poisson.pmf(i, away_expected_goals)) for i in range(max_goals + 1)
    ]

    # Calculate probabilities for home win, draw, and away win
    home_win_prob = sum(
        home_goal_probs[i] * sum(away_goal_probs[:i]) for i in range(1, max_goals + 1)
    )
    draw_prob = sum(
        home_goal_probs[i] * away_goal_probs[i] for i in range(max_goals + 1)
    )
    away_win_prob = sum(
        away_goal_probs[i] * sum(home_goal_probs[:i]) for i in range(1, max_goals + 1)
    )

    # Double chance markets
    home_win_or_draw = home_win_prob + draw_prob
    away_win_or_draw = away_win_prob + draw_prob
    home_win_or_away_win = home_win_prob + away_win_prob

    # Calculate BTTS (Both Teams To Score)
    # btts_prob = 1 - (
    #     home_goal_probs[0] * sum(away_goal_probs)
    #     + away_goal_probs[0] * sum(home_goal_probs)
    # )

    # Calculate over 1.5, over 2.5, over 3.5, and over 4.5 goals
    fixture_avg_goals = home_expected_goals + away_expected_goals
    over_0_5_prob = 1 - poisson.cdf(0, fixture_avg_goals)
    over_1_5_prob = 1 - poisson.cdf(1, fixture_avg_goals)
    over_2_5_prob = 1 - poisson.cdf(2, fixture_avg_goals)
    over_3_5_prob = 1 - poisson.cdf(3, fixture_avg_goals)
    over_4_5_prob = 1 - poisson.cdf(4, fixture_avg_goals)

    # Home team over goals probabilities
    home_over_0_5 = 1 - poisson.cdf(0, home_expected_goals)
    home_over_1_5 = 1 - poisson.cdf(1, home_expected_goals)
    home_over_2_5 = 1 - poisson.cdf(2, home_expected_goals)
    home_over_3_5 = 1 - poisson.cdf(3, home_expected_goals)

    # Away team over goals probabilities
    away_over_0_5 = 1 - poisson.cdf(0, away_expected_goals)
    away_over_1_5 = 1 - poisson.cdf(1, away_expected_goals)
    away_over_2_5 = 1 - poisson.cdf(2, away_expected_goals)
    away_over_3_5 = 1 - poisson.cdf(3, away_expected_goals)

    btts_prob = home_over_0_5 * away_over_0_5

    # Handicap betting probabilities
    home_minus_1 = sum(
        home_goal_probs[i] * sum(away_goal_probs[:i]) for i in range(2, max_goals + 1)
    )
    home_minus_2 = sum(
        home_goal_probs[i] * sum(away_goal_probs[: i - 1])
        for i in range(3, max_goals + 1)
    )
    home_minus_3 = sum(
        home_goal_probs[i] * sum(away_goal_probs[: i - 2])
        for i in range(4, max_goals + 1)
    )

    away_minus_1 = sum(
        away_goal_probs[i] * sum(home_goal_probs[:i]) for i in range(2, max_goals + 1)
    )
    away_minus_2 = sum(
        away_goal_probs[i] * sum(home_goal_probs[: i - 1])
        for i in range(3, max_goals + 1)
    )
    away_minus_3 = sum(
        away_goal_probs[i] * sum(home_goal_probs[: i - 2])
        for i in range(4, max_goals + 1)
    )

    # Prepare result dictionary with probabilities
    probabilities_raw = {
        "home_win": home_win_prob,
        "draw": draw_prob,
        "away_win": away_win_prob,
        "_1x": home_win_or_draw,
        "x2": away_win_or_draw,
        "_12": home_win_or_away_win,
        "btts": btts_prob,
        "o05": over_0_5_prob,
        "u05": 1 - over_0_5_prob,
        "o15": over_1_5_prob,
        "u15": 1 - over_1_5_prob,
        "o25": over_2_5_prob,
        "u25": 1 - over_2_5_prob,
        "o35": over_3_5_prob,
        "u35": 1 - over_3_5_prob,
        "o45": over_4_5_prob,
        "u45": 1 - over_4_5_prob,
        "home_o05": home_over_0_5,
        "home_o15": home_over_1_5,
        "home_o25": home_over_2_5,
        "home_o35": home_over_3_5,
        "away_o05": away_over_0_5,
        "away_o15": away_over_1_5,
        "away_o25": away_over_2_5,
        "away_o35": away_over_3_5,
        "home_minus_1": home_minus_1,
        "home_minus_2": home_minus_2,
        "home_minus_3": home_minus_3,
        "away_minus_1": away_minus_1,
        "away_minus_2": away_minus_2,
        "away_minus_3": away_minus_3,
    }

    probabilities_percent = {
        k: float(round(v * 100, 2)) for k, v in probabilities_raw.items()
    }

    # Calculate corresponding odds from probabilities
    odds = {
        k: (float(round(1 / v, 2)) if v > 0 else float("inf"))
        for k, v in probabilities_raw.items()
    }

    return {"probabilities": probabilities_percent, "odds": odds}
