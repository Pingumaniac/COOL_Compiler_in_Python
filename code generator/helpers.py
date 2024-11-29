# helpers.py

class LabelGenerator:
    def __init__(self):
        self.counter = 0

    def new_label(self, base):
        label = f"{base}_{self.counter}"
        self.counter += 1
        return label

class StringCache:
    def __init__(self):
        self.string_table = {}
        self.string_count = 0

    def cache_string(self, value):
        if value not in self.string_table:
            label = f"string{self.string_count}"
            self.string_table[value] = label
            self.string_count += 1
        return self.string_table[value]
