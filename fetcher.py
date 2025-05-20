import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_race_calendar(year: str) -> Dict[str, Any]:
    """
    Fetches the Formula 1 race calendar for a specified year.

    Args:
        year (str): The year for which to fetch the F1 calendar

    Returns:
        Dict[str, Any]: F1 calendar information for the specified year
    """
    url = f"https://www.formula1.com/en/racing/{year}.html"
    logger.info(f"Fetching F1 calendar for {year} from {url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract race information
        races = []

        # Look for round links in the page
        round_links = soup.find_all(
            "a", href=re.compile(f"/en/racing/{year}/[a-zA-Z-]+")
        )

        if not round_links:
            logger.warning(
                "No race round links found. The website structure might have changed."
            )

        # Process each round link - but avoid individual HTTP requests to speed up
        for link in round_links:
            try:
                race_info = {}

                # Get the race name from the link text or URL
                href = link.get("href", "")
                race_slug = href.split("/")[-1] if href else ""

                # Extract round number from text like "ROUND 1"
                round_text = link.text.strip()
                round_match = re.search(r"ROUND\s+(\d+)", round_text, re.IGNORECASE)
                round_number = round_match.group(1) if round_match else None

                if race_slug == "pre-season-testing":
                    race_info["name"] = "Pre-Season Testing"
                    race_info["is_testing"] = True
                else:
                    # Instead of visiting each race page, extract what we can from the main page
                    # Prettify the race slug to get a decent name
                    race_info["name"] = " ".join(
                        word.capitalize() for word in race_slug.split("-")
                    )

                    # Extract any available info from the link or its parent elements
                    parent_div = link.find_parent("div")
                    if parent_div:
                        # Try to find date info in nearby siblings or children
                        date_elem = parent_div.select_one(
                            ".f1-race-hub--date, .date-container, .race-date"
                        )
                        if date_elem:
                            race_info["date"] = date_elem.text.strip()

                        # Try to find location info in nearby siblings or children
                        location_elem = parent_div.select_one(
                            ".f1-race-hub--location, .location-container"
                        )
                        if location_elem:
                            race_info["location"] = location_elem.text.strip()

                # Add round number if found
                if round_number:
                    race_info["round"] = round_number

                # Add the race URL
                race_info["url"] = f"https://www.formula1.com{href}"

                races.append(race_info)

            except Exception as e:
                logger.error(f"Error extracting race information: {e}")

        # Sort races by round number if available
        sorted_races = sorted(
            races, key=lambda x: int(x.get("round", "999")) if x.get("round") else 999
        )

        return {
            "year": year,
            "source": url,
            "races": sorted_races,
            "total_races": len(sorted_races),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return {"year": year, "error": str(e), "races": [], "total_races": 0}


if __name__ == "__main__":
    # Test the function
    import json

    calendar = fetch_race_calendar("2025")
    print(json.dumps(calendar, indent=2))
