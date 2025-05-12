# Using AWS CodeCommit as a **SOURCE** for Congregate

> **TL;DR**  
> The HTTPS password that Congregate places in the `import_url` **must not contain the `/` character**.  
> If your generated password includes a slash, click **“Generate credentials”** again until you obtain one that does not.

## 1. Create/choose an IAM user

1. Open the **IAM Console** -> *Users*  
2. Create a new user (or select an existing one) and attach either:
   * **AWSCodeCommitFullAccess**: easiest for testing,  
   *or*
   * the scoped policy you really need **AWSCodeCommitPowerUser**.
3. Go to **Select the CodeCommit user you just created ▸ Go to the Security credentials tab**
4. Choose **“Create access key” from Access keys**.

AWS [Docs](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-https-unixes.html#setting-up-https-unixes-iam): **“Step 1: Create an IAM user for CodeCommit”**  

## 2. Generate HTTPS credentials

1. Go to **IAM -> Users -> Select the CodeCommit user you just created -> Go to the Security credentials tab**
2. Choose **“Generate credentials” from HTTPS Git credentials for AWS CodeCommit**.
3. Look at the generated **Password**:
   * If it **contains `/`**, click **Refresh Password** until it does **not**.  
     (`+` and `=` are fine; only `/` breaks GitLab 17.2+ imports.)
4. Copy the **Username** and **Password** – you will not see them again.

AWS [Docs](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-https-unixes.html): **“Setup for HTTPS users using Git credentials”**  

## 3. Populate `congregate.conf`

```ini
[SOURCE]
src_type                   = CodeCommit
src_aws_region             = us-east-1            # e.g. us‑east‑1
src_aws_access_key_id      = AKIA...              # IAM user’s access key
src_aws_secret_access_key  = <obfuscated>         # run `congregate obfuscate`
src_aws_session_token      = <obfuscated>         # (leave empty or comment this out for static creds)
src_aws_codecommit_username = <codecommit-user-at>-<account-id>
src_aws_codecommit_password = <obfuscated>        # must **not** include "/"
