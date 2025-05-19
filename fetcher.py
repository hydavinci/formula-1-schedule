"""
Fetcher for Formula 1 race calendar.
This script retrieves and outputs the F1 race schedule for the specified year.
If no data is available for the current year, it tries alternative APIs or falls back to the previous year.
"""

import requests
from datetime import datetime
import sys
import json
import logging
import concurrent.futures
import os
from functools import lru_cache
from typing import List, Dict, Tuple, Optional, Callable, Any
from bs4 import BeautifulSoup

# Configuration constants
DEFAULT_TIMEOUT = 10  # seconds
MAX_WORKERS = 5  # maximum parallel requests
CACHE_SIZE = 32  # number of results to cache
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('f1_fetcher')

# Create a shared session for all HTTP requests
session = requests.Session()
session.headers.update({'User-Agent': USER_AGENT})

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_f1_calendar_internal(year: Optional[str] = None, max_fallbacks: int = 3) -> Tuple[List[Dict], int, str]:
    """
    Fetch the Formula 1 race calendar for the specified year.
    If no year is specified, uses the current year, and falls back to previous years if needed.
    If the primary API fails, tries alternative APIs.
    
    Args:
        year (str, optional): Year to fetch calendar for. Defaults to current year.
        max_fallbacks (int, optional): Maximum number of years to fall back. Defaults to 3.
    
    Returns:
        tuple: (races, year_used, status)
            - races: List of F1 races with details
            - year_used: Year from which data was obtained
            - status: String indicating data source ("current", "fallback", "alt_api", "error")
    """
    # Convert year string to int if provided, otherwise use current year
    year_int = int(year) if year is not None else datetime.now().year
    
    original_year = year_int
    fallback_count = 0
    status = "current"
      # Try primary API first (Ergast)
    races = fetch_from_ergast_api(year_int)
    if races:
        return races, year_int, status
    
    # If primary API failed for current year, try alternative APIs before falling back
    if year_int == datetime.now().year:
        alt_races = fetch_from_alternative_apis(year_int)
        if alt_races:
            return alt_races, year_int, "alt_api"
      # If alternative APIs also failed or it's not the current year, try fallbacks
    while fallback_count < max_fallbacks:
        fallback_count += 1
        year_int = original_year - fallback_count
        print(f"Trying {year_int} from primary API...")
          # Try primary API for previous years
        races = fetch_from_ergast_api(year_int)
        if races:
            return races, year_int, "fallback"
    
    print(f"Could not find F1 calendar data for {original_year} or any of the {max_fallbacks} previous years.")
    return [], year_int, "error"

