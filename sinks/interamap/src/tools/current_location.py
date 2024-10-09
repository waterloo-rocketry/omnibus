import geocoder

def get_current_location(): # TODO: Only test function, not used in the final code
    """Function to get the current location using geocoder and mark it on the map."""
    try:
        # Get the current location using geocoder (based on IP)
        g = geocoder.ip("me")
        if g.ok:
            lat, lon = g.latlng
            return [lat, lon]
        else:
            print("Unable to determine current location.")
            return None
    except Exception as e:
        print(f"Error fetching current location: {e}")
        return None