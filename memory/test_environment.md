# AWS Object Storage Demo — Test Environment Setup Guide

**Generated:** 2026-09-24  
**Test Scenarios:** 2 total

---

## 🌐 EXTERNAL SERVICE SETUP: AWS S3

BEFORE RUNNING TESTS, CREATE THE FOLLOWING ON THE EXTERNAL SERVICE:

### 1. AWS S3 Bucket "salescommission"

**What:** A public or private AWS S3 bucket with the exact name `salescommission`.

**Why:** Both test scenarios target this bucket by name. The bucket must exist before the extension can execute List Objects or Upload File operations. If the bucket does not exist, the extension will fail with a `NoSuchBucket` error.

**How:**
1. Log in to the AWS Management Console (https://console.aws.amazon.com)
2. Navigate to S3 (Simple Storage Service)
3. Click **Create bucket**
4. Enter bucket name: `salescommission`
5. Select a region (e.g., `us-east-1`); note this region for task configuration
6. Leave all other settings at defaults (block public access is recommended)
7. Click **Create bucket**

**Example:** After creation, you will see the bucket listed as `salescommission` in your S3 bucket list.

---

### 2. AWS IAM User with S3 Access Credentials

**What:** An AWS IAM user with an Access Key ID and Secret Access Key, configured with permissions to list and upload objects to the `salescommission` bucket.

**Why:** The extension uses these credentials to authenticate all S3 API calls. The credentials must grant `s3:ListBucket` (for List Objects) and `s3:PutObject` (for Upload File) permissions on the `salescommission` bucket. Without these permissions, the extension will fail with `AccessDenied` errors.

**How:**
1. Log in to the AWS Management Console
2. Navigate to IAM (Identity and Access Management)
3. Click **Users** in the left sidebar
4. Click **Create user**
5. Enter a username (e.g., `stonebranch-s3-demo`)
6. Click **Next**
7. On the permissions page, click **Attach policies directly**
8. Search for and attach the policy `AmazonS3FullAccess` (or create a custom policy with `s3:ListBucket` and `s3:PutObject` on `arn:aws:s3:::salescommission*`)
9. Click **Next**, then **Create user**
10. Click the username to open user details
11. Click **Security credentials** tab
12. Under **Access keys**, click **Create access key**
13. Select **Command Line Interface (CLI)** and check the confirmation
14. Click **Next**
15. Copy and securely store the **Access Key ID** and **Secret Access Key**

**Example:**
- Access Key ID: `AKIAIOSFODNN7EXAMPLE`
- Secret Access Key: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

**Note:** These credentials are already referenced in the UAC controller as the credential entity `AWS_key_Secret`. Use this credential name when creating task instances in the task JSON.

---

## 🖥️ AGENT HOST SETUP

BEFORE RUNNING TESTS, PREPARE THE FOLLOWING ON THE UAC AGENT MACHINE:

### 1. Test Input File `/tmp/report1.txt`

**What:** A plain text file located at `/tmp/report1.txt` on the Linux agent host.

**Why:** The second test scenario uploads this file to S3. If the file does not exist at the specified path, the extension will fail with a `LocalFileNotFoundError` before attempting any S3 API call.

**How:**

Create the file using one of the following methods:

**Option A: Create with shell command**
```bash
cat > /tmp/report1.txt << 'EOF'
Sales Commission Report
Generated: 2026-09-24
Department: Sales
Quarter: Q3

Total Commission: $125,000
Paid Agents: 12
Average Commission: $10,416.67
EOF
```

**Option B: Create minimal file**
```bash
echo "Sales report data" > /tmp/report1.txt
```

**Verification:**
```bash
ls -la /tmp/report1.txt
```
Expected output:
```
-rw-r--r-- 1 user group 100 Sep 24 12:00 /tmp/report1.txt
```

**Example:** After creation, the file should be readable and contain valid text content. Any non-empty text file is sufficient for the test.

---

## 📋 CHECKLIST

- ☐ AWS S3 bucket `salescommission` created in a valid AWS region (e.g., `us-east-1`)
- ☐ AWS IAM user created with Access Key ID and Secret Access Key
- ☐ IAM user granted `s3:ListBucket` permission on bucket `salescommission`
- ☐ IAM user granted `s3:PutObject` permission on bucket `salescommission`
- ☐ Note the AWS region where the bucket was created (for task configuration)
- ☐ Test input file `/tmp/report1.txt` created on the UAC agent host
- ☐ Verified: File exists and is readable by the UAC agent user
- ☐ Verified: S3 bucket is accessible from the agent host network (no firewall blocks AWS S3 endpoints)

---

## Test Execution Environment

**Test Scenarios:** The following test cases will be executed:

1. **List Objects** — Query the `salescommission` bucket and display objects
   - Input: bucket_name = `salescommission`, aws_region = `us-east-1` (or configured region)
   - Expected: Extension lists all objects in the bucket (may be empty if no prior uploads exist)

2. **Upload File** — Upload `/tmp/report1.txt` to `salescommission` with object key `reports/report1.txt`
   - Input: local_file = `/tmp/report1.txt`, bucket_name = `salescommission`, s3_object_key = `reports/report1.txt`
   - Expected: Extension uploads the file and confirms success with S3 URI `s3://salescommission/reports/report1.txt`

**Credential Reference:** Both scenarios use the UAC credential entity named `AWS_key_Secret` for authentication.

**Region Configuration:** All tasks will use the AWS region where the `salescommission` bucket was created (e.g., `us-east-1`).
