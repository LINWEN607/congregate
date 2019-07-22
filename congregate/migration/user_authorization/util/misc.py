from datetime import datetime
import inspect
import time
import boto3
import os
import re


def get_time_stamp():
    now = datetime.now() #+ timedelta(hours=7)
    time_stamp = now.strftime('%m%d%y_%H%M')
    return time_stamp


def debug_print(var_name, var_val):
    # function_name = inspect.stack()[0][3]
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    line_number = caller.lineno
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    caller_function = calframe[1][3]
    file_name = caller.filename.split('/')[-1]
    text = "In function {} in file {} at line number {}. {} = {}".format(caller_function, file_name, line_number, var_name, var_val)
    print(text)


def stable_retry(function, ExceptionType=Exception, tries=5, delay=1, backoff=1.20):
    def f_retry(*args, **kwargs):
        mtries, mdelay = tries, delay
        while mtries > 1:
            try:
                return function(*args, **kwargs)
            except ExceptionType, e:
                time.sleep(mdelay)
                mtries -= 1
                mdelay *= backoff
        return function(*args, **kwargs)

    return f_retry


def move_to_s3(local_file_key, s3_file_key, s3_bucket_name):
    s3 = boto3.client('s3')
    s3.upload_file(local_file_key, s3_bucket_name, s3_file_key)


def get_log_s3_key(repo_name, build_user_id):
    timestamp = get_time_stamp()
    return "{}_{}_{}.log".format(build_user_id, repo_name, timestamp)


def get_env_user_attributes():
    env_user_attributes = {}
    attribute_pairs = [
        ('FirstName', 'BUILD_USER_FIRST_NAME'),
        ('LastName', 'BUILD_USER_LAST_NAME'),
        ('Email', 'BUILD_USER_EMAIL'),
        ('BUILD_USER_ID', 'BUILD_USER_ID')
    ]
    env_user_attribute_keys = [
        'first_name',
        'last_name',
        'email',
        'build_user_id'
    ]
    user_test_attributes = [pair[0] for pair in attribute_pairs]
    user_test_attributes_are_available = [os.getenv(user_test_attr) is not None for user_test_attr in user_test_attributes]
    assert not (any(user_test_attributes_are_available) and not all(user_test_attributes_are_available)), "Some testing attributes are available but not all.\n{}".format(
        ["{}: {}".format(pair[0], os.getenv(pair[0])) for pair in attribute_pairs]
    )
    conditions_for_using_test_user = [
        all([os.getenv(test_attr) is not None for test_attr in user_test_attributes]),
    ]
    use_test_user = True if all(conditions_for_using_test_user) else False
    for i in range(len(attribute_pairs)):
        env_user_attributes[env_user_attribute_keys[i]] = os.getenv(attribute_pairs[i][1]) if not use_test_user else os.getenv(attribute_pairs[i][0])
    # for k, v in env_user_attributes.items():
    #     print('{} {}: {}'.format('env_user_attributes', k, v))
    return env_user_attributes


def process_name(name):
    processed_name = re.sub("[^a-zA-Z ]", "", name)
    return processed_name


def replace_multiple_pairs(str, replace_pairs):
    """
    Function that accepts a string and a list of tuples whose first element is the character in the string to replace
    and second element is the character to replace the first character with. It runs the replace for each of these
    pairs in order and returns the string.
    :param replace_pairs: A list of tuples with the pairs of characters to replace and to replace with
    :param str: The string to run the replace pairs on
    :return: The fully processed string
    """
    for pair in replace_pairs:
        str = str.replace(pair[0], pair[1])
    return str


def main():
    var = 6
    debug_print('var', var)


if __name__ == '__main__':
    main()
