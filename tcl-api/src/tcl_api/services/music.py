from tcl_api.internal.musicache import get_cache

music_cache = get_cache()


def get_note_from_aspn(aspn_note: str):
    return music_cache.get_note_by_aspn(aspn_note)
