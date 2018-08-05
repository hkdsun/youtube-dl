from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    str_to_int,
    urlencode_postdata,
)


class RadioJavanBaseIE(InfoExtractor):
    def _real_extract(self, url):
        entry_id = self._match_id(url)

        webpage = self._download_webpage(url, entry_id)

        download_host = self._get_download_host(url, entry_id)

        formats = self.get_formats(webpage, download_host)
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="date_added">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        return {
            'id': entry_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }

    def _get_download_host(self, url, entry_id):
        json_payload = self._download_webpage(
            self._HOST_TRACKER_URL,
            entry_id,
            data=urlencode_postdata({'id': entry_id}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url,
            }
        )

        return json.loads(json_payload)['host']


class RadioJavanVideoIE(RadioJavanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/videos/video/(?P<id>[^/]+)/?'
    _HOST_TRACKER_URL = 'https://www.radiojavan.com/videos/video_host'
    _TEST = {
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - Ashoobam',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20150215',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    }

    def get_formats(self, webpage, download_host):
        return [{
            'url': '%s/%s' % (download_host, video_path),
            'format_id': '%sp' % height,
            'height': int(height),
        } for height, video_path in re.findall(r"RJ\.video(\d+)p\s*=\s*'/?([^']+)'", webpage)]


class RadioJavanMp3IE(RadioJavanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/mp3s/mp3/(?P<id>[^/?]+)/?'
    _HOST_TRACKER_URL = 'https://www.radiojavan.com/mp3s/mp3_host'
    _TEST = {
        'url': 'https://www.radiojavan.com/mp3s/mp3/Mazyar-Fallahi-Baran-Fallahi-Begoo-Boro',
        'md5': '9601a5a94ced3a2f772f8d18170a8920',
        'info_dict': {
            'id': 'Mazyar-Fallahi-Baran-Fallahi-Begoo-Boro',
            'ext': 'mp3',
            'title': 'Mazyar Fallahi & Baran Fallahi - Begoo Boro',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20180729',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    }

    def get_formats(self, webpage, download_host):
        mp3_path = re.findall(r"RJ\.currentMP3Url\s*=\s*'/?([^']+)'", webpage)[0]
        return [{'url': '%s/media/%s.mp3' % (download_host, mp3_path)}]


class RadioJavanPlaylistBaseIE(RadioJavanBaseIE):
    def _extract_entries(self, webpage, entry_key="next"):
        entries_json_re = r'RJ.relatedMP3\s*=\s*(.*)\s*;'
        entries_json = json.loads(re.search(entries_json_re, webpage).group(1))

        entries = []
        for e in entries_json:
            entry_id = e[entry_key]
            entry = self.url_result("https://www.radiojavan.com/mp3s/mp3/%s" % entry_id)
            entries.append(entry)

        return entries


class RadioJavanPlaylistIE(RadioJavanPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/playlists/playlist/mp3/(?P<id>[^/?]+)/?'
    _TEST = {
        'url': 'https://www.radiojavan.com/playlists/playlist/mp3/854b87855624',
        'info_dict': {
            'id': '854b87855624',
            'title': '\'Today\'s Top Hits\' MP3 Playlist',
        },
        'playlist_mincount': 30,
    }

    def _real_extract(self, url):
        id = self._match_id(url)

        playlist_page = self._download_webpage(url, id)
        title = self._og_search_title(playlist_page)

        player_url = "https://www.radiojavan.com/mp3s/playlist_start?id=%s" % id
        player_page = self._download_webpage(player_url, id)

        entries = self._extract_entries(player_page)

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': id,
            'title': title,
        }


class RadioJavanAlbumIE(RadioJavanPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/mp3s/album/(?P<id>[^/?]+)/?'
    _TEST = {
        'url': 'https://www.radiojavan.com/mp3s/album/TM-Bax-Selsele?index=1',
        'info_dict': {
            'id': 'TM-Bax-Selsele',
            'title': 'TM Bax - Selsele',
        },
        'playlist_mincount': 9,
    }

    def _real_extract(self, url):
        id = self._match_id(url)
        player_page = self._download_webpage(url, id)

        title = self._og_search_title(player_page)
        entries = self._extract_entries(player_page, entry_key="mp3")

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': id,
            'title': title,
        }
