def classify_region(x: float, field_width: float) -> int:
    if x < 0:
        raise ValueError("x-coordinate outside field")

    region_width = field_width / 16
    region = int(x // region_width) + 1
    return min(region, 16)
