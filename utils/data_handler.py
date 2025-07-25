import json

class DataHandler:
    def __init__(self, data_file):
        self.data_file = data_file
        self.message_counts = self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get('message_counts', {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump({'message_counts': self.message_counts}, f, indent=4)