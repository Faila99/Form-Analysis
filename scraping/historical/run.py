import os

from scraping.historical.constants import field_names
from scraping.historical.scraper import scraper
from shared.utils.utils import save_to_json, convert_to_csv, load_json


def run(leagues_url_details):
    current_state = load_json("scraping/historical/state_2.json")
    # Stop script if inactive
    if not current_state.get("active", True):  # Defaults to True if 'active' is missing
        print("All leagues and seasons have been scraped. Stopping script.")
        return

    current_league_index = current_state.get('league_index')
    current_league = leagues_url_details[current_league_index]

    seasons = current_league.get("seasons")
    base_url = current_league.get("url")
    country = current_league.get("country")
    league_name = current_league.get("league_name")

    season_index = current_state.get("season_index")
    new_season_index = season_index + 3 if season_index + 3 < len(seasons) else len(seasons)
    is_last_season = new_season_index == len(seasons)

    is_last_league = current_league_index == len(leagues_url_details) - 1

    # create a directory for the data
    directory_path = f"./shared/data/historical/{country}"
    try:
        os.makedirs(
            directory_path, exist_ok=True
        )  # Creates parent directories if needed
        print(f"Directory created successfully at: {directory_path}")
    except OSError as e:
        print(f"Error creating directory: {e}")
        return

    for season in seasons[season_index:new_season_index]:
        url = f"{base_url}/{season}"
        print(url)
        file_name = f"{country}_{league_name}_{season}"
        
        try:
            scraped_stats = scraper(url)

            convert_to_csv(
                scraped_stats, f"{directory_path}/{file_name}.csv", field_names=field_names
            )
            print(f'scraped stats for {country} - {league_name} "{season}" season.')
        except Exception as e:
            print(f"Unexpected error occur while scraping {url}")

            # Track the error and the URL in a JSON file
            try:
                current_error = load_json("scraping/historical/errors_2.json")
            except FileNotFoundError:
                current_error = []  # Initialize empty list if file doesn't exist
    
            current_error.append({'url': url, 'error': str(e), 'league_index': current_league_index, 'season_index': season_index})
            
            save_to_json("./scraping/historical/errors_2.json", current_error)
            continue
    # Check if this is the last league and the last season

    # Update state
    if is_last_league and is_last_season:
        print("All leagues and seasons scraped. Deactivating script.")
        current_state["active"] = False
    else:
        # Update to the next league or season
        if is_last_season:
            # Move to the next league
            current_state["season_index"] = 0
            current_state["league_index"] = current_league_index + 1
        else:
            # Move to the next season within the current league
            current_state["season_index"] = new_season_index

    # print(current_state)
    # print(leagues_url_details[current_league_index]['league_name'])
    # Save updated state
    save_to_json( "./scraping/historical/state_2.json", current_state)
    print(f"Scraping complete, state updated. - {current_state}")
    print("")
