import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict, Any, List, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common headers for all requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_and_parse(url: str, parser_func: Callable, error_context: str) -> Dict[str, Any]:
    """
    Common function to fetch data from URL and parse it with the provided parser function.
    
    Args:
        url: URL to fetch data from
        parser_func: Function to parse the BeautifulSoup object
        error_context: Context for error messages
        
    Returns:
        Dict[str, Any]: Parsed data or error information
    """
    logger.info(f"Fetching data from {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        return parser_func(soup)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {error_context}: {e}")
        return {"error": str(e), error_context: []}


def parse_standings_table(soup: BeautifulSoup, year: str, url: str, entity_type: str, row_parser: Callable) -> Dict[str, Any]:
    """
    Generic function to parse standings data from a table.
    
    Args:
        soup: BeautifulSoup object of the page
        year: Year for the standings
        url: Source URL
        entity_type: Type of entities (e.g., "teams" or "drivers")
        row_parser: Function to parse each row in the table
        
    Returns:
        Dict[str, Any]: Parsed standings data
    """
    entities = []
    table = soup.find("table")
    
    if table and table.find("tbody"):
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            entity = row_parser(row)
            if entity:
                entities.append(entity)
                
        return {
            "year": year,
            "source": url,
            entity_type: entities,
            f"total_{entity_type}": len(entities)
        }
    else:
        logger.warning(f"No {entity_type} standings table found on the page")
        return {
            "year": year,
            "source": url,
            "error": f"No {entity_type} standings table found",
            entity_type: [],
            f"total_{entity_type}": 0
        }


def extract_race_info(link: BeautifulSoup, year: str) -> Dict[str, Any]:
    """
    Extract race information from a link element.
    
    Args:
        link: BeautifulSoup link element
        year: Calendar year
        
    Returns:
        Dict[str, Any]: Race information
    """
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
        # Prettify the race slug to get a decent name
        race_info["name"] = " ".join(
            word.capitalize() for word in race_slug.split("-")
        )
        
        # Extract available info from parent elements
        parent_div = link.find_parent("div")
        if parent_div:
            # Try to find date info
            date_elem = parent_div.select_one(
                ".f1-race-hub--date, .date-container, .race-date"
            )
            if date_elem:
                race_info["date"] = date_elem.text.strip()
                
            # Try to find location info
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
    
    return race_info


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

    def parse_race_calendar(soup: BeautifulSoup) -> Dict[str, Any]:
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
        
        # Process each round link
        for link in round_links:
            try:
                race_info = extract_race_info(link, year)
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

    return fetch_and_parse(url, parse_race_calendar, "race calendar")


def fetch_team_standings(year: str) -> Dict[str, Any]:
    """
    Fetches the Formula 1 team standings for a specified year.

    Args:
        year (str): The year for which to fetch the F1 team standings

    Returns:
        Dict[str, Any]: F1 team standings information for the specified year
    """
    url = f"https://www.formula1.com/en/results/{year}/team"
    logger.info(f"Fetching F1 team standings for {year} from {url}")

    def parse_team_standings(soup: BeautifulSoup) -> Dict[str, Any]:
        def parse_team_row(row: BeautifulSoup) -> Dict[str, str]:
            cells = row.find_all("td")
            if len(cells) >= 3:  # We need at least position, team name, and points
                position = cells[0].text.strip()
                team_name = cells[1].text.strip()
                points = cells[2].text.strip()
                
                return {
                    "position": position,
                    "name": team_name,
                    "points": points
                }
            return {}

        return parse_standings_table(soup, year, url, "teams", parse_team_row)

    return fetch_and_parse(url, parse_team_standings, "team standings")


