from pathlib import Path
from json import loads, dumps
from typing import Dict, List
from datetime import datetime

from tidalapi import Session, Config, Quality, VideoQuality
from tidalapi.artist import Artist
from tidalapi.user import Favorites


class Client:
    def __init__(self, key: Dict) -> None:
        """Initialize client"""
        self.key = key
        self.tidal_key = self.key.get("tidal")

        self.tidal_config = Config(
            quality=Quality.lossless, video_quality=VideoQuality.low
        )

        self.tidal = Session(self.tidal_config)
        if "token_type" in self.tidal_key:
            self.tidal.load_oauth_session(
                self.tidal_key.get("token_type"),
                self.tidal_key.get("access_token"),
                self.tidal_key.get("refresh_token"),
                datetime.fromisoformat(self.tidal_key.get("expiry_time")),
            )

        if not self.tidal.check_login():
            print("Not logged in, trying Tidal OAUTH")
            self.tidal.login_oauth_simple()
        else:
            print("Logged in to Tidal")

        assert self.tidal.check_login(), "Login to tidal failed!"

        self.save_key()

    def save_key(self) -> None:
        """Save the key file"""
        self.key["tidal"]["token_type"] = self.tidal.token_type
        self.key["tidal"]["access_token"] = self.tidal.access_token
        self.key["tidal"]["refresh_token"] = self.tidal.refresh_token
        self.key["tidal"]["expiry_time"] = self.tidal.expiry_time.isoformat()

        Path("./key.json").write_text(dumps(self.key))

    def get_lastfm_artists(self) -> List[str]:
        """Get list of lastfm artists"""
        template = "https://www.last.fm/user/{USER}/library/artists?page={PAGE}"
        user = input("Last.FM Username: ")

        favorites = Favorites(self.tidal, self.tidal.user.id)

        pages = []
        page_id = 1
        while True:
            url = template.format(USER=user, PAGE=page_id)
            res = get(url)

            if res.headers.get("X-PJAX-URL") != url or page_id > 1000:
                break

            pages.append(res)

        artists = []

        for page in pages:
            soup = BeautifulSoup(page.content)
            for td in soup.find_all("td", {"class": "chartlist-name"})
                artists.append(td.get_text().strip())

        for artist in artists:
            try:
                result = self.tidal.search(artist, models=[Artist], limit=5)
                if "top_hit" in result and result["top_hit"]:
                    top_hit = result["top_hit"]
                    favorites.add_artist(top_hit.id)
            except:
                print(f"unable to favorite artist '{artist}'")



if __name__ == "__main__":
    keyfile = Path("./key.json")
    key = loads(keyfile.read_text())
    c = Client(key)
    artists = c.get_lastfm_artists()
