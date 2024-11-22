import requests
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError,
    InvalidURL,
    TooManyRedirects,
)
import time

from shared.utils.utils import save_to_json


def safe_request(url, max_retries=3, retry_delay=2, timeout=10):
    retryable_exceptions = (Timeout, ConnectionError)

    for retry in range(max_retries + 1):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response  # Successful response

        except HTTPError as e:
            print(f"HTTP error (Attempt {retry + 1}/{max_retries + 1}): {e}")
            return None  # HTTP errors are not retryable

        except InvalidURL as e:
            print(f"Inalid URL (Attempt {retry + 1}/{max_retries + 1}): {e}")
            return None  # invalid url error is not retryable

        except TooManyRedirects as e:
            print(f"Too many redirects (Attempt {retry + 1}/{max_retries + 1}): {e}")
            return None  # TooManyRedirects error is not retryable

        except RequestException as e:
            if isinstance(e, retryable_exceptions):
                if isinstance(e, Timeout):
                    print(
                        f"Request timeout (Attempt {retry + 1}/{max_retries + 1}): {e}"
                    )

                if isinstance(e, ConnectionError):
                    print(
                        f"Connection error (Attempt {retry + 1}/{max_retries + 1}): {e}"
                    )

                if retry < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Request failed.")
                    return None
            else:
                print("Request failed due to unknown error: ", e)


def footystats_seperator(stats_data: []):
    overall_stats_list = []
    home_stats_list = []
    away_stats_list = []

    for data in stats_data:
        overall_stats_list.append(data["overall_stats"])
        home_stats_list.append(data["home_stats"])
        away_stats_list.append(data["away_stats"])

    save_to_json("merged_overall_stats.json", overall_stats_list)
    save_to_json("merged_home_stats.json", home_stats_list)
    save_to_json("merged_away_stats.json", away_stats_list)


def extract_years(text):
    parts = text.split("-")
    if len(parts) == 1:
        # Only a number, treat it as start_year
        return {"start_year": int(text), "finish_year": None}
    elif len(parts) == 2:
        try:
            # Try converting both parts to int
            return {"start_year": int(parts[0]), "finish_year": int(parts[1])}
        except ValueError:
            # Second part is a word, assume no finish year
            return {"start_year": int(parts[0]), "finish_year": None}
    else:
        # More than one hyphen, invalid format
        raise ValueError(
            "Invalid format, expected hyphen separated years or single year"
        )
