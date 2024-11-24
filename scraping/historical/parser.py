from datetime import datetime
from io import StringIO

import pandas as pd
import re
from bs4 import BeautifulSoup


# HELPER FUNCTIONS
def extract_stats_from_scores(scores_list, team, tp):
    o15 = o25 = o35 = gg = cs = fts = 0

    for score in scores_list:
        if sum(score) > 1.5:
            o15 += 1
        if sum(score) > 2.5:
            o25 += 1
        if sum(score) > 3.5:
            o35 += 1
        if score[0] > 0 and score[-1] > 0:
            gg += 1
        if score[-1] < 1:
            cs += 1
        if score[0] < 1:
            fts += 1

    if team == "h":
        suffix = "0" if tp == "overall" else "1"
    else:
        suffix = "0" if tp == "overall" else "2"

    prefix = team

    stats = {
        f"{prefix}_o15_{suffix}": o15,
        f"{prefix}_o25_{suffix}": o25,
        f"{prefix}_o35_{suffix}": o35,
        f"{prefix}_gg_{suffix}": gg,
        f"{prefix}_cs_{suffix}": cs,
        f"{prefix}_fts_{suffix}": fts,
    }

    return stats


def is_team_in_the_league(team_name, league_teams):
    return any(d.get("name") == team_name for d in league_teams)


def get_team_pos(team_name, league_teams):
    for d in league_teams:
        if d.get("name").lower() == team_name.lower():
            return d.get("pos")
    return None


def get_goals(scores_str_list):
    scores = [score.split("-") for score in scores_str_list if score != "-"]
    int_goals = []
    for score in scores:
        goals = [int(re.sub(r'[^0-9]', '', s)) for s in score]
        int_goals.append(goals)
    return int_goals


def smart_avg(value, frequency):
    if frequency < 1:
        return 0
    return round(value / frequency, 2)


# PARSERS
def parse_matches_stats(matches_table, home_team, matches_type, teams_list=None) -> []:
    stats = []

    matches = matches_table.find("tbody").find_all("tr")

    for match in matches:
        date = datetime.strptime(
            match.find(class_="date").text.strip(), "%Y-%m-%d"
        ).date()

        home = match.find(class_="hteam").text.strip().lower()
        away = match.find(class_="ateam").text.strip().lower()

        result = match.find(class_="result").text.strip().split("-")
        result = [int(re.sub(r'[^0-9]', '', score)) for score in result]

        if home.lower() == home_team.lower():
            gf = result[0]
            ga = result[-1]
            venue = "hh"
        else:
            gf = result[-1]
            ga = result[0]
            venue = "ha"

        # for h2h matches
        if matches_type == "h2h":
            stats.append({"date": date, "gf": gf, "ga": ga, "venue": venue})

        # for previous matches
        if matches_type == "prev":
            # determine weather the match is a league match or not
            if venue == "hh":
                is_league_match = (
                    True if is_team_in_the_league(away, teams_list) else False
                )
            else:
                is_league_match = (
                    True if is_team_in_the_league(home, teams_list) else False
                )

            if not is_league_match:
                continue

            home_pos = get_team_pos(home, teams_list)
            away_pos = get_team_pos(away, teams_list)

            stats.append(
                {
                    "date": date,
                    "gf": gf,
                    "ga": ga,
                    "venue": venue,
                    "home_team": home,
                    "away_team": away,
                    "home_pos": home_pos,
                    "away_pos": away_pos,
                }
            )

    return stats


