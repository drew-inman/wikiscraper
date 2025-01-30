import wikipedia
import requests
from bs4 import BeautifulSoup

def search_wikipedia_album(query):
    try:
        page = wikipedia.page(query)
        return page.url
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Disambiguation error. Possible options: {e.options}"
    except wikipedia.exceptions.PageError:
        return "Page not found. Please check your query."
    except Exception as e:
        return f"An error occurred: {str(e)}"


def get_wikipedia_page_content(page_url):
    response = requests.get(page_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return None


def extract_album_metadata(soup):
    metadata = {}

    # Extract infobox
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return None  # No infobox found

    # Album name (header)
    metadata['album_name'] = infobox.find('th', class_='infobox-above summary album').text.strip()

    # Iterate over rows to find key info
    for row in infobox.find_all('tr'):
        header = row.find('th', class_='infobox-label')
        value = row.find('td', class_='infobox-data')
        
        if not header or not value:
            continue

        key = header.text.strip().lower()
        if "artist" in key:
            metadata['artist_name'] = value.text.strip()
        elif "genre" in key:
            metadata['genres'] = [g.text.strip() for g in value.find_all('a')]
        elif "released" in key:
            metadata['release_date'] = value.text.strip()
        elif "cover" in key or "image" in key:
            image = value.find('img')
            if image:
                metadata['album_art_url'] = "https:" + image['src']

    return metadata


def extract_tracklist(soup):
    tracklist = []

    # Look for the "Track listing" section header
    track_section = soup.find('span', {'id': 'Track_listing'})
    if not track_section:
        return tracklist

    # The tracklist table usually follows the header
    table = track_section.find_next('table', class_='tracklist')
    if not table:
        return tracklist

    # Extract track names
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            track_name = cells[0].text.strip()  # First column usually has the track name
            tracklist.append(track_name)

    return tracklist


def get_album_metadata(query):
    # Search and fetch page
    page_url = search_wikipedia_album(query)
    if not page_url:
        return {"error": "Album page not found on Wikipedia"}

    soup = get_wikipedia_page_content(page_url)
    if not soup:
        return {"error": "Failed to retrieve Wikipedia page content"}

    # Extract metadata and tracklist
    metadata = extract_album_metadata(soup)
    if not metadata:
        return {"error": "Failed to extract album metadata"}

    metadata['tracklist'] = extract_tracklist(soup)

    return metadata


# Example usage
album_data = get_album_metadata("Eighteen Visions album")
print(album_data)
