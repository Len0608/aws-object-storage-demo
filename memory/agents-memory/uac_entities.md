# UAC Entities

**Extension:** aws-object-storage-demo

---

## Agent Selection

### Available Agents

| Agent Name | Host | IP | Type | Status | Queue | Version |
|------------|------|----|------|--------|-------|---------|
| nginx-with-sidecar - AKS-SIDECAR-TEST | nginx-with-sidecar | 10.244.4.224 | Linux/Unix | Active | AKS-SIDECAR-TEST | 7.9.2.2 |
| sb-agent-ubu - AGNT0012 | sb-agent-ubu | 127.0.1.1 | Linux/Unix | Active | AGNT0012 | 7.9.0.0 |
| UDMG-SB | ip-172-31-2-26.us-east-2.compute.internal | 172.31.2.26 | Linux/Unix | Active | AGNT0118 | 7.9.2.0 |
| pm-agent-ua-98fb75db9-48lt5 - OCP-Agent | pm-agent-ua-98fb75db9-48lt5 | 10.173.1.203 | Linux/Unix | Active | OCP-Agent | 7.9.0.0 |
| workload-identity-ua-0 - UA-DEV-K8S | workload-identity-ua-0 | 10.244.3.98 | Linux/Unix | Active | UA-DEV-K8S | 8.0.0.1 |
| AGT_LINUX_LIBELLE | ip-30-0-2-107.eu-west-1.compute.internal | 30.0.2.107 | Linux/Unix | Active | AGNT0002 | 7.9.2.2 |
| sbbatch-77656fff4b-nrdkq - AGNT0040 | sbbatch-77656fff4b-nrdkq | 10.174.1.228 | Linux/Unix | Active | AGNT0040 | 7.8.0.0 |
| universal-agent-7dc969c757-ch7rt - KymaRbacAgent | universal-agent-7dc969c757-dwl27 | 10.96.5.9 | Linux/Unix | Active | KymaRbacAgent | 8.0.2.0 |
| openshift-agent-0 - Openshift-Agent | openshift-agent-0 | 10.173.1.22 | Linux/Unix | Active | Openshift-Agent | 7.9.0.0 |
| universal-agent-65f58f69cf-7dxgn - KymaRbacAgent-dev | universal-agent-65f58f69cf-gn4jq | 10.96.4.6 | Linux/Unix | Active | KymaRbacAgent-dev | 8.0.2.0 |
| AGT_LINUX_PS1 | packaged-solutions-1 | 30.0.1.111 | Linux/Unix | Active | AGNT0009 | 8.0.0.0 |
| AGT_WIN_PS3 | EC2AMAZ-KP602N3 | 30.0.1.241 | Windows | Active | AGNT0006 | 7.7.1.0 |
| yellowbird - AGNT0019 | yellowbird | 172.16.0.4 | Linux/Unix | Active | AGNT0019 | 7.9.0.1 |
| k3s-ua-1 - k3s-ua-1 | k3s-ua-1 | 10.42.0.19 | Linux/Unix | Active | k3s-ua-1 | 8.0.0.0 |
| k3s-ua-0 - k3s-ua-0 | k3s-ua-0 | 10.42.0.18 | Linux/Unix | Active | k3s-ua-0 | 8.0.0.0 |
| backup-ua-6c59d6578b-dvn24 - AGNT0142 | backup-ua-6c59d6578b-dvn24 | 10.244.1.69 | Linux/Unix | Active | AGNT0142 | 8.0.1.0 |
| integration-showcase-ua-56b6947d59-lr4zn - AGNT0149 | integration-showcase-ua-56b6947d59-lr4zn | 10.244.3.240 | Linux/Unix | Active | AGNT0149 | 8.0.0.1 |
| pm-agent-demo - pm-agent-demo | pm-agent-demo | 10.120.70.26 | Linux/Unix | Active | pm-agent-demo | 7.8.0.0 |

### Selected Agent

| Field      | Value |
|------------|-------|
| Agent Name | nginx-with-sidecar - AKS-SIDECAR-TEST |
| Host Name  | nginx-with-sidecar |
| IP Address | 10.244.4.224 |
| Type       | Linux/Unix |
| Status     | Active |
| Queue Name | AKS-SIDECAR-TEST |
| Version    | 7.9.2.2 |
| SysID      | 2ed88652f231458ba5d81a4db5ef398c |

**Required OS Type:** Linux
**Selection rationale:** First active Linux agent returned by the UAC controller agent list API.

---

## Required Entities

### Credentials

| Credential Name | Type | Field Name | Auth Method | Used In Scenarios |
|----------------|------|------------|-------------|-------------------|
| AWS_key_Secret | Generic | aws_credentials | AWS Access Key (user = Access Key ID, password = Secret Access Key) | Test_AwsObjectStorageDemo_ListObjects_Minimal, Test_AwsObjectStorageDemo_UploadFile_Minimal |

### Scripts

*No script fields are defined in this extension's template.*

---

## Created Entities

### Credentials

| Credential Name | SysID | Status |
|----------------|-------|--------|
| | | |

### Scripts

| Script Name | SysID | Status |
|------------|-------|--------|
| | | |
