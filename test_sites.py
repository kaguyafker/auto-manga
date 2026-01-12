import asyncio
import os

# Fix Pyrogram import crash: ensure event loop exists
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Set dummy env vars to pass Config validation
os.environ["USER_ID"] = "12345"
os.environ["API_ID"] = "12345"
os.environ["CHECK_INTERVAL"] = "300"
os.environ["BOT_TOKEN"] = "dummy"
os.environ["API_HASH"] = "dummy"
os.environ["DB_NAME"] = "dummy"
os.environ["DB_URL"] = "dummy"

from config import Config
from Plugins.Sites.mangadex import MangaDexAPI
from Plugins.Sites.mangakakalot import MangakakalotAPI
from Plugins.Sites.mangaforest import MangaForestAPI
from Plugins.Sites.allmanga import AllMangaAPI

async def test_sites():
    query = "One Piece"
    print(f"Testing Search for: '{query}'\n")

    sites = [
        ("MangaDex", MangaDexAPI),
        ("Mangakakalot", MangakakalotAPI),
        ("MangaForest", MangaForestAPI),
        #("AllManga", AllMangaAPI) 
    ]

    for name, api_cls in sites:
        print(f"--- Testing {name} ---")
        try:
            async with api_cls(Config) as api:
                results = await api.search_manga(query)
                if results:
                    print(f"SUCCESS: Found {len(results)} results")
                    print(f"   First: {results[0].get('title')} ({results[0].get('id')})")
                else:
                    print(f"FAILURE: No results found")
        except Exception as e:
            print(f"ERROR: {e}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(test_sites())
