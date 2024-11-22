import json
from datetime import datetime

from bs4 import BeautifulSoup

from scraping.historical.parser import (
    parse_matches_stats,
    parse_teams_stats,
    parse_league_stats,
    parse_odds,
)
from scraping.utils.utils import safe_request
from scraping.historical.constants import primatips_base_url


def scraper(url):
    fixtures_page = safe_request(url).text
    fixtures_page_soup = BeautifulSoup(fixtures_page, "html.parser")

    fixtures_containers = fixtures_page_soup.find_all("div", class_="gml")

    # get all the urls and match weeks of all fixtures
    fixtures_info = []
    for fixture_cont in fixtures_containers:
        round = int(
            fixture_cont.find_previous_sibling("h2", class_="standing-games-date")
            .attrs.get("id")
            .replace("r", "")
        )

        fixtures_urls = fixture_cont.find_all("a", class_="gma")
        fixtures_urls = [f.attrs.get("href") for f in fixtures_urls]

        for url in fixtures_urls:
            fixtures_info.append({"url": url, "round": round})

    fixtures_stats = []

    # fixtures = fixtures_info[0: 2]
    fixtures = fixtures_info
    for fixture in fixtures:
        try:
            fixture_content = safe_request(
                f"{primatips_base_url}{fixture.get('url')}"
            ).text

            soup = BeautifulSoup(fixture_content, "html.parser")
        except Exception as e:
            print(
                f"Unable to reach {primatips_base_url}{fixture.get('url')} - skipping..."
            )
            continue

        fixture_wrapper = soup.find("div", id="game-details-wrapper")

        # fixture stats
        fixture_stats = {}
        try:
            game_league_title = fixture_wrapper.find(
                "h1", class_="game-league"
            ).text.split("-")
            league_name = game_league_title[0].strip()
            league_country = game_league_title[-1].strip()

            game_time = (
                fixture_wrapper.find(class_="game-time")
                .get_text(separator="|", strip=True)
                .split(",")[-1]
                .split("|")
            )
            game_date = datetime.strptime(game_time[0].strip(), "%d.%m.%Y").date()
            game_kickoff = datetime.strptime(game_time[-1].strip(), "%H:%M").time()

            home_team = (
                fixture_wrapper.find(class_="team-flag-left").find("h1").text.strip()
            )
            away_team = (
                fixture_wrapper.find(class_="team-flag-right").find("h1").text.strip()
            )

            fixture_stats = {
                "date": game_date,
                "kickoff": game_kickoff,
                "league": league_name,
                "country": league_country,
                "round": fixture.get("round"),
                "home_team": home_team,
                "away_team": away_team,
            }
        except Exception as e:
            print(f"Unable to parse fixtures stats due to --> {e}")

        # results
        results = {}
        try:
            scores = fixture_wrapper.find(class_="game-extended-result").text.strip()
            fh_scores = scores.split(",")[0].replace("(", "").strip().replace("-", "")
            sh_scores = scores.split(",")[-1].replace(")", "").strip().replace("-", "")

            results = {
                "hg_fh": int(fh_scores.split(" ")[0]),
                "hg_sh": int(sh_scores.split(" ")[0]),
                "ag_fh": int(fh_scores.split(" ")[-1]),
                "ag_sh": int(sh_scores.split(" ")[-1]),
            }

            if (results.get("hg_fh") + results.get("hg_sh")) > (
                results.get("ag_fh") + results.get("ag_sh")
            ):
                results["ft_res"] = "H"
            if (results.get("hg_fh") + results.get("hg_sh")) == (
                results.get("ag_fh") + results.get("ag_sh")
            ):
                results["ft_res"] = "D"
            if (results.get("hg_fh") + results.get("hg_sh")) < (
                results.get("ag_fh") + results.get("ag_sh")
            ):
                results["ft_res"] = "A"
        except Exception as e:
            print(f"Unable to parse results due to --> {e}")

        # h2h stats
        h2h_stats = []
        try:
            h2h_table_title = fixture_wrapper.select_one(
                "h2.games-title:-soup-contains('H2H last')"
            )

            no_h2h = h2h_table_title.find_next_sibling(
                "div", class_="games-stat-no-data"
            )

            if no_h2h:
                pass
            else:
                h2h_table = h2h_table_title.find_next_sibling("table")
                h2h_stats = parse_matches_stats(
                    h2h_table, fixture_stats.get("home_team"), matches_type="h2h"
                )
        except Exception as e:
            print(f"Unable to parse H2H stats due to --> {e}")

        # previous matches
        pm_home = []
        pm_away = []
        try:
            league_table = (
                fixture_wrapper.select_one("h2.games-title:-soup-contains('Table')")
                .find_next_sibling("table", class_="standing")
                .find("tbody")
            )
            league_teams = [
                {
                    "name": row.find("td", class_="team").text.strip().lower(),
                    "pos": int(row.find("td", class_="position").text.strip()),
                }
                for row in league_table.find_all("tr")
            ]

            # home team prev matches table
            ht = fixture_stats.get("home_team")
            home_pm_table = fixture_wrapper.select_one(
                f"h2.games-title:-soup-contains('{ht} last 12 games')"
            ).find_next_sibling("table", class_="games-stat")

            # away team prev matches table
            at = fixture_stats.get("away_team")
            away_pm_table = fixture_wrapper.select_one(
                f"h2.games-title:-soup-contains('{at} last 12 games')"
            ).find_next_sibling("table", class_="games-stat")

            pm_home = parse_matches_stats(
                matches_table=home_pm_table,
                home_team=fixture_stats.get("home_team"),
                matches_type="prev",
                teams_list=league_teams,
            )

            pm_away = parse_matches_stats(
                matches_table=away_pm_table,
                home_team=fixture_stats.get("away_team"),
                matches_type="prev",
                teams_list=league_teams,
            )
        except Exception as e:
            print(f"Unable to parse prev matches stats due to --> {e}")

        # teams stats
        teams_stats = {}
        try:
            teams_stats = parse_teams_stats(
                fixture_wrapper,
                fixture_stats.get("home_team"),
                fixture_stats.get("away_team"),
            )
        except Exception as e:
            print(f"Unable to parse teams stats due to --> {e}")

        #  league stats
        league_stats = {
            "lg_mp": None,
            "lw_hw": None,
            "lg_draws": None,
            "lg_aw": None,
            "lg_avg_goals": None,
            "lg_gsr_1": None,
            "lg_gsr_2": None,
            "lg_gsf_1": None,
            "lg_gsf_2": None,
            "lg_gg": None,
            "lg_015": None,
            "lg_025": None,
            "lg_035": None,
        }
        try:
            league_stats = parse_league_stats(fixture_wrapper)
        except Exception as e:
            print(f"Unable to parse league stats due to --> {e}")

        # odd
        try:
            odds_stat = parse_odds(fixture_wrapper)
        except Exception as e:
            raise (e)
            print(f"Unable to parse odds due to --> {e}")

        final_stats = {
            **fixture_stats,
            **results,
            "h2h": json.dumps(f"{h2h_stats}"),
            "pm_home": json.dumps(f"{pm_home}"),
            "pm_away": json.dumps(f"{pm_away}"),
            **teams_stats,
            **league_stats,
            **odds_stat,
        }

        # print(final_stats.keys())

        fixtures_stats.append(final_stats)

    return fixtures_stats
