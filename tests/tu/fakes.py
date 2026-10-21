class FakeHistory:
    def __init__(self):
        self.requests = []
        self.documents = []
        self.responses = []
        self.errors = []

    def check_available(self):
        pass

    def record_request(self, received_at, content):
        self.requests.append((received_at, content))
        return len(self.requests)

    def record_documents(self, request_id, paths):
        self.documents.append((request_id, paths))

    def record_error(self, request_id, tool, reason):
        self.errors.append((request_id, tool, reason))

    def record_response(self, request_id, status_code):
        self.responses.append((request_id, status_code))


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def notify(self, error_log, procedure):
        self.sent.append((error_log, procedure))
