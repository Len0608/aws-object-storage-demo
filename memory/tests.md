# Test Plan

**Extension:** aws-object-storage-demo
**Generated:** 2026-09-24

---

## Test: Test_AwsObjectStorageDemo_ListObjects_Minimal

**Template:** Aws Object Storage Demo
**Agent:** nginx-with-sidecar - AKS-SIDECAR-TEST
**Input Fields:**
- action: List Objects
- aws_credentials: AWS_key_Secret
- aws_region: us-east-1
- bucket_name: salescommission
**Expected Results:**
- Task completes with exit code 0
- STDOUT contains a rounded_outline ASCII table with columns Key, Size, Last Modified
- output_data.status = "Success: Listed <N> objects in 'salescommission'"
- output_data.result = "<N> objects"

---

## Test: Test_AwsObjectStorageDemo_UploadFile_Minimal

**Template:** Aws Object Storage Demo
**Agent:** nginx-with-sidecar - AKS-SIDECAR-TEST
**Input Fields:**
- action: Upload File
- aws_credentials: AWS_key_Secret
- aws_region: us-east-1
- bucket_name: salescommission
- local_file: /tmp/report1.txt
- s3_object_key: reports/report1.txt
**Expected Results:**
- Task completes with exit code 0
- STDOUT contains "Uploaded /tmp/report1.txt to s3://salescommission/reports/report1.txt"
- output_data.status = "Success: Uploaded to s3://salescommission/reports/report1.txt"
- output_data.result = "s3://salescommission/reports/report1.txt"

---
