def get_position_id(position_name: str) -> int:
    """Map API position names to database position IDs"""
    position_mapping = {
        'Goalkeeper': 1,
        'G': 1,
        'GK': 1,
        'Defender': 2,
        'D': 2,
        'DEF': 2,
        'Midfielder': 3,
        'M': 3,
        'MID': 3,
        'Attacker': 4,
        'F': 4,
        'FW': 4,
        'ATT': 4
    }
    
    # Default to Midfielder (3) if position is unknown
    return position_mapping.get(position_name, 3) 