class MockUsersApi():
    '''
        Simulates a /users request with no additional parameters
    '''
    def get_current_user(self):
        return {
            "id": 1,
            "username": "root",
            "name": "John Smith",
            "state": "active",
            "avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",
            "web_url": "http://localhost:3000/john_smith"
        }