@lru_cache(maxsize=CACHE_SIZE)
def fetch_from_ergast_api(year: int) -> List[Dict]:
    """
    Fetch F1 calendar from the Ergast API.
    
    Args:
        year (int): The year to fetch data for.
        
    Returns:
        list: List of race data or empty list if failed.
    """
    url = f"http://ergast.com/api/f1/{year}.json"
    cache_file = os.path.join(CACHE_DIR, f"ergast_{year}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} F1 calendar from cache...")
                races = json.load(f)
                return races
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Requesting F1 calendar for {year} from Ergast API...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        
        if races:
            logger.info(f"Successfully retrieved {year} F1 calendar from Ergast API.")
            
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(races, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
                
            return races
        else:
            logger.info(f"No race information available for {year} from Ergast API.")
            
            # If this is the current year, it might be because the calendar isn't published yet
            if year == datetime.now().year:
                logger.info(f"The F1 calendar for {year} may not be published in Ergast API yet.")
            
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching F1 calendar from Ergast API: {e}")
        return []

def fetch_from_alternative_apis(year: int) -> List[Dict]:
    """
    Try alternative F1 calendar APIs when the primary API fails.
    
    Args:
        year (int): The year to fetch data for.
        
    Returns:
        list: List of race data formatted like Ergast API or empty list if all failed.
    """
    # List of alternative API attempts
    api_attempts = [
        fetch_from_formula1_api,
        fetch_from_sportradar_api,
        fetch_from_rapidapi_f1
    ]
    
    cache_file = os.path.join(CACHE_DIR, f"alt_api_{year}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} F1 calendar from alternative API cache...")
                races = json.load(f)
                return races
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    for api_func in api_attempts:
        races = api_func(year)
        if races:
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(races, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
                
            return races
    
    logger.warning(f"All alternative APIs failed for {year} F1 calendar data.")
    return []

def fetch_from_formula1_api(year: int) -> List[Dict]:
    """
    Fetch F1 calendar from Formula 1's official website using web scraping.
    
    Args:
        year (int): The year to fetch data for.
        
    Returns:
        list: List of race data formatted like Ergast API or empty list if failed.
    """
    url = f"https://www.formula1.com/en/racing/{year}.html"
    cache_file = os.path.join(CACHE_DIR, f"formula1_com_{year}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} F1 calendar from Formula1.com cache...")
                races = json.load(f)
                return races
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Trying to scrape F1 calendar from Formula1.com for {year}...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the race round links on the F1 website
        race_links = []
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            text = a_tag.get_text(strip=True)
            if href.startswith(f'/en/racing/{year}/') and text.startswith('ROUND '):
                race_links.append(href)
        
        if not race_links:
            logger.warning(f"Could not find race links on Formula1.com for {year}.")
            return []
        
        # Process race pages in parallel
        races = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Create a list of futures
            future_to_link = {
                executor.submit(fetch_race_details, f"https://www.formula1.com{link}", year, i): (link, i) 
                for i, link in enumerate(race_links, 1)
            }
            
            # Process completed futures as they complete
            for future in concurrent.futures.as_completed(future_to_link):
                link, i = future_to_link[future]
                try:
                    race = future.result()
                    if race:
                        races.append(race)
                except Exception as e:
                    logger.error(f"Error processing race {i}: {e}")
        
        # Sort races by date if dates are available
        races = sorted(races, key=lambda r: r.get('date', '0000-00-00'))
        
        if races:
            logger.info(f"Successfully scraped {len(races)} races from Formula1.com for {year}")
            
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(races, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
                
            return races
        else:
            logger.warning(f"No races found on Formula1.com for {year}")
            return []
    except Exception as e:
        logger.error(f"Error fetching from Formula1.com: {e}")
        return []

def fetch_race_details(url: str, year: int, round_num: int) -> Optional[Dict]:
    """
    Fetch details for a single F1 race.
    
    Args:
        url (str): The URL of the race page
        year (int): The year of the race
        round_num (int): The round number
        
    Returns:
        dict: Race details in Ergast API format or None if failed
    """
    try:
        logger.info(f"Fetching details for round {round_num}...")
        
        race_response = session.get(url, timeout=DEFAULT_TIMEOUT)
        race_response.raise_for_status()
        
        race_soup = BeautifulSoup(race_response.content, 'html.parser')
        
        # Extract race name (usually the country name, in heading)
        country_heading = race_soup.find('h1')
        country = country_heading.get_text(strip=True) if country_heading else f"Race {round_num}"
        
        # Extract the full race name (usually with sponsor)
        race_title = None
        for heading in race_soup.find_all(['h2', 'h3']):
            text = heading.get_text()
            if 'GRAND PRIX' in text:
                race_title = text.strip()
                break
        
        race_name = race_title if race_title else f"{country} Grand Prix"
        
        # Extract date information
        date_text = ""
        month_pattern = lambda s: isinstance(s, str) and any(month in s for month in MONTHS_MAP.keys())
        date_elements = race_soup.find_all(string=month_pattern)
        
        for date_elem in date_elements:
            if "-" in date_elem and len(date_elem.strip()) < 15:  # Likely a date range like "14 - 16 MAR"
                date_text = date_elem.strip()
                break
        
        # Parse the date
        race_date = parse_race_date(date_text, year) if date_text else ""
        
        # Extract circuit information
        circuit_name = ""
        circuit_info = race_soup.find(string=lambda s: isinstance(s, str) and "CIRCUIT" in s.upper())
        if circuit_info:
            circuit_name = circuit_info.strip()
        else:
            # Try to find circuit name in paragraphs
            for p in race_soup.find_all('p'):
                p_text = p.get_text().lower()
                if 'circuit' in p_text or 'track' in p_text:
                    circuit_info = p.get_text()
                    # Extract just the circuit name
                    circuit_name = circuit_info.split('at')[-1].split('in')[0].strip()
                    if circuit_name:
                        break
        
        if not circuit_name:
            circuit_name = f"{country} Circuit"
        
        # Create a race object in Ergast API format
        race = {
            "raceName": race_name,
            "Circuit": {
                "circuitName": circuit_name,
                "Location": {
                    "country": country,
                    "locality": country  # Using country as locality if specific city not found
                }
            },
            "date": race_date or f"{year}-01-01",  # Default date if not found
            "time": "14:00:00Z",  # Default time (most F1 races start around 14:00 local time)
            "round": str(round_num),  # Add round number
            "url": url  # Add source URL
        }
        
        return race
    except Exception as e:
        logger.error(f"Error parsing race page (round {round_num}): {e}")
        return None

def fetch_from_sportradar_api(year):
    """
    Fetch F1 calendar from SportRadar API (requires API key).
    
    Args:
        year (int): The year to fetch data for.
        
    Returns:
        list: List of race data formatted like Ergast API or empty list if failed.
    """
    # This would require a paid API key, so this is a placeholder
    print(f"Trying alternative API: SportRadar for {year}...")
    # In a real implementation, you would need to sign up for an API key
    return []

def fetch_from_rapidapi_f1(year):
    """
    Fetch F1 calendar from a RapidAPI F1 endpoint.
    
    Args:
        year (int): The year to fetch data for.
        
    Returns:
        list: List of race data formatted like Ergast API or empty list if failed.
    """
    # Another common source is RapidAPI which hosts various F1 APIs
    # This would also require an API key
    print(f"Trying alternative API: RapidAPI F1 for {year}...")
    
    # Example URL - would need API key and proper endpoint
    # url = "https://api-formula-1.p.rapidapi.com/races"
    
    # For now, return empty list as this is just a demonstration
    return []

# Functions to scrape data directly from Formula1.com website
def fetch_f1_website_results(year: int, round_num: str = "last") -> Dict:
    """
    Scrape race results directly from Formula1.com website.
    
    Args:
        year (int): Year of the race
        round_num (str): Round number or 'last' for the most recent race
        
    Returns:
        dict: Race results information or empty dict if failed
    """
    # Determine the URL based on the round number
    if round_num == "last":
        url = f"https://www.formula1.com/en/results/{year}/races.html"
    else:
        url = f"https://www.formula1.com/en/results/{year}/races/{round_num}.html"
    
    cache_file = os.path.join(CACHE_DIR, f"f1com_results_{year}_{round_num}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} race results from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Scraping race results for {year} from Formula1.com...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get race info
        race_info = {}
        
        # If it's the races listing page, get the most recent race
        if round_num == "last":
            race_links = soup.select('a.resultsarchive-filter-item-link')
            if race_links:
                # Get the first race link (most recent)
                latest_race_url = race_links[0].get('href')
                if latest_race_url:
                    full_url = f"https://www.formula1.com{latest_race_url}"
                    response = session.get(full_url, timeout=DEFAULT_TIMEOUT)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract race name and date
        title_elem = soup.select_one('h1.ResultsArchiveTitle')
        if title_elem:
            race_info['raceName'] = title_elem.get_text(strip=True)
        
        date_elem = soup.select_one('span.full-date')
        if date_elem:
            race_info['date'] = date_elem.get_text(strip=True)
        
        # Extract race results table
        results = []
        results_table = soup.select_one('table.resultsarchive-table')
        if results_table:
            rows = results_table.select('tbody tr')
            
            for row in rows:
                cols = row.select('td')
                if len(cols) >= 5:
                    driver_name_elem = cols[3].select_one('span.hide-for-tablet')
                    driver_surname_elem = cols[3].select_one('span.hide-for-mobile')
                    team_elem = cols[4]
                    
                    position = cols[1].get_text(strip=True)
                    driver_name = ""
                    if driver_name_elem and driver_surname_elem:
                        driver_name = f"{driver_name_elem.get_text(strip=True)} {driver_surname_elem.get_text(strip=True)}"
                    team = team_elem.get_text(strip=True) if team_elem else "Unknown Team"
                    
                    # Try to get points if available
                    points_elem = cols[-1] if len(cols) > 5 else None
                    points = points_elem.get_text(strip=True) if points_elem else "0"
                    
                    result = {
                        "position": position,
                        "Driver": {
                            "code": cols[3].select_one('span.hide-for-desktop').get_text(strip=True) if cols[3].select_one('span.hide-for-desktop') else "",
                            "givenName": driver_name_elem.get_text(strip=True) if driver_name_elem else "",
                            "familyName": driver_surname_elem.get_text(strip=True) if driver_surname_elem else "",
                            "name": driver_name
                        },
                        "Constructor": {
                            "name": team
                        },
                        "points": points
                    }
                    results.append(result)
        
        race_info['Results'] = results[:20]  # Only keep top 20 results
        
        # Get circuit information
        circuit_elem = soup.select_one('p.circuit-info')
        if circuit_elem:
            race_info['Circuit'] = {
                "circuitName": circuit_elem.get_text(strip=True),
                "Location": {
                    "country": race_info.get('raceName', '').split(' Grand Prix')[0].strip(),
                    "locality": race_info.get('raceName', '').split(' Grand Prix')[0].strip()
                }
            }
        
        # Save to cache
        if race_info.get('Results'):
            try:
                with open(cache_file, 'w') as f:
                    json.dump(race_info, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
        
        return race_info
    
    except Exception as e:
        logger.error(f"Error scraping race results from Formula1.com: {e}")
        return {}

def fetch_f1_website_driver_standings(year: int) -> List[Dict]:
    """
    Scrape driver standings directly from Formula1.com website.
    
    Args:
        year (int): Year to fetch standings for
        
    Returns:
        list: List of driver standings
    """
    url = f"https://www.formula1.com/en/results/{year}/drivers.html"
    cache_file = os.path.join(CACHE_DIR, f"f1com_drivers_{year}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} driver standings from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Scraping driver standings for {year} from Formula1.com...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract standings table
        standings = []
        standings_table = soup.select_one('table.resultsarchive-table')
        
        if standings_table:
            rows = standings_table.select('tbody tr')
            
            for row in rows:
                cols = row.select('td')
                if len(cols) >= 5:
                    position = cols[1].get_text(strip=True)
                    
                    driver_name_elem = cols[2].select_one('span.hide-for-tablet')
                    driver_surname_elem = cols[2].select_one('span.hide-for-mobile')
                    
                    driver_name = ""
                    if driver_name_elem and driver_surname_elem:
                        driver_name = f"{driver_name_elem.get_text(strip=True)} {driver_surname_elem.get_text(strip=True)}"
                    
                    nationality = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                    team = cols[4].get_text(strip=True) if len(cols) > 4 else "Unknown Team"
                    points = cols[5].get_text(strip=True) if len(cols) > 5 else "0"
                    
                    driver_standing = {
                        "position": position,
                        "points": points,
                        "Driver": {
                            "code": cols[2].select_one('span.hide-for-desktop').get_text(strip=True) if cols[2].select_one('span.hide-for-desktop') else "",
                            "givenName": driver_name_elem.get_text(strip=True) if driver_name_elem else "",
                            "familyName": driver_surname_elem.get_text(strip=True) if driver_surname_elem else "",
                            "nationality": nationality
                        },
                        "Constructors": [
                            {
                                "name": team
                            }
                        ]
                    }
                    standings.append(driver_standing)
        
        # Create standings list in Ergast format
        standings_list = {
            "season": str(year),
            "round": "latest",
            "DriverStandings": standings
        }
        
        # Save to cache
        if standings:
            try:
                with open(cache_file, 'w') as f:
                    json.dump([standings_list], f)
            except IOError as e:
                logger.warning(f"Failed to cache driver standings: {e}")
        
        return [standings_list]
    
    except Exception as e:
        logger.error(f"Error scraping driver standings from Formula1.com: {e}")
        return []

def fetch_f1_website_constructor_standings(year: int) -> List[Dict]:
    """
    Scrape constructor/team standings directly from Formula1.com website.
    
    Args:
        year (int): Year to fetch standings for
        
    Returns:
        list: List of constructor standings
    """
    url = f"https://www.formula1.com/en/results/{year}/team.html"
    cache_file = os.path.join(CACHE_DIR, f"f1com_teams_{year}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} constructor standings from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Scraping constructor standings for {year} from Formula1.com...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract standings table
        standings = []
        standings_table = soup.select_one('table.resultsarchive-table')
        
        if standings_table:
            rows = standings_table.select('tbody tr')
            
            for row in rows:
                cols = row.select('td')
                if len(cols) >= 3:
                    position = cols[1].get_text(strip=True)
                    team = cols[2].get_text(strip=True)
                    points = cols[3].get_text(strip=True) if len(cols) > 3 else "0"
                    
                    constructor_standing = {
                        "position": position,
                        "points": points,
                        "Constructor": {
                            "name": team,
                            "nationality": "Unknown"  # Formula1.com doesn't show nationality
                        }
                    }
                    standings.append(constructor_standing)
        
        # Create standings list in Ergast format
        standings_list = {
            "season": str(year),
            "round": "latest",
            "ConstructorStandings": standings
        }
        
        # Save to cache
        if standings:
            try:
                with open(cache_file, 'w') as f:
                    json.dump([standings_list], f)
            except IOError as e:
                logger.warning(f"Failed to cache constructor standings: {e}")
        
        return [standings_list]
    
    except Exception as e:
        logger.error(f"Error scraping constructor standings from Formula1.com: {e}")
        return []

# New functions for fetching race results, constructor points, and driver standings
@lru_cache(maxsize=CACHE_SIZE)
def fetch_race_results(year: int, round_num: str = "last") -> List[Dict]:
    """
    Get results for a specific race (top three finishers).
    
    Args:
        year (int): Race year
        round_num (str): Race round number, defaults to "last" (most recent completed race)
        
    Returns:
        list: Race results list, contains race information and driver results
    """
    # Try to get from Formula1.com website first
    f1_website_data = fetch_f1_website_results(year, round_num)
    if f1_website_data and f1_website_data.get('Results'):
        # Format as a list with one race to match Ergast API format
        return [f1_website_data]
    
    # Fall back to Ergast API if website scraping fails
    url = f"http://ergast.com/api/f1/{year}/{round_num}/results.json"
    cache_file = os.path.join(CACHE_DIR, f"results_{year}_{round_num}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} round {round_num} race results from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Requesting {year} round {round_num} race results from Ergast API...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        race_data = data.get('MRData', {}).get('RaceTable', {})
        races = race_data.get('Races', [])
        
        if races:
            logger.info(f"Successfully retrieved race results")
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(races, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
            
            return races
        else:
            logger.info(f"No race results available")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching race results from Ergast API: {e}")
        return []

@lru_cache(maxsize=CACHE_SIZE)
def fetch_driver_standings(year: int, round_num: str = "current") -> List[Dict]:
    """
    Get driver championship standings.
    
    Args:
        year (int): Race year
        round_num (str): Race round number, defaults to "current" (current latest standings)
        
    Returns:
        list: Driver standings list
    """
    # Try to get from Formula1.com website first (website doesn't support specific rounds)
    if round_num == "current":
        f1_website_data = fetch_f1_website_driver_standings(year)
        if f1_website_data:
            return f1_website_data
    
    # Fall back to Ergast API if website scraping fails
    url = f"http://ergast.com/api/f1/{year}/{round_num}/driverStandings.json"
    cache_file = os.path.join(CACHE_DIR, f"driver_standings_{year}_{round_num}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} driver standings from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Requesting {year} driver standings from Ergast API...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        standings_data = data.get('MRData', {}).get('StandingsTable', {})
        standings_lists = standings_data.get('StandingsLists', [])
        
        if standings_lists:
            logger.info(f"Successfully retrieved driver standings")
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(standings_lists, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
            
            return standings_lists
        else:
            logger.info(f"No driver standings available")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching driver standings from Ergast API: {e}")
        return []

@lru_cache(maxsize=CACHE_SIZE)
def fetch_constructor_standings(year: int, round_num: str = "current") -> List[Dict]:
    """
    Get team/constructor championship standings.
    
    Args:
        year (int): Race year
        round_num (str): Race round number, defaults to "current" (current latest standings)
        
    Returns:
        list: Constructor standings list
    """
    # Try to get from Formula1.com website first (website doesn't support specific rounds)
    if round_num == "current":
        f1_website_data = fetch_f1_website_constructor_standings(year)
        if f1_website_data:
            return f1_website_data
    
    # Fall back to Ergast API if website scraping fails
    url = f"http://ergast.com/api/f1/{year}/{round_num}/constructorStandings.json"
    cache_file = os.path.join(CACHE_DIR, f"constructor_standings_{year}_{round_num}.json")
    
    # Try to load from cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logger.info(f"Loading {year} constructor standings from cache...")
                data = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load from cache: {e}")
    
    try:
        logger.info(f"Requesting {year} constructor standings from Ergast API...")
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        standings_data = data.get('MRData', {}).get('StandingsTable', {})
        standings_lists = standings_data.get('StandingsLists', [])
        
        if standings_lists:
            logger.info(f"Successfully retrieved constructor standings")
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(standings_lists, f)
            except IOError as e:
                logger.warning(f"Failed to cache results: {e}")
            
            return standings_lists
        else:
            logger.info(f"No constructor standings available")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching constructor standings from Ergast API: {e}")
        return []

# Utility functions and constants
MONTHS_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", 
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08", 
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
}

def parse_race_date(date_text: str, year: int) -> str:
    """
    Parse a race date from text format to ISO format.
    
    Args:
        date_text (str): Date text like "14 - 16 MAR" or "14-16 MAR"
        year (int): The year for the date
        
    Returns:
        str: ISO format date or empty string if parsing failed
    """
    try:
        parts = date_text.split()
        if len(parts) >= 2:
            if '-' in parts[0]:
                # Format like "14-16 MAR"
                days = parts[0].split('-')
                race_day = days[-1].strip()
            else:
                # Format like "14 - 16 MAR"
                days = parts[-2].split('-')
                race_day = days[-1].strip()
            
            month_name = parts[-1]
            month = MONTHS_MAP.get(month_name[:3], "01")
            
            return f"{year}-{month}-{race_day.zfill(2)}"
    except Exception as e:
        logger.error(f"Error parsing date '{date_text}': {e}")
    
    return ""

def format_race_podium(race_results: List[Dict]) -> str:
    """
    Format race podium (top three finishers) for display.
    
    Args:
        race_results (List[Dict]): Race results
        
    Returns:
        str: Formatted podium information
    """
    if not race_results:
        return "No race results data available"
    
    race = race_results[0]
    race_name = race.get('raceName', 'Unknown Race')
    circuit = race.get('Circuit', {}).get('circuitName', 'Unknown Circuit')
    
    results = race.get('Results', [])
    if not results:
        return f"{race_name} (at {circuit}): No race results data available"
    
    # Get top three finishers
    top_three = results[:3] if len(results) >= 3 else results
    
    podium_text = f"{race_name} (at {circuit}) Podium:\n"
    for position, driver_result in enumerate(top_three, 1):
        driver = driver_result.get('Driver', {})
        constructor = driver_result.get('Constructor', {})
        
        driver_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}"
        team_name = constructor.get('name', 'Unknown Team')
        time = driver_result.get('Time', {}).get('time', 'No Time')
        
        # Get points
        points = driver_result.get('points', '0')
        
        podium_text += f"{position}. {driver_name} ({team_name}) - {points} points"
        if position < len(top_three):
            podium_text += "\n"
    
    return podium_text

def format_driver_standings(standings_lists: List[Dict]) -> str:
    """
    Format driver championship standings for display.
    
    Args:
        standings_lists (List[Dict]): Driver standings data
        
    Returns:
        str: Formatted driver standings
    """
    if not standings_lists:
        return "No driver standings data available"
    
    standings_list = standings_lists[0]
    season = standings_list.get('season', 'Unknown Season')
    round_num = standings_list.get('round', 'Unknown Round')
    
    driver_standings = standings_list.get('DriverStandings', [])
    if not driver_standings:
        return f"{season} Season Round {round_num}: No driver standings data available"
    
    result = f"{season} Season Round {round_num} - Driver Championship Standings:\n"
    result += "-" * 40 + "\n"
    
    # Show top 10 drivers
    top_drivers = driver_standings[:10] if len(driver_standings) > 10 else driver_standings
    
    for standing in top_drivers:
        position = standing.get('position', 'Unknown')
        points = standing.get('points', '0')
        driver = standing.get('Driver', {})
        driver_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}"
        constructor = standing.get('Constructors', [{}])[0] if standing.get('Constructors') else {}
        team_name = constructor.get('name', 'Unknown Team')
        
        result += f"{position}. {driver_name} - {points} points ({team_name})\n"
    
    return result

def format_constructor_standings(standings_lists: List[Dict]) -> str:
    """
    Format constructor/team championship standings for display.
    
    Args:
        standings_lists (List[Dict]): Constructor standings data
        
    Returns:
        str: Formatted constructor standings
    """
    if not standings_lists:
        return "No constructor standings data available"
    
    standings_list = standings_lists[0]
    season = standings_list.get('season', 'Unknown Season')
    round_num = standings_list.get('round', 'Unknown Round')
    
    constructor_standings = standings_list.get('ConstructorStandings', [])
    if not constructor_standings:
        return f"{season} Season Round {round_num}: No constructor standings data available"
    
    result = f"{season} Season Round {round_num} - Constructor Championship Standings:\n"
    result += "-" * 40 + "\n"
    
    for standing in constructor_standings:
        position = standing.get('position', 'Unknown')
        points = standing.get('points', '0')
        constructor = standing.get('Constructor', {})
        team_name = constructor.get('name', 'Unknown Team')
        
        result += f"{position}. {team_name} - {points} points\n"
    
    return result

def handle_special_requests(args, year: int) -> int:
    """
    Handle special requests like race results, standings, etc.
    
    Args:
        args: Command line arguments
        year (int): Year to query for
        
    Returns:
        int: Exit code, 0 means success
    """
    # Show recent race results
    if args.podium or args.all_info:
        round_to_use = args.round if args.round != "current" else "last"
        race_results = fetch_race_results(year, round_to_use)
        if race_results:
            podium_text = format_race_podium(race_results)
            print(f"\n{podium_text}\n")
        else:
            print(f"\nNo race results found for {year}\n")
    
    # Show driver standings
    if args.drivers or args.all_info:
        driver_standings = fetch_driver_standings(year, args.round)
        if driver_standings:
            standings_text = format_driver_standings(driver_standings)
            print(f"\n{standings_text}")
        else:
            print(f"\nNo driver standings found for {year} round {args.round}\n")
    
    # Show constructor standings
    if args.teams or args.all_info:
        constructor_standings = fetch_constructor_standings(year, args.round)
        if constructor_standings:
            standings_text = format_constructor_standings(constructor_standings)
            print(f"\n{standings_text}")
        else:
            print(f"\nNo constructor standings found for {year} round {args.round}\n")
    
    return 0

def format_race_info(race: Dict) -> str:
    """
    Format race information for display.
    
    Args:
        race (dict): Race information dictionary.
        
    Returns:
        str: Formatted race information.
    """
    race_name = race.get('raceName', 'Unknown')
    circuit_name = race.get('Circuit', {}).get('circuitName', 'Unknown Circuit')
    
    # Format date and time
    race_date = race.get('date', 'Unknown Date')
    raw_time = race.get('time', '')
    
    # Format time more efficiently
    if raw_time:
        race_time = raw_time.rstrip(':00Z').replace(':00Z', '')
    else:
        race_time = 'TBD'
    
    location = race.get('Circuit', {}).get('Location', {})
    country = location.get('country', 'Unknown')
    city = location.get('locality', country)  # Use country as fallback
    
    # Include weekend information if available
    first_practice = race.get('FirstPractice', {}).get('date', '')
    weekend_info = f" (Race weekend: {first_practice} - {race_date})" if first_practice else ""
        
    return f"{race_date} {race_time}: {race_name} at {circuit_name} ({city}, {country}){weekend_info}"

def display_calendar(races: List[Dict], year_used: int, status: str, args) -> None:
    """
    Display race calendar information.
    
    Args:
        races (List[Dict]): List of race information
        year_used (int): Year used for the calendar
        status (str): Data source status
        args: Command line arguments
    """
    # Get requested year
    requested_year = args.year if args.year else datetime.now().year
    
    # Show appropriate header
    if status == "fallback":
        if requested_year == datetime.now().year:
            print(f"\n⚠️ NOTE: The {requested_year} F1 calendar is not yet published in the API.")
            print(f"Showing the {year_used} Formula 1 Calendar instead:")
        else:
            print(f"\n⚠️ NOTE: No F1 calendar found for {requested_year}.")
            print(f"Showing the {year_used} Formula 1 Calendar instead:")
    elif status == "alt_api":
        print(f"\nFormula 1 {year_used} Season Calendar (retrieved from alternative source):")
    else:
        print(f"\nFormula 1 {year_used} Season Calendar:")
    
    print("-" * 50)
    
    # Get current date to mark future races
    current_date = datetime.now().date()
    
    # Display race list
    for i, race in enumerate(races, 1):
        formatted_race = format_race_info(race)
        
        # Check race date to determine if it's completed
        race_date_str = race.get('date', '')
        race_status = ""
        
        if race_date_str:
            try:
                race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
                if race_date < current_date:
                    race_status = " [Completed]"
                elif race_date == current_date:
                    race_status = " [Today]"
                else:
                    race_status = " [Upcoming]"
            except ValueError:
                pass
        
        print(f"Round {i}: {formatted_race}{race_status}")

def main():
    """Main function to fetch and display the F1 calendar."""
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Fetch Formula 1 race calendar and related information')
    parser.add_argument('year', type=int, nargs='?', default=None,
                        help='Year to fetch calendar for (default: current year)')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format instead of text')
    parser.add_argument('--no-cache', action='store_true',
                        help='Ignore cached data and fetch fresh data')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    # Additional parameters
    parser.add_argument('--podium', '--results', action='store_true',
                        help='Show the podium (top 3) for the most recent completed race')
    parser.add_argument('--drivers', '--driver-standings', action='store_true',
                        help='Show current driver championship standings')
    parser.add_argument('--teams', '--constructor-standings', action='store_true',
                        help='Show current constructor championship standings')
    parser.add_argument('--round', type=str, default='current',
                        help='Specify the round to query (e.g., 1, 2, last, current, etc.)')
    parser.add_argument('--all-info', action='store_true',
                        help='Show all information: calendar, recent race results, driver and constructor standings')
    
    args = parser.parse_args()
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Clear cache if requested
    if args.no_cache:
        try:
            for cache_file in os.listdir(CACHE_DIR):
                os.remove(os.path.join(CACHE_DIR, cache_file))
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    # Use specified year or current year
    year_to_use = args.year if args.year else datetime.now().year
    
    # Handle special requests
    show_special_info = args.podium or args.drivers or args.teams or args.all_info
    
    # If only special info is requested (not calendar), handle it separately
    if show_special_info and not args.all_info:
        return handle_special_requests(args, year_to_use)
      # Fetch calendar data
    # Convert year to string if present, otherwise pass None
    year_arg = str(args.year) if args.year is not None else None
    races, year_used, status = fetch_f1_calendar_internal(year_arg)
    
    if not races:
        requested_year = args.year if args.year else datetime.now().year
        logger.error(f"No race information found for {requested_year} or earlier years.")
        return 1
      # Output in JSON format if requested
    if args.json:
        output = {
            "year": year_used,
            "status": status,
            "races": races
        }
        # Add additional information to JSON output
        if args.podium or args.all_info:
            race_results = fetch_race_results(year_to_use, args.round if args.round != "current" else "last")
            if race_results:
                output["latest_results"] = race_results[0]
                
        if args.drivers or args.all_info:
            driver_standings = fetch_driver_standings(year_to_use, args.round)
            if driver_standings:
                output["driver_standings"] = driver_standings[0]
                
        if args.teams or args.all_info:
            constructor_standings = fetch_constructor_standings(year_to_use, args.round)
            if constructor_standings:
                output["constructor_standings"] = constructor_standings[0]
        
        print(json.dumps(output, indent=2))
        return 0
    
    # Display calendar
    display_calendar(races, year_used, status, args)
    
    # If all information is requested, continue processing
    if args.all_info:
        print("\n" + "=" * 50 + "\n")
        handle_special_requests(args, year_to_use)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())