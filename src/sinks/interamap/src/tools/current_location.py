from typing import Any, cast

import geocoder  # pyright: ignore[reportMissingTypeStubs]

def get_current_location() -> list[float] | None: # TODO: Only test function, not used in the final code
    """Function to get the current location using geocoder and mark it on the map."""
    try:
        # Get the current location using geocoder (based on IP)
        g = cast(Any, geocoder.ip("me"))  # pyright: ignore[reportUnknownMemberType]
        if g.ok and g.latlng:
            lat, lon = g.latlng
            return [lat, lon]
        else:
            print("Unable to determine current location.")
            return None
    except Exception as e:
        print(f"Error fetching current location: {e}")
        return None