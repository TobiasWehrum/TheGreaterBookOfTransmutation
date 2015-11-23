import random


# Based on https://gist.github.com/agiliq/131679
class Markov:
    def __init__(self, length):
        super(Markov, self).__init__()
        self.length = length
        self.database = {}
        self.tuple_array_cache = list(range(self.length))
        self.inputs = []

    def add(self, input_array):
        input_array_length = len(input_array)
        for i in range(-self.length, input_array_length - self.length + 1):
            for offset in range(self.length):
                if i + offset >= 0:
                    self.tuple_array_cache[offset] = input_array[i + offset]
                else:
                    self.tuple_array_cache[offset] = 0

            key = tuple(self.tuple_array_cache)
            if i + self.length >= input_array_length:
                result = 0
            else:
                result = input_array[i + self.length]

            if key in self.database:
                self.database[key].append(result)
            else:
                self.database[key] = [ result ]

    def generate(self):
        array = [0] * self.length
        while True:
            seed = tuple(array[-self.length:])
            result = random.choice(self.database[seed])
            if result == 0:
                break
            else:
                array.append(result)

        return array[self.length:]
