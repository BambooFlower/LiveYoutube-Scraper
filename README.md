<a href="https://www.buymeacoffee.com/BambooFlower" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

# LiveYoutube Scraper
Scrape YouTube Live without API. Your last hope when you can't use the official [YouTube API](https://developers.google.com/youtube)
or Selenium. Let me know if you get any errors, YouTube is constantly changing their backend.

# Installation
`pip install YTLiveScrape`

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

Get new comments and stats

```python
comments = L.get_comments()
stats = L.get_stats()
```

To stop the script
```python
L.stop_scrape()
```
