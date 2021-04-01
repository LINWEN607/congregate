# Writing Tests for Congregate

Congregate is a little bit of a challenge to test in an automated fashion. A lot of the codebase is reliant on consuming external APIs, so mocking data accordingly can be tough.

Congregate consists of varying types of tests:

- Unit tests:
    - Unit testing is a level of software testing where individual units/ components of a software are tested. The purpose is to validate that each unit of the software performs as designed. [(source)](http://softwaretestingfundamentals.com/unit-testing/)
- Integration tests
    - Integration testing is a level of software testing where individual units are combined and tested as a group. [(source)](http://softwaretestingfundamentals.com/integration-testing/)
- End to end tests
    - Also known as system testing, end to end testing is a level of software testing where a complete and integrated software is tested. [(source)](http://softwaretestingfundamentals.com/system-testing/)

## Quick resources

#### How do I run the test suite?

Unit and Integration Tests:

```bash
poetry run pytest \
    -m "not e2e and not e2e_setup and not e2e_setup_2" \
    --cov-config=.coveragerc \
    --cov=congregate congregate/tests/
```

End to End Tests:

NOTE: You will need to configure congregate to run an end to end test

```bash
poetry run pytest -s -m e2e congregate/tests/
```

These commands are also stored in the codebase in dev/bin/env and can also be exposed as aliases with `. dev/bin/env`

#### We currently use the following libraries for our tests:

- [unittest](https://docs.python.org/2/library/unittest.html)
    - Python's built-in unit test library
- [mock](https://cpython-test-docs.readthedocs.io/en/latest/library/unittest.mock.html)
    - Python's built-in mocking and data patching library
- [responses](https://pypi.org/project/responses/0.3.0/)
    - Open source testing library used to intercept HTTP requests and overload the data returned
- Our [built-in MockApi classes](../congregate.tests.mockapi.html) contain example responses from the APIs consume. Utilize these classes for mocking a GET request or some JSON we would use

#### We utilize the mock library through decorators. 

##### What does that mean?

The mock library allows you to use a [decorator](https://realpython.com/primer-on-python-decorators/) to override/overload default return values for specific aspects of the application we want to mock.

Congregate is configuration heavy and makes a lot of HTTP requests. Instead of relying on a configuration file and it's settings, we can mock the specific configuration values we need to use when testing methods.

The same applies for HTTP requests or anything that requires connecting to some external application. We mock our HTTP requests somewhat differently depending on the circumstance, but we can mock a method utilizing an HTTP request or the HTTP response itself. The latter requires utilizing the [responses](https://pypi.org/project/responses/0.3.0/) library.

##### How do I mock the following:

- Properties (when you need to mock our configuration getters)
    - Ex: `@mock.patch('congregate.helpers.conf.Config.<config-getter>', new_callable=mock.PropertyMock)`
- Method return values
    - Ex: `@mock.patch('congregate.helpers.api.get_count')`
- Mock class object method return values
    - Ex: `@mock.patch.object(KeysClient, "migrate_user_ssh_keys")`

#### I created multiple patches, but how do I reference them in my test?

You reference the patches as parameters in the test method (name the parameters whatever works for you), going from the bottom patch up to the top. See the example test below for the order.

#### What if I need to call the same method multiple times and return different values?

Utilize a [side_effect](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.side_effect)

Example test utilizing a side effect:

```python
@mock.patch("congregate.helpers.misc_utils.read_json_file_into_object")
@mock.patch("glob.glob")
def test_stitch_json(glob, json):
    results = MockProjectResults()
    glob.return_value = [
        'project_migration_results_2020-05-05_22:17:45.335715.json',
        'project_migration_results_2020-05-05_21:38:04.565534.json',
        'project_migration_results_2020-05-05_21:17:42.719402.json',
        'project_migration_results_2020-05-05_19:26:18.616265.json',
        'project_migration_results_2020-04-28_23:06:02.139918.json'
    ]

    json.side_effect = [
        results.get_completely_failed_results(),
        results.get_partially_successful_results(),
        results.get_successful_results_subset()
    ]

    expected = results.get_completely_successful_results()
    actual = misc.stitch_json_results(steps=2)

    assert expected == actual
```

#### My tests are failing and the diff is hard to read. What do I do?

Pytest allows for a more detailed output by adding a `-v` flag

```bash
poetry run pytest \
    -m "not e2e and not e2e_setup and not e2e_setup_2" \
    --cov-config=.coveragerc \
    --cov=congregate congregate/tests/ -v
```

This should help to pretty print any JSON diffs in the output

You can also make the output more verbose by adding more verbose flags

```bash
poetry run pytest \
    -m "not e2e and not e2e_setup and not e2e_setup_2" \
    --cov-config=.coveragerc \
    --cov=congregate congregate/tests/ -vv
```

### Unit tests

Unit tests in congregate are any test written to confirm the expected behavior of a single method and its output. A basic unit test looks like the following:

```python
def test_get_results_export_happy(self):
    results = [
        {"export1": True},
        {"export2": True},
        {"export3": True}
    ]
    self.assertEqual(mutils.get_results(results), {
                        "Total": 3, "Successful": 3})
```

We are testing the output of a method based on some example input. This is about as basic as our tests get. We provide an input and we expect an output. These are the easiest tests to write.


We have several methods with dependencies on other aspects of the codebase. For example, many methods need to check the configuration of congregate to get through a specific condition.
This requires the use of mocking data. Take this method and one of its tests for example:

Methods:

```python
def generate_extern_uid(self, user, identities):
    if self.config.group_sso_provider_pattern == "email":
        return user.get("email", None)
    else:
        return self.find_extern_uid_by_provider(identities, self.config.group_sso_provider)

def find_extern_uid_by_provider(self, identities, provider):
    if identities:
        for identity in identities:
            if provider == identity["provider"]:
                return identity["extern_uid"]
    return None
```

Test (with a line-by-line breakdown):

```python
@mock.patch('congregate.helpers.conf.Config.group_sso_provider', new_callable=mock.PropertyMock)    # group_sso_provider config is declared as a mocked and callable @Property
def test_generate_extern_uid_no_pattern_no_ids(self, provider):                                     # The provider argument will carry it's mocked return value
    provider.return_value = "okta"                                                                  # The provider return value is initialized
    mock_user = self.mock_users.get_dummy_user()                                                    # mock_user is initialized from our pool of mock user json responses
    expected = None                                                                                 # The expected return from calling self.users.generate_extern_uid is None
    actual = self.users.generate_extern_uid(mock_user, None)                                        # The actual call to self.users.generate_extern_uid is made

    self.assertEqual(expected, actual)                                                              # We assert whether the previous 2 are equal.
```

This test is utilizing the mock library's `PropertyMock` and patching functionality. Our config class is primarily filled with various property methods, so we need to use a PropertyMock to simulate retrieving data from that class. Once the property is patched, we overload the value of the property in the following line:

`provider.return_value = "okta"`

Now when we run this test and get the property, `okta` will be the value returned.

This test is also utilizing another method of mocking we use which is our MockAPI. This is a simpler use of our MockAPI because we are using it solely for test data. We aren't actually mocking a full GET request.


### Integration Tests

There are some blurred lines between our unit tests and integration tests. The approach is very similar, but our integration tests are a bit more complex to write. We don't have a traditional approach to an integration test to actually call the endpoints we want to test, but we can still go through some of our more complicated methods utilizing multiple methods integrated together. 

Our integration tests will usually utilize the responses library to mock HTTP requests. For example:

```python

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.Config.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.api.get_count')
    @mock.patch.object(KeysClient, "migrate_user_ssh_keys")
    @mock.patch.object(KeysClient, "migrate_user_gpg_keys")
    @mock.patch('congregate.migration.migrate._DRY_RUN', False)
    def test_handle_user_creation_improperly_formatted_json(self, get_gpg, get_ssh, count, parent_id, destination):
        get_ssh.return_value = True
        get_gpg.return_value = True
        count.return_value = 1
        parent_id.return_value = None
        destination.return_value = "https://gitlabdestination.com"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_user_400(), status=400)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        expected = {
            "id": None,
            "email": "jdoe@email.com"
        }
        self.assertEqual(handle_user_creation(new_user), expected)

```

Let's break this down. The first few lines activate our ability to use responses in this test. Pylint has an issue with the `@responses.activate` so it must be wrapped in the two pylint comments.
Next, we are mocking various methods, properties, and methods like we would do with a more complex unit test.  Much of the test syntax looks like a unit test, until we get to:

```python
    url_value = "https://gitlabdestination.com/api/v4/users"
    # pylint: disable=no-member
    responses.add(responses.POST, url_value,
                    json=self.mock_users.get_user_400(), status=400)
    # pylint: enable=no-member
```

We are defining the specific API endpoint we want to intercept with responses, and we get the base URL from a few lines above when we set the `destination_host` property.

Now we need to add that specific URL to responses to watch for it to be requested. Responses is expecting a POST request to `https://gitlabdestination.com/api/v4/users` and once that request is made, responses will intercept the request, return `self.mock_users.get_user_400()` and a status code of `400`

Note the additional pylint comments. Every time we use responses, we need to have pylint ignore it.

Finally, we repeat the same process for a GET request to `https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d` and then add our test assertions.

If you are testing a method making several HTTP requests, you will need to mock every request with responses.

### End to End Tests

Since Congregate orchestrates interactions between two SCM instances through a series of REST API calls, the best way we can test to make sure our changes are completely working is to test it against a live instance of the APIs we are consuming. This is where an end to end test comes in to play.

There is a lot involved with writing an end to end test. The following work was done for our GitLab to GitLab e2e test:

- Create a test GitLab instance with preseeded data
- Automate [building out](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/gitlab-seed-image) the preseeded GitLab instance as an AMI with Packer
- Set up a [pipeline schedule](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/gitlab-seed-image/-/pipeline_schedules) to repeatedly build a new version of the GitLab seed AMI
- Utilize a [web scraper](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/congregate/helpers/seed/generate_token.py) to generate new access tokens for the test source and destination instances
- Automatically [configure congregate](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/congregate/tests/migration/gitlab/test_migration_setup.py) before kicking off a full migration
- Write a series of [API diff reports](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/tree/master/congregate/migration/gitlab/diff) testing the different responses between the same API endpoints on the different instances
    - As a prerequisite, write out the [framework](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/congregate/migration/gitlab/diff/basediff.py) for building a diff report between the instances
- Write a script to [automatically spin up](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/ci/spin_up_test_vm.sh) the newest version of our seeded AMI in EC2
- Write a script to [automatically tear down](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/.gitlab-ci.yml#L132) the test AMI after the test is finished.
- Automate this entire process in a [GitLab CI/CD pipeline](https://gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate/-/blob/master/.gitlab-ci.yml#L112)

The hardest part about writing out end to end tests is building out the foundation for subsequent end to end tests. For example, we first set up a full end to end test for a GitLab to GitLab migration and the development process took several weeks. Months later, we integrated a new method of GitLab to GitLab migration where we would migrate a single group to an entirely new instance. This required a new end to end test, but the level of effort for this test was much lower because all it required was a new test configuration.

This process will vary from SCM to SCM we support. We use AWS for our GitLab seed image because our GitLab docker containers use ephemeral, external storage, so the data we seed would always be wiped out when we spin up a new container. We still use our GitLab docker containers as a service in our end to end test jobs because we don't need to worry about storing the data after the job is finished. It's better it just gets blown away.

Once the infrastructure and test data can be generated automatically on command, we need to be able to automatically configure congregate to run a migration unattended. 

#### TODO/In progress

With our BitBucket support, it's still a little up in the air as of writing this page, but we are currently approaching a mix between docker-compose and docker in our CI pipeline to help simplify some of this process.

With our upcoming GitHub Enterprise support, there is no docker container available for GHE so we will have to seed data to a persistent GHE instance during the test and delete the test data afterwards.

