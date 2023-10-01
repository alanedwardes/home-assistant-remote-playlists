from __future__ import annotations

import logging

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> RemotePlaylistMediaSource:
    return RemotePlaylistMediaSource(hass)


class RemotePlaylistMediaSource(MediaSource):
    name = "Remote Playlists"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.VIDEO,
            title=self.name,
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.DIRECTORY,
            children=[*await self._async_remote_playlists(item)],
        )

    async def _async_remote_playlists(
        self, item: MediaSourceItem
    ) -> list[BrowseMediaSource]:
        sources = []

        for config in self.hass.config_entries.async_entries(DOMAIN):
            if config.disabled_by is None:
                sources.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=config.entry_id,
                        media_class=MediaClass.CHANNEL,
                        media_content_type=MediaType.VIDEO,
                        title=config.title,
                        thumbnail=config.data.get("icon_url"),
                        can_play=True,
                        can_expand=False,
                    )
                )

        return sources

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        for config in self.hass.config_entries.async_entries(DOMAIN):
            if config.entry_id == item.identifier:
                return PlayMedia(config.data["playlist_url"], config.data["mime_type"])
