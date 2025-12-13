class RegionClassifier:
    def __init__(self, field_width: float):
        self.field_width = field_width
        self.region_width = field_width / 16

    def classify(self, x: float) -> int:
        if x < 0:
            raise ValueError("x-coordinate outside field")

        region = int(x // self.region_width) + 1
        return min(region, 16)
