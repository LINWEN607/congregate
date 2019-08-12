class MockVersionApi():
    '''
        Simulates a /users request with no additional parameters
    '''
    def get_11_10_version(self):
        return {
            "version": "11.10.0",
            "revision": "4e963fe"
        }

    def get_12_0_version(self):
        return {
            "version": "12.0.0",
            "revision": "4e963fe"
        }