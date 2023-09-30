from __future__ import annotations

import json
import logging

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> RemotePlaylistMediaSource:
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    return RemotePlaylistMediaSource(hass, entry)


class RemotePlaylistMediaSource(MediaSource):
    name = "Remote Playlists"

    def __init__(self, hass: HomeAssistant, config: ConfigItem) -> None:
        super().__init__(DOMAIN)
        self.hass = hass
        self.config = config

    async def __async_read_response(self, response):
        """Reads the response, logging any json errors"""

        text = await response.text()

        if response.status >= 400:
            _LOGGER.error(f"Request failed: {response.status}: {text}")
            return None

        try:
            return json.loads(text)
        except:
            raise Exception(f"Failed to extract response json: {text}")

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        url = (
            "https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/iptv-all/vpid/"
            + item.identifier
            + "/format/json"
        )

        async with aiohttp.ClientSession() as client:
            async with client.get(url) as mediaset_response:
                mediaset = await self.__async_read_response(mediaset_response)
                (video,) = filter(lambda x: x["kind"] == "video", mediaset["media"])

                connections = filter(
                    lambda x: x["protocol"] == "https", video["connection"]
                )

                connections = filter(
                    lambda x: x["transferFormat"] == "dash", connections
                )

                connection = next(connections, None)

                _LOGGER.info(connection)

                return PlayMedia(connection["href"], video["type"])

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        print(self.config.data["playlist_url"])
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.VIDEO,
            title="BBC Channels",
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.DIRECTORY,
            children=[*await self._async_build_channels(item)],
        )

    async def _async_build_channels(
        self, item: MediaSourceItem
    ) -> list[BrowseMediaSource]:
        channel_list = [
            ("bbc_one_hd", "BBC One"),
            ("bbc_two_hd", "BBC Two"),
            ("bbc_four_hd", "BBC Four"),
            ("cbbc_hd", "CBBC"),
            ("cbeebies_hd", "CBeebies"),
            ("bbc_news24", "BBC News Channel"),
            ("bbc_parliament", "BBC Parliament"),
            ("bbc_alba", "Alba"),
            ("s4cpbs", "S4C"),
            ("bbc_one_london", "BBC One London"),
            ("bbc_one_scotland_hd", "BBC One Scotland"),
            ("bbc_one_northern_ireland_hd", "BBC One Northern Ireland"),
            ("bbc_one_wales_hd", "BBC One Wales"),
            ("bbc_two_scotland", "BBC Two Scotland"),
            ("bbc_two_northern_ireland_digital", "BBC Two Northern Ireland"),
            ("bbc_two_wales_digital", "BBC Two Wales"),
            (
                "bbc_two_england",
                "BBC Two England",
            ),
            (
                "bbc_one_cambridge",
                "BBC One Cambridge",
            ),
            (
                "bbc_one_channel_islands",
                "BBC One Channel Islands",
            ),
            (
                "bbc_one_east",
                "BBC One East",
            ),
            (
                "bbc_one_east_midlands",
                "BBC One East Midlands",
            ),
            (
                "bbc_one_east_yorkshire",
                "BBC One East Yorkshire",
            ),
            (
                "bbc_one_north_east",
                "BBC One North East",
            ),
            (
                "bbc_one_north_west",
                "BBC One North West",
            ),
            (
                "bbc_one_oxford",
                "BBC One Oxford",
            ),
            (
                "bbc_one_south",
                "BBC One South",
            ),
            (
                "bbc_one_south_east",
                "BBC One South East",
            ),
            (
                "bbc_one_west",
                "BBC One West",
            ),
            (
                "bbc_one_west_midlands",
                "BBC One West Midlands",
            ),
            (
                "bbc_one_yorks",
                "BBC One Yorks",
            ),
        ]

        sources = []

        for identifier, name in channel_list:
            sources.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=identifier,
                    media_class=MediaClass.CHANNEL,
                    media_content_type=MediaType.VIDEO,
                    title=name,
                    can_play=True,
                    can_expand=False,
                )
            )

        return sources
