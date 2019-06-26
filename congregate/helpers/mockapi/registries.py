class MockRegistryApi():
    def get_all_registries(self):
        '''
            Simulates a /projects/:id/registry/repositories request
        '''
        return [
            {
                "id": 192,
                "name": "10-fix-the-date-and-add-some-colour",
                "path": "adrian-demos/minimal-ruby-app/10-fix-the-date-and-add-some-colour",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/10-fix-the-date-and-add-some-colour",
                "created_at": "2019-01-15T12:56:52.187Z"
            },
            {
                "id": 378,
                "name": "11-change-message-font",
                "path": "adrian-demos/minimal-ruby-app/11-change-message-font",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/11-change-message-font",
                "created_at": "2019-04-29T08:15:35.236Z"
            },
            {
                "id": 197,
                "name": "12-fix-the-date",
                "path": "adrian-demos/minimal-ruby-app/12-fix-the-date",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/12-fix-the-date",
                "created_at": "2019-01-17T11:22:04.961Z"
            },
            {
                "id": 198,
                "name": "13-fix-the-date-and-maybe-add-some-colour",
                "path": "adrian-demos/minimal-ruby-app/13-fix-the-date-and-maybe-add-some-colour",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/13-fix-the-date-and-maybe-add-some-colour",
                "created_at": "2019-01-17T12:29:21.684Z"
            },
            {
                "id": 215,
                "name": "15-fix-date-again",
                "path": "adrian-demos/minimal-ruby-app/15-fix-date-again",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/15-fix-date-again",
                "created_at": "2019-01-23T11:55:43.778Z"
            },
            {
                "id": 218,
                "name": "16-fix-date",
                "path": "adrian-demos/minimal-ruby-app/16-fix-date",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/16-fix-date",
                "created_at": "2019-01-24T12:13:09.137Z"
            },
            {
                "id": 232,
                "name": "17-date-is-wrong",
                "path": "adrian-demos/minimal-ruby-app/17-date-is-wrong",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/17-date-is-wrong",
                "created_at": "2019-01-30T13:07:36.141Z"
            },
            {
                "id": 234,
                "name": "18-the-date-is-wrong",
                "path": "adrian-demos/minimal-ruby-app/18-the-date-is-wrong",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/18-the-date-is-wrong",
                "created_at": "2019-01-30T14:23:04.304Z"
            },
            {
                "id": 240,
                "name": "19-the-date-in-the-output-is-wrong",
                "path": "adrian-demos/minimal-ruby-app/19-the-date-in-the-output-is-wrong",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/19-the-date-in-the-output-is-wrong",
                "created_at": "2019-01-31T11:38:01.007Z"
            },
            {
                "id": 166,
                "name": "1-make-homepage-prettier",
                "path": "adrian-demos/minimal-ruby-app/1-make-homepage-prettier",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/1-make-homepage-prettier",
                "created_at": "2019-01-03T12:34:48.132Z"
            },
            {
                "id": 256,
                "name": "20-date-needs-fixing",
                "path": "adrian-demos/minimal-ruby-app/20-date-needs-fixing",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/20-date-needs-fixing",
                "created_at": "2019-02-06T11:38:55.109Z"
            },
            {
                "id": 260,
                "name": "21-fix-date-in-output-please",
                "path": "adrian-demos/minimal-ruby-app/21-fix-date-in-output-please",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/21-fix-date-in-output-please",
                "created_at": "2019-02-07T14:28:34.883Z"
            },
            {
                "id": 261,
                "name": "22-the-date-in-the-output-is-wrong",
                "path": "adrian-demos/minimal-ruby-app/22-the-date-in-the-output-is-wrong",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/22-the-date-in-the-output-is-wrong",
                "created_at": "2019-02-08T13:39:03.777Z"
            },
            {
                "id": 280,
                "name": "23-fix-the-date",
                "path": "adrian-demos/minimal-ruby-app/23-fix-the-date",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/23-fix-the-date",
                "created_at": "2019-02-22T14:35:54.650Z"
            },
            {
                "id": 326,
                "name": "24-the-date-in-web-is-wrong",
                "path": "adrian-demos/minimal-ruby-app/24-the-date-in-web-is-wrong",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/24-the-date-in-web-is-wrong",
                "created_at": "2019-03-27T15:46:36.931Z"
            },
            {
                "id": 397,
                "name": "25-fix-message",
                "path": "adrian-demos/minimal-ruby-app/25-fix-message",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/25-fix-message",
                "created_at": "2019-05-16T12:08:27.752Z"
            },
            {
                "id": 399,
                "name": "26-fix-the-month-in-the-outpu",
                "path": "adrian-demos/minimal-ruby-app/26-fix-the-month-in-the-outpu",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/26-fix-the-month-in-the-outpu",
                "created_at": "2019-05-16T15:22:28.543Z"
            },
            {
                "id": 400,
                "name": "26-fix-the-month-in-the-outpu-2",
                "path": "adrian-demos/minimal-ruby-app/26-fix-the-month-in-the-outpu-2",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/26-fix-the-month-in-the-outpu-2",
                "created_at": "2019-05-16T16:49:01.928Z"
            },
            {
                "id": 170,
                "name": "2-make-even-prettier",
                "path": "adrian-demos/minimal-ruby-app/2-make-even-prettier",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/2-make-even-prettier",
                "created_at": "2019-01-04T10:42:36.409Z"
            },
            {
                "id": 171,
                "name": "3-change-message",
                "path": "adrian-demos/minimal-ruby-app/3-change-message",
                "location": "registry.demo.i2p.online/adrian-demos/minimal-ruby-app/3-change-message",
                "created_at": "2019-01-04T12:26:14.755Z"
            }
        ]