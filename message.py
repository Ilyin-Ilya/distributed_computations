class Message:
    def __init__(self, unique_id: int, sender: int, recipient: int, text: str):
        self.unique_id = unique_id
        self.sender = sender
        self.recipient = recipient
        self.text = text

