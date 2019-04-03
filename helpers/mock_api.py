class MockApi():
    '''
        Simulates a /users request with no additional parameters
    '''
    def get_current_user(self):
        return {
            "id": 1,
            "username": "root"
        }