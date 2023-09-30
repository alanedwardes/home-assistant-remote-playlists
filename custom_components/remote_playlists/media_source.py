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
from .m3u_parser import M3uParser

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> RemotePlaylistMediaSource:
    entries = hass.config_entries.async_entries(DOMAIN)
    entry = entries[0]
    return RemotePlaylistMediaSource(hass, entry)


class RemotePlaylistMediaSource(MediaSource):
    name = "Remote Playlist"

    def __init__(self, hass: HomeAssistant, config: ConfigItem) -> None:
        super().__init__(DOMAIN)
        self.hass = hass
        self.config = config
        self.name = self.config.data["title"]

    async def async_resolve_playlist(self, playlist_url) -> str:
        async with aiohttp.ClientSession() as client:
            async with client.get(playlist_url) as playlist_response:
                return await playlist_response.text()

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.VIDEO,
            title=self.config.data["title"],
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.DIRECTORY,
            children=[*await self._async_build_channels(item)],
        )

    async def _async_build_channels(
        self, item: MediaSourceItem
    ) -> list[BrowseMediaSource]:
        playlist_text = await self.async_resolve_playlist(
            self.config.data["playlist_url"]
        )

        parser = M3uParser()
        await parser.parse_m3u_content(playlist_text)
        playlist = parser.get_list()

        sources = []

        for playlist_item in playlist:
            sources.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=playlist_item["url"],
                    media_class=MediaClass.CHANNEL,
                    media_content_type=MediaType.VIDEO,
                    title=playlist_item["name"],
                    can_play=True,
                    can_expand=False,
                )
            )

        return sources

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        return PlayMedia(item.identifier, "video/mp4")