def parse_teams_stats(fixture_wrapper: BeautifulSoup, home_team: str, away_team: str):

    # paser home / away stats from home / away table using scores
    try:
        home_away_stats_table = fixture_wrapper.select_one(
            "h2.games-title:-soup-contains('Home/Away Matches')"
        ).find_next_sibling("table", class_="lgames")
        home_away_stats_df = pd.read_html(StringIO(str(home_away_stats_table)))[0]

        home_scores = home_away_stats_df[home_team].dropna().tolist()
        home_goals = get_goals(home_scores)

        away_scores = home_away_stats_df[away_team].dropna().tolist()
        away_goals = get_goals(away_scores)

        # todos.py: extract / deduce stats from the goals
        home_stats_home = extract_stats_from_scores(home_goals, "h", "home_away")
        away_stats_away = extract_stats_from_scores(away_goals, "a", "home_away")
    except Exception as e:
        print("Teams stats Error", e)
        home_stats_home = {
            "h_o15_1": 0,
            "h_o25_1": 0,
            "h_o35_1": 0,
            "h_gg_1": 0,
            "h_cs_1": 0,
            "h_fts_1": 0,
        }
        away_stats_away = {
            "a_o15_2": 0,
            "a_o25_2": 0,
            "a_o35_2": 0,
            "a_gg_2": 0,
            "a_cs_2": 0,
            "a_fts_2": 0,
        }

    # teams points and positions
    teams_pos_and_points = (
        fixture_wrapper.select_one("h2.games-title:-soup-contains('League Position')")
        .find_next_sibling("table", class_="perf")
        .find_all("tr")
    )
    overall_positions = [
        int(re.sub(r'[^0-9]', '', s.text.strip()) for s in teams_pos_and_points[1].find_all(class_="pos")
    ]
    home_away_positions = [
        int(re.sub(r'[^0-9]', '', s.text.strip()) for s in teams_pos_and_points[4].find_all(class_="pos")
    ]

    overall_points = [
        int(re.sub(r'[^0-9]', '', s.text.strip()) for s in teams_pos_and_points[2].find_all(class_="pos")
    ]
    home_away_points = [
        int(re.sub(r'[^0-9]', '', s.text.strip()) for s in teams_pos_and_points[5].find_all(class_="pos")
    ]

    # form stats
    teams_form_stats = (
        fixture_wrapper.select_one("h2.games-title:-soup-contains('League Form')")
        .find_next_sibling("table", class_="perf")
        .find_all("tr")
    )

    def get_inner_row_stats(stats_rows, row_index, For):
        form_stats = stats_rows[row_index].find_all(class_="form")

        For_index = 0 if For == "home" else -1

        form_stats = (
            form_stats[For_index]
            .find(class_="form-inner")
            .get_text(separator="|", strip=True)
            .split("|")
        )
        form_stats = [
            int(re.sub(r'[^0-9]', '', s)) for s in form_stats if s != "" and s != "\xa0" and s != " "
        ]

        return form_stats

    home_overall_form_stats = get_inner_row_stats(teams_form_stats, 1, "home")
    home_home_form_stats = get_inner_row_stats(teams_form_stats, 3, "home")

    away_overall_form_stats = get_inner_row_stats(teams_form_stats, 1, "away")
    away_away_form_stats = get_inner_row_stats(teams_form_stats, 3, "away")

    mp_home_overall = sum(home_overall_form_stats)
    mp_home_home = sum(home_home_form_stats)
    mp_away_overall = sum(away_overall_form_stats)
    mp_away_away = sum(away_away_form_stats)

    # teams stats table
    teams_goals_stats = (
        fixture_wrapper.select_one("h2.games-title:-soup-contains('League Goals')")
        .find_next_sibling("table", class_="perf")
        .find_all("tr")
    )

    home_overall_goal_stats = get_inner_row_stats(teams_goals_stats, 1, "home")
    away_overall_goal_stats = get_inner_row_stats(teams_goals_stats, 1, "away")

    home_home_goal_stats = get_inner_row_stats(teams_goals_stats, 3, "home")
    away_away_goal_stats = get_inner_row_stats(teams_goals_stats, 3, "away")

    teams_stats = {
        # matches played
        "h_mp_0": mp_away_overall,
        "h_mp_1": mp_home_home,
        "a_mp_0": mp_away_overall,
        "a_mp_2": mp_away_away,
        # positions
        "h_pos_0": overall_positions[0],
        "h_pos_1": home_away_positions[0],
        "a_pos_0": overall_positions[-1],
        "a_pos_2": home_away_positions[-1],
        # gsr and gcr
        "h_gsr_0": smart_avg(home_overall_goal_stats[0], mp_home_overall),
        "h_gcr_0": smart_avg(home_overall_goal_stats[-1], mp_home_overall),
        "h_gsr_1": smart_avg(home_home_goal_stats[0], mp_home_home),
        "h_gcr_1": smart_avg(home_home_goal_stats[-1], mp_home_home),
        "a_gsr_0": smart_avg(away_overall_goal_stats[0], mp_away_overall),
        "a_gcr_0": smart_avg(away_overall_goal_stats[-1], mp_away_overall),
        "a_gsr_2": smart_avg(away_away_goal_stats[0], mp_away_away),
        "a_gcr_2": smart_avg(away_away_goal_stats[-1], mp_away_away),
        # ppg
        "h_ppg_0": smart_avg(overall_points[0], mp_home_overall),
        "h_ppg_1": smart_avg(home_away_points[0], mp_home_home),
        "a_ppg_0": smart_avg(overall_points[-1], mp_away_overall),
        "a_ppg_2": smart_avg(home_away_points[-1], mp_away_away),
        # other stats
        **home_stats_home,
        **away_stats_away,
    }

    return teams_stats


def parse_league_stats(fixture_wrapper):
    league_stats_rows = (
        fixture_wrapper.select_one(
            "h2.games-title:-soup-contains('Overall Statistics for')"
        )
        .find_next_sibling("table", class_="lperf")
        .find("tbody")
        .find_all("tr")
    )

    def get_league_stat(caption, fl=False):
        for row in league_stats_rows:
            label = None
            try:
                label = row.find(class_="label").text.strip().lower()
            except Exception as e:
                continue

            if label == caption.lower():
                if fl:
                    return float(row.find(class_="data").text.strip().replace("%", ""))
                return int(row.find(class_="data").text.strip().replace("%", ""))

    league_stats = {
        "lg_mp": int(league_stats_rows[0].text.strip().split("(")[-1].replace(")", "")),
        "lw_hw": get_league_stat("Home Win"),
        "lg_draws": get_league_stat("Draw"),
        "lg_aw": get_league_stat("Away Win"),
        "lg_avg_goals": get_league_stat("Goals per Game", fl=True),
        "lg_gsr_1": get_league_stat("Home Goals per Game", fl=True),
        "lg_gsr_2": get_league_stat("Away Goals per Game", fl=True),
        "lg_gsf_1": get_league_stat("Home Team Scored in"),
        "lg_gsf_2": get_league_stat("Away Team Scored in"),
        "lg_gg": get_league_stat("Both Teams to Score"),
        "lg_015": get_league_stat("Over 1.5"),
        "lg_025": get_league_stat("Over 2.5"),
        "lg_035": get_league_stat("Over 3.5"),
    }

    return league_stats


def parse_odds(fixture_wrapper):
    # odds_tables = (
    #     fixture_wrapper.select_one("h2.games-title:-soup-contains('Coefficients and Probabilities')")
    #     .find_parent(class_='games-stat-wrapper').find_all('table', class_='odds')
    # )

    odds_tables = fixture_wrapper.find_all("table", class_="odds")

    def get_odd(odd_name, type="odd"):
        row_index = 0 if type == "odd" else 1
        for table in odds_tables:
            odd_type = table.find("thead").find(class_="odds-type").text.strip()
            if odd_name.lower() == odd_type.lower():
                try:
                    odds = (
                        table.find("tbody")
                        .find_all("tr")[row_index]
                        .find_all("td", class_="odd")
                    )
                    odds = [odd.text.strip().replace("%", "") for odd in odds]

                    if type == "odd":
                        odds = [float(odd) for odd in odds if odd != ""]
                    else:
                        odds = [int(odd) for odd in odds if odd != ""]

                    return odds
                except:
                    pass

    wdl_odds = get_odd("Standard 1X2") or [None, None]
    dc_odds = get_odd("Double Chance") or [None, None]
    o15_odds = get_odd("Over/Under 1.5") or [None, None]
    o25_odds = get_odd("Over/Under 2.5") or [None, None]
    o35_odds = get_odd("Over/Under 3.5") or [None, None]
    gg_odds = get_odd("Both Teams to Score") or [None, None]

    wdl_prob = get_odd("Standard 1X2", "prob") or [None, None]
    dc_prob = get_odd("Double Chance", "prob") or [None, None]
    o15_prob = get_odd("Over/Under 1.5", "prob") or [None, None]
    o25_prob = get_odd("Over/Under 2.5", "prob") or [None, None]
    o35_prob = get_odd("Over/Under 3.5", "prob") or [None, None]
    gg_prob = get_odd("Both Teams to Score", "prob") or [None, None]

    odds_stats = {
        "hw_odds": wdl_odds[0],
        "draw_odds": wdl_odds[-1],
        "aw_odds": wdl_odds[-1],
        "1x_odds": dc_odds[0],
        "x2_odds": dc_odds[-1],
        "o15_odds": o15_odds[0],
        "u15_odds": o15_odds[-1],
        "o25_odds": o25_odds[0],
        "u25_odds": o25_odds[-1],
        "o35_odds": o35_odds[0],
        "u35_odds": o35_odds[-1],
        "gg_yes_odds": gg_odds[0],
        "gg_no_odds": gg_odds[-1],
        "hw_prima_prob": wdl_prob[0],
        "draw_prima_prob": wdl_prob[1],
        "aw_prima_prob": wdl_prob[-1],
        "1x_prima_prob": dc_prob[0],
        "x2_prima_prob": dc_prob[-1],
        "o15_prima_prob": o15_prob[0],
        "u15_prima_prob": o15_prob[-1],
        "o25_prima_prob": o25_prob[0],
        "u25_prima_prob": o25_prob[-1],
        "o35_prima_prob": o35_prob[0],
        "u35_prima_prob": o35_prob[-1],
        "gg_yes_prima_prob": gg_prob[0],
        "gg_no_prima_prob": gg_odds[-1],
    }

    return odds_stats
