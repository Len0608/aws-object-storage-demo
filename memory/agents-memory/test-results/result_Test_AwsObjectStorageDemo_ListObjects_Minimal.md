## Test: Test_AwsObjectStorageDemo_ListObjects_Minimal

**Status**: ⚠ Error

### Output:
```
STDERR:
2026-09-24 12:35:57,753 - 140447599752768 AsyEvent[EXTENSION_START] - extension.py[63] INFO: aws-object-storage-demo v1.0.0 started
2026-09-24 12:35:57,753 - 140447599752768 AsyEvent[EXTENSION_START] - extension.py[70] INFO: Action requested: List Objects
2026-09-24 12:35:57,753 - 140447599752768 AsyEvent[EXTENSION_START] - extension.py[76] INFO: Executing action: List Objects
2026-09-24 12:35:57,753 - 140447599752768 AsyEvent[EXTENSION_START] - list_objects.py[33] INFO: Starting list_objects action
2026-09-24 12:35:57,796 - 140447599752768 AsyEvent[EXTENSION_START] - extension_start_result.py[221] ERROR: Error in extension: /var/opt/universal/uag/extensions/.aws-object-storage-demo/extension.py:187 - System Error: 'Credential' object is not subscriptable

STDOUT: [empty]

EXTENSION:
{
  "exit_code": 1,
  "status_description": "System Error: 'Credential' object is not subscriptable",
  "metadata": {
    "version": "1.0.0",
    "extension": "aws-object-storage-demo"
  },
  "input_fields": {
    "action": ["List Objects"],
    "aws_credentials": {
      "user": "AKIARYOBJ5GY2FWR7V7Y",
      "password": "****",
      "token": "",
      "passphrase": ""
    },
    "aws_region": "us-east-1",
    "bucket_name": "salescommission",
    "local_file": "",
    "s3_object_key": ""
  },
  "result": {},
  "errors": [
    {
      "type": "UnexpectedSystemError",
      "message": "System Error: 'Credential' object is not subscriptable",
      "exit_code": 1
    }
  ]
}
```

### Notes:
- UAC instance ID: 1790250098958687155MLO4CNLWHTHVW
- Exit code: 1
- Status description: System Error: 'Credential' object is not subscriptable
- Error originates at extension.py:187
