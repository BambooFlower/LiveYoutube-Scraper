# LiveYoutube Scraper
Scrape YouTube Live without API. Your last hope when you can't use the official [YouTube API](https://developers.google.com/youtube)
or Selenium. Let me know if you get any errors, YouTube is constantly changing their backend.

# Installation
`pip install -i https://test.pypi.org/simple/ YTLiveScrape`

# Example

```python
from YTLiveScrape.live_chat_worker import LiveMachine

livestream_id = '3GgSphuyBiY'  # from e.g. https://www.youtube.com/watch?v=3GgSphuyBiY

L = LiveMachine(livestream_id)

# Start stats loop
L.request_stats()
# Start comments loop
L.request_comments()
```

Script will start "watching" the stream. To get all of the comments and stats so far 

```python
all_comments = L.get_comments()
all_stats = L.get_stats()
```

To stop the script
```python
L.stop = True
```