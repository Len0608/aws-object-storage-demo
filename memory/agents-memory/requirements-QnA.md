# Requirements Completeness Assessment

The requirements are classified as **Moderate Detail**.

The core intent is clear and well-established: a simple AWS S3 integration with two well-defined actions (List Objects and Upload File) using the boto3 SDK. The library choice, action set, field names (AWS Credentials, AWS Region, Bucket Name, Local File, S3 Object Key), the decision to exclude a prefix field, the bundling requirement, and the MVP/demo scope are all explicitly stated — a solid foundation.

To build the best possible solution together, a few key decisions remain open: how AWS credentials are provided to the extension, what object metadata to display when listing, what to surface in the UAC task execution UI, and whether to apply a safety cap for large S3 buckets.

---

# Platform Compatibility

**Platform Compatibility from Requirements**: Linux — confirmed in `environment.md` (Build OS: Linux, Architecture: x86_64); the requirements also state "local file from the Linux server where the Stonebranch Universal Agent is installed."

**Platform Compatibility Agreement**: Linux x86_64 — `manylinux_2_17_x86_64` compatibility rules apply. Both boto3 and tabulate are pure-Python, so no binary wheel constraints are relevant.

---

# Python Modules and Versions

## Researched Modules

**boto3**
- **Module Purpose**: AWS SDK for Python — provides all S3 operations required, including `list_objects_v2` for listing objects and `upload_file` / `put_object` for file uploads.
- **Version**: 1.43.101
- **Type**: Pure Python

**tabulate**
- **Module Purpose**: Formats Python lists into clean ASCII tables for human-readable STDOUT output (e.g., displaying S3 object listings as a grid with columns for Key, Size, and Last Modified). The architect notes specifically recommend `tablefmt="rounded_outline"` for a polished appearance.
- **Version**: 0.10.0
- **Type**: Pure Python

## Agreed Python Modules and Versions

> Placeholder — to be filled in after Q1 answer is applied.

| Module Name | Module Purpose | Version | Type |
|---|---|---|---|
| boto3 | AWS S3 SDK (list objects, upload file) | 1.43.101 | Pure Python |
| tabulate *(pending Q1)* | ASCII table formatting for STDOUT | 0.10.0 | Pure Python |

---

# Question Rationale

The requirements establish a clear, minimal scope. The five questions below target specific gaps that cannot be resolved by inference alone and that will materially shape the implementation:

1. **Module selection** — whether to add `tabulate` alongside the required `boto3` (affects STDOUT output quality for the demo)
2. **Authentication design** — whether credentials flow through a UAC Credential Field or through agent-level environment variables (a fundamental architectural decision with security implications)
3. **List Objects output detail** — which object metadata fields to display (affects STDOUT table columns and Extension Output JSON structure)
4. **Output Only Fields** — what summary information to expose in the UAC task execution list (affects the template field definition and code)
5. **Max records safety net** — whether to cap inline output for large buckets (affects code behavior and adherence to UAC best practices)

---

# Clarifying Questions for Requirements Refinement

## Critical Decision Path Questions

---

**Question 1**: Should the `tabulate` library (v0.10.0, pure-Python) be added alongside `boto3` to produce formatted ASCII table output when listing S3 objects?

- **O1: Yes** — add `tabulate` for formatted table output on STDOUT (e.g., a neatly aligned table with columns: Object Key | Size | Last Modified)
- **O2: No** — print a plain text list, one object per line (no additional dependency, simpler output)

- **Question Type**: New Discussion topic
- **Context & Resources**: Both `boto3` (1.43.101) and `tabulate` (0.10.0) are confirmed as pure-Python, compatible with Linux x86_64 and all other platforms, and have no binary wheel constraints. The UAC architect guide recommends ASCII table format for record-based STDOUT output and explicitly suggests `tablefmt="rounded_outline"` for a polished appearance. Reference: [tabulate on PyPI](https://pypi.org/project/tabulate/)
- **Question Dependencies**: None. This question is independent and informs the STDOUT format used for the List Objects action.
- **Recommended Answer**: O1 — Yes, add `tabulate`. For a demo extension, a formatted table with columns for Key, Size, and Last Modified is significantly more readable and visually compelling than a raw text list. The library is pure-Python, lightweight, and purpose-built for this use case.
- **Rationale**: A formatted table demonstrates the integration's quality and follows the UAC architect best practice for STDOUT output on record-based results. The pure-Python nature means no build or platform risk.
- **Trade-offs**: O1 adds one lightweight dependency with no binary concerns. O2 avoids the dependency entirely but produces less readable demo output.
- **Requirement Impact**: If O1 is chosen, `tabulate==0.10.0` is added to `requirements.txt`. STDOUT for List Objects will render as a `rounded_outline` ASCII table.
- **User's Answer**: O1 — Yes, add tabulate.

---

**Question 2**: How should AWS credentials be supplied to the extension at runtime?

The requirements mention "AWS Credentials" as a field. In UAC there are two distinct design approaches:

- **O1: UAC Credential Field** — The task template includes a dedicated Credential Field (a UAC-native type that securely references a stored Credential entity). The extension reads `user` (for Access Key ID) and `password` (for Secret Access Key) from the credential at runtime. Credentials are defined once in UAC, reused across task definitions, audited, and never need to be manually placed on the agent filesystem.
- **O2: Agent Environment Variables** — No credential field in the template. Instead, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are pre-configured as environment variables on the UAC Agent host. The boto3 SDK auto-discovers these variables through its credential chain. This removes the UAC credential setup step but stores credentials on the agent, requires per-agent configuration, and is outside UAC's credential management.

- **Question Type**: Clarification on existing requirement
- **Context & Resources**: boto3 credential resolution chain: [boto3 Credentials Guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html). UAC architect notes §Credential Field — recommends Credential Fields for "any sensitive authentication data" and using a single shared credential when "all actions use same authentication." UAC Credential field `user` attribute: always mandatory; `password`: for secrets up to 255 characters; `token`: for longer secrets.
- **Question Dependencies**: None. This is an independent foundational design decision.
- **Recommended Answer**: O1 — UAC Credential Field. Access Key ID stored in the `user` attribute, Secret Access Key in the `password` attribute. This is the standard, secure UAC approach and makes the task definition fully self-contained.
- **Rationale**: A UAC Credential Field is the idiomatic UAC pattern for secure credential management. It avoids coupling the extension to per-agent environment setup, keeps credentials within UAC's security boundary, and allows the same extension to be reused across different AWS accounts simply by swapping the referenced credential. For a demo this also makes the extension easier to showcase cleanly.
- **Trade-offs**: O1 requires creating a UAC Credential entity before running the task (a one-time setup step). O2 eliminates that step but couples the extension to agent-level configuration and moves credentials outside UAC's management scope.
- **Requirement Impact**: If O1 is chosen, the template includes a Credential Field labeled "AWS Credentials" (required). If O2 is chosen, no credential field appears in the template, but the task documentation must specify the required agent environment variables.
- **User's Answer**: O1 — UAC Credential Field (Access Key ID in `user`, Secret Access Key in `password`).

---

## Essential Input/Output Questions

---

**Question 3**: When listing objects in an S3 bucket, which metadata fields should be included for each object?

The boto3 `list_objects_v2` API returns per-object metadata including: Key (object name/path), Size (bytes), LastModified (timestamp), StorageClass (e.g., STANDARD, GLACIER), and ETag (MD5 hash). These fields appear in the STDOUT table and in the `result.objects` array of the Extension Output JSON.

- **O1: Object Key only** — list object names, nothing else. Minimal and clean.
- **O2: Key + Size + Last Modified** — object name, file size in bytes, and last modification timestamp. Good balance of usefulness and readability. *(Recommended)*
- **O3: Full metadata** — Key, Size, Last Modified, Storage Class, and ETag. Maximum information; most verbose.

- **Question Type**: Clarification on existing requirement
- **Context & Resources**: boto3 `list_objects_v2` response reference: [list_objects_v2 docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html). The `Contents` array in the response contains one dict per object with all available fields.
- **Question Dependencies**: Selected fields will be used in both the STDOUT table (if Q1=O1) and the `result.objects` array in the Extension Output JSON. No dependency on other questions.
- **Recommended Answer**: O2 — Key + Size + Last Modified. This set shows that the integration retrieves meaningful metadata, not just names, while remaining easy to read in a demo context. Size and date are the fields users most commonly care about when browsing object storage.
- **Rationale**: Pure name listing (O1) is underwhelming for a demo. Full metadata (O3) adds fields like ETag and StorageClass that carry little meaning to most users in a demo context. O2 strikes the practical balance.
- **Trade-offs**: O2 adds minimal complexity over O1 while significantly improving the demo experience. O3 is more complete but adds noise with fields that are rarely actionable without deeper AWS context.
- **Requirement Impact**: The selected fields define the STDOUT table columns and the structure of each object entry in the Extension Output `result.objects` array. With O2 selected: `[{"key": "...", "size": 12345, "last_modified": "2026-09-24T10:00:00Z"}, ...]`.
- **User's Answer**: O2 — Key + Size + Last Modified.

---

**Question 4**: What information should be surfaced as Output Only fields visible in the UAC task execution list?

UAC displays Output Only fields as columns in the task execution list view, giving at-a-glance visibility into what a task did without opening the full log. The architect guide recommends 2–3 fields for most extensions, keeping values short and immediately meaningful.

Proposed fields:
- **Status**: A brief result message always visible regardless of action. Examples: `"Success: Listed 42 objects in 'my-bucket'"`, `"Success: Uploaded to s3://my-bucket/reports/q3.csv"`, `"Error: Bucket 'my-bucket' not found"`
- **Result** (action-specific): For List Objects — the count of objects returned (e.g., `"42 objects"`). For Upload File — the full S3 URI of the uploaded object (e.g., `"s3://my-bucket/reports/q3.csv"`).

- **O1: Status only** — one output field with a brief success/error message. Simplest possible.
- **O2: Status + Result** — Status message plus a second field showing the object count (List Objects) or S3 URI (Upload File). *(Recommended)*

- **Question Type**: New Discussion topic
- **Context & Resources**: UAC architect notes §Runtime Outputs — "2–3 fields are suitable for most cases"; §Multi-Channel Output Pattern — shows Status and a result field as the standard two-field pattern.
- **Question Dependencies**: None.
- **Recommended Answer**: O2 — Status + Result. Two output fields strike the recommended balance: status provides an immediately human-readable summary, and the result field (count or S3 URI) gives the most actionable piece of data for each action without needing to open the task logs.
- **Rationale**: For a demo, the S3 URI after upload is particularly useful — it confirms exactly where the file landed. The object count for List Objects gives immediate feedback on what the bucket contains. Both are short enough to display cleanly in the task list column.
- **Trade-offs**: O2 adds one more template field to define and set in code. At this scale it is trivially simple. O1 is the bare minimum but misses the demo value of showing the key result at a glance.
- **Requirement Impact**: Template will include two Output Only Text Fields: a "Status" field (always set) and a "Result" field (set to object count for List Objects, S3 URI for Upload File). Both will have `defaultListView: true` to appear as columns in the UAC task list.
- **User's Answer**: O2 — Status + Result (object count for List Objects; S3 URI for Upload File).

---

## Functional Behavior Questions

---

**Question 5**: Should the List Objects output be capped to protect against very large S3 buckets?

S3 buckets can contain thousands or millions of objects. If the extension outputs the full listing inline to STDOUT and the Extension Output JSON, it can bloat the UAC database and hit the Universal Agent's output size limits. The UAC architect guide defines the "Large Output Safety Net Pattern" for exactly this scenario: cap the number of records written inline using the environment variable `UE_MAX_OUTPUT_RECORDS` (defaulting to 100), and include a note in the output when the result is truncated.

The cap applies only to inline output written to STDOUT and Extension Output. The actual boto3 API call still requests up to the cap number of objects from S3 using the `MaxKeys` parameter, so no unnecessary data is fetched.

- **O1: No cap** — output all objects returned by the S3 API. Simpler code; risky for large buckets.
- **O2: Cap at 100 records by default** — controlled via `UE_MAX_OUTPUT_RECORDS` environment variable; when truncated, STDOUT and Extension Output include a note with the total returned count and the applied limit. *(Recommended)*

- **Question Type**: New Discussion topic
- **Context & Resources**: UAC architect notes §Large Output Safety Net Pattern. The `UE_MAX_OUTPUT_RECORDS` convention is the standard UAC-recommended environment variable name for this pattern. boto3 `list_objects_v2` supports `MaxKeys` (1–1000) to limit the API response directly.
- **Question Dependencies**: None.
- **Recommended Answer**: O2 — cap at 100 records via `UE_MAX_OUTPUT_RECORDS`. Even for an MVP/demo, this is a sensible guard that costs minimal code complexity and prevents unexpected issues if the demo bucket is larger than expected.
- **Rationale**: The 100-record default is sufficient for any demo scenario. The environment variable gives flexibility to adjust without code changes. Following this pattern from the start means no rework is needed if the extension moves beyond demo use.
- **Trade-offs**: O2 adds a small amount of code to read the environment variable and apply the cap. O1 is marginally simpler but introduces a latent risk that is hard to diagnose when it triggers.
- **Requirement Impact**: The extension will read `UE_MAX_OUTPUT_RECORDS` from `os.environ` (defaulting to `100`) and pass it as `MaxKeys` to `list_objects_v2`. If the bucket contains more objects than the cap, STDOUT will include a line such as: `"Note: Output limited to 100 records. Total objects in bucket: 2847."` The same note will appear in the Extension Output JSON as `result.truncated: true` and `result.total_returned: 2847`.
- **User's Answer**: O2 — Cap at 100 records by default via UE_MAX_OUTPUT_RECORDS environment variable.
