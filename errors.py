class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

class PasswordError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

class RegisterError(Exception):
    def __init__(self, error, status_code=400):
        self.error = error
        self.status_code = status_code