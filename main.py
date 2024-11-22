from scraping.historical.run import run as run_historical_scraper
from shared.utils.utils import load_json


def main():
    leagues_url_details = load_json('scraping/historical/urls_v2.json')
    run_historical_scraper(leagues_url_details)
    # print(leagues_url_details)


if __name__ == "__main__":
    main()
