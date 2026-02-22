# stupid hack so I can create data containers in python

class MapData(object):
    pass


def normalize_map_data(map_data):
    """Ensure map data exposes standard Nc/Wc and Np/Wp names via aliases."""
    if getattr(map_data, '_normalized', False):
        return map_data

    alias_pairs = (('NcMap', 'NpMap'), ('WcMap', 'WpMap'))

    for primary, alias in alias_pairs:
        if hasattr(map_data, primary) and not hasattr(map_data, alias):
            setattr(map_data, alias, getattr(map_data, primary))
        elif hasattr(map_data, alias) and not hasattr(map_data, primary):
            setattr(map_data, primary, getattr(map_data, alias))

    defaults = getattr(map_data, 'defaults', None)
    if isinstance(defaults, dict):
        for primary, alias in alias_pairs:
            if primary in defaults and alias not in defaults:
                defaults[alias] = defaults[primary]
            elif alias in defaults and primary not in defaults:
                defaults[primary] = defaults[alias]

    units = getattr(map_data, 'units', None)
    if isinstance(units, dict):
        for primary, alias in alias_pairs:
            if primary in units and alias not in units:
                units[alias] = units[primary]
            elif alias in units and primary not in units:
                units[primary] = units[alias]

    map_data._normalized = True
    return map_data
