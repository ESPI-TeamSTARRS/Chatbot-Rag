class FakeHistory:
    def __init__(self):
        self.requests = []
        self.documents = []

    def record_request(self, received_at, content):
        self.requests.append((received_at, content))
        return len(self.requests)

    def record_documents(self, request_id, paths):
        self.documents.append((request_id, paths))
