import wikipedia
import requests
from bs4 import BeautifulSoup
import re
import os
from PIL import Image
from io import BytesIO
import sys

def get_wikipedia_page_url(query: str) -> str:
    try:
        page = wikipedia.page(query)
        return page.url
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Disambiguation error. Possible options: {e.options}"
    except wikipedia.exceptions.PageError:
        return "Page not found. Please check your query."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def scrape_wikipedia_infobox_and_intro(url: str) -> dict:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        infobox = soup.find('table', {'class': 'infobox'})
        result = {"artist": None, "album": None, "year": None, "genres": None, "intro": None, "image_url": None}

        if infobox:
            image_tag = infobox.find('img')
            if image_tag and image_tag.get('src'):
                thumbnail_url = image_tag['src']
                full_image_url = re.sub(r'/thumb/(.*?)/(\d+px-.*?)$', r'/\1', thumbnail_url)
                result["image_url"] = f"https:{full_image_url}"

            for row in infobox.find_all('tr'):
                header = row.find('th')
                data = row.find('td')

                if header:
                    if "album" in header.get("class", []) or "summary" in header.get("class", []):
                        result["album"] = header.get_text(strip=True)
                        continue

                if header and data:
                    header_text = header.get_text(strip=True).lower()
                    data_text = data.get_text(strip=True)

                    if "artist" in header_text or "performer" in header_text:
                        result["artist"] = data_text
                    elif "album" in header_text or "title" in header_text:
                        result["album"] = data_text
                    elif "released" in header_text or "year" in header_text:
                        result["year"] = data_text.split('(')[0].strip()
                    elif "genre" in header_text:
                        result["genres"] = extract_genres_from_infobox(data)
        else:
            print("No infobox found on the page.")

        return result
    except Exception as e:
        print(f"An error occurred while scraping: {str(e)}")
        return {"error": f"An error occurred while scraping: {str(e)}"}

def extract_genres_from_infobox(data) -> str:
    genres = [li.get_text(strip=True) for li in data.find_all('li')] if data else []
    return ", ".join(genres) if genres else "No genres listed."

def download_image(image_url: str, filename: str) -> str:
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Save the image to the same directory as the script
        image_path = os.path.join(os.getcwd(), filename)
        with open(image_path, 'wb') as file:
            file.write(response.content)
        
        print(f"Image successfully downloaded to {image_path}")
        
        # Display the image
        image = Image.open(BytesIO(response.content))
        image.show()
        
        return image_path
    except Exception as e:
        print(f"Failed to download image: {str(e)}")
        return ""

def wikipedia_search_loop():
    while True:
        user_query = input("Enter text: (or 'QUIT_NOW' to quit): ").strip()
        if user_query.lower() == "QUIT_NOW":
            print("Bye!")
            break
        elif user_query.lower() == "REBOOT_NOW":
            print("Rebooting the script...")
            os.execv(sys.executable, ['python'] + sys.argv)

        url = get_wikipedia_page_url(user_query)
        print(f"\nURL: {url}\n=================================")

        if url.startswith("http"):
            result = scrape_wikipedia_infobox_and_intro(url)
            if "error" in result:
                print(result["error"])
            else:
                artist = result['artist'].title() if result['artist'] else "N/A"
                raw_year = re.sub(r'\[\d+\]', '', result['year'] or "")
                year_match = re.search(r'\b(\d{4})\b', raw_year)
                year = year_match.group(1) if year_match else "N/A"

                cleaned_genres = re.sub(r'\[\d+\]', '', result['genres'] or "")
                genres = "/".join(genre.strip().title() for genre in cleaned_genres.split(',')) if cleaned_genres else "N/A"

                labels = ["Artist", "Album", "Year", "Genres", "Image URL"]
                max_label_length = max(len(label) for label in labels)
                print(f"{'Artist:'.ljust(max_label_length + 7)} {artist}")
                print(f"{'Album:'.ljust(max_label_length + 7)} {result['album']}")
                print(f"{'Year:'.ljust(max_label_length + 7)} {year}")
                print(f"{'Genres:'.ljust(max_label_length + 7)} {genres}")
                print(f"{'Image URL:'.ljust(max_label_length + 7)} {result['image_url'] or 'N/A'}")

                if result['image_url']:
                    image_filename = f"{user_query.replace(' ', '_')}.jpg"
                    download_image(result['image_url'], image_filename)
        else:
            print("Invalid URL returned:", url)

        print("\n")

        
print("For best results: '{album name} album' or '{album name} {artist name} album'")
wikipedia_search_loop()