def fetch_driver_standings(year: str) -> Dict[str, Any]:
    """
    Fetches the Formula 1 driver standings for a specified year.

    Args:
        year (str): The year for which to fetch the F1 driver standings

    Returns:
        Dict[str, Any]: F1 driver standings information for the specified year
    """
    url = f"https://www.formula1.com/en/results/{year}/drivers"
    logger.info(f"Fetching F1 driver standings for {year} from {url}")

    def parse_driver_standings(soup: BeautifulSoup) -> Dict[str, Any]:
        def parse_driver_row(row: BeautifulSoup) -> Dict[str, str]:
            cells = row.find_all("td")
            if len(cells) >= 5:  # We need at least position, driver, nationality, car, and points
                position = cells[0].text.strip()
                
                # Process driver name and code
                driver_text = cells[1].text.strip()
                # Typically the format is "FirstName LastNameCOD"
                # Try to extract the three-letter driver code
                if len(driver_text) >= 3:
                    driver_code = driver_text[-3:]
                    driver_name = driver_text[:-3].strip().replace('\xa0', ' ')
                else:
                    driver_name = driver_text
                    driver_code = ""
                
                nationality = cells[2].text.strip()
                team = cells[3].text.strip()
                points = cells[4].text.strip()
                
                return {
                    "position": position,
                    "name": driver_name,
                    "code": driver_code,
                    "nationality": nationality,
                    "team": team,
                    "points": points
                }
            return {}

        return parse_standings_table(soup, year, url, "drivers", parse_driver_row)

    return fetch_and_parse(url, parse_driver_standings, "driver standings")


def fetch_race_results(year: str) -> Dict[str, Any]:
    """
    Fetches the Formula 1 race results for a specified year.

    Args:
        year (str): The year for which to fetch the F1 race results

    Returns:
        Dict[str, Any]: F1 race results information for the specified year
    """
    url = f"https://www.formula1.com/en/results/{year}/races"
    logger.info(f"Fetching F1 race results for {year} from {url}")

    def parse_race_results(soup: BeautifulSoup) -> Dict[str, Any]:
        races = []
        table = soup.find("table")
        
        if table and table.find("tbody"):
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                race_info = {}
                cells = row.find_all("td")
                
                if len(cells) >= 5:  # We need at least grand prix, date, winner, car, and laps
                    # Get Grand Prix info
                    gp_cell = cells[0]
                    gp_link = gp_cell.find("a")
                    
                    if gp_link:
                        race_info["name"] = gp_link.text.strip()
                        href = gp_link.get("href", "")
                        race_info["url"] = f"https://www.formula1.com{href}" if href else ""
                    else:
                        race_info["name"] = gp_cell.text.strip()
                    
                    # Get date
                    race_info["date"] = cells[1].text.strip()
                    
                    # Get winner
                    winner_cell = cells[2]
                    winner_link = winner_cell.find("a")
                    if winner_link:
                        winner_name = winner_link.text.strip()
                        # Clean up the driver code format if present
                        if len(winner_name) >= 3:
                            driver_code = winner_name[-3:]
                            driver_name = winner_name[:-3].strip().replace('\xa0', ' ')
                            race_info["winner_name"] = driver_name
                            race_info["winner_code"] = driver_code
                        else:
                            race_info["winner_name"] = winner_name
                    else:
                        race_info["winner_name"] = winner_cell.text.strip()
                    
                    # Get car/team
                    race_info["winner_car"] = cells[3].text.strip()
                    
                    # Get laps
                    race_info["laps"] = cells[4].text.strip()
                    
                    # Get time if available
                    if len(cells) > 5:
                        race_info["time"] = cells[5].text.strip()
                    
                    races.append(race_info)

        return {
            "year": year,
            "source": url,
            "races": races,
            "total_races": len(races),
        }

    return fetch_and_parse(url, parse_race_results, "race results")


if __name__ == "__main__":
    # Test the functions
    import json
    import sys
    
    year = sys.argv[1] if len(sys.argv) > 1 else "2025"
    
    # Unified test function
    def test_and_print(func, name):
        print(f"\n{name}:")
        result = func(year)
        print(json.dumps(result, indent=2))

    # Run all tests    
    test_and_print(fetch_race_calendar, "Race Calendar")
    test_and_print(fetch_team_standings, "Team Standings")
    test_and_print(fetch_driver_standings, "Driver Standings")
    test_and_print(fetch_race_results, "Race Results")
