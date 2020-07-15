# Writing Tests for Congregate

Congregate is a little bit of a challenge to test in an automated fashion. A lot of the codebase is reliant on consuming external APIs, so mocking data accordingly can be tough.

Congregate consists of varying types of tests:

- Unit tests
- Integration tests
- End to end tests

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

We are testing the output of a method based on some example input. This is about as basic as our tests get. We provide and input and we expect an output. These are the easiest tests to write.


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

Test:

```python
@mock.patch('congregate.helpers.conf.Config.group_sso_provider', new_callable=mock.PropertyMock)
def test_generate_extern_uid_no_pattern_no_ids(self, provider):
    provider.return_value = "okta"
    mock_user = self.mock_users.get_dummy_user()
    expected = None
    actual = self.users.generate_extern_uid(mock_user, None)

    self.assertEqual(expected, actual)
```

This test is utilizing the mock library's `PropertyMock` and patching functionality. Our config class is primarily filled with various property methods, so we need to use a PropertyMock to simlulate retrieving data from that class. Once the property is patched, we overload the value of the property in the following line:

`provider.return_value = "okta"`

Now when we run this test and get the property, `okta` will be the value returned.

This test is also utilizing another method of mocking we use which is our MockAPI. This is a simpler use of our MockAPI because we are using it solely for test data. We aren't actually mocking a full GET request.


### Integration Tests

There are some blurred lines between our unit tests and integration tests. The approach is very similar, but our integration tests are a bit more complex to write. We don't have a traditional approach to an integration test to actually call the endpoints we want to test, but we can still go through some of our more complicated methods utilizing multiple methods integrated together. 

### End to End Tests

Since Congregate orchestrates interactions between two SCM instances through a series of REST API calls, the best way we can test to make sure our changes are completely working is to test it against a live instance of the APIs we are consuming. This is where an end to end test comes in to play.

There is a lot involved with writing an end to end test. The following work was done for our GitLab to GitLab e2e test:

- Create a test GitLab instance with preseeded data
- Automate building out the preseeded GitLab instance as an AMI with Packer
- Set up a pipeline schedule to repeatedly build a new version of the GitLab seed AMI
- Utilize a web scraper to generate new access tokens for the test source and destination instances
- Automatically configure congregate before kicking off a full migration
- Write a series of API diff reports testing the different responses between the same API endpoints on the different instances
    - As a prerequisite, write out the framework for building a diff report between the instances
- Write a script to automatically spin up the newest version of our seeded AMI in EC2
- Write a script to automatically tear down the test AMI after the test is finished.
- Automate this entire process in a GitLab CI/CD pipeline

The hardest part about writing out end to end tests is building out the foundation for subsequent end to end tests. For example, we first set up a full end to end test for a GitLab to GitLab migration and the development process took several weeks. Months later, we integrated a new method of GitLab to GitLab migration where we would migrate a single group to an entirely new instance. This required a new end to end test, but the level of effort for this test was much lower because all it required was a new test configuration.

This process will vary from SCM to SCM we support. We use AWS for our GitLab seed image because our GitLab docker containers use ephemeral, external storage, so the data we seed would always be wiped out when we spin up a new container. We still use our GitLab docker containers as a service in our end to end test jobs because we don't need to worry about storing the data after the job is finished. It's better it just gets blown away.

With our BitBucket support, it's still a little up in the air as of writing this page, but we are currently approaching a mix between docker-compose and docker in our CI pipeline to help simplify some of this process.

With our upcoming GitHub Enterprise support, there is no docker container available for GHE so we will have to seed data to a persistent GHE instance during the test and delete the test data afterwards.

Once the infrastructure and test data can be generated automatically on command, we need to be able to automatically configure congregate to run a migration unattended. 

