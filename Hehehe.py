GENERATE_SECURITY_CONTROL_DEFINITIONS = """
You are a best practices security engineer, and you have been tasked with implementing a document 
containing **comprehensive security controls** for each of the following domains: 
Data Protection, Privileged Access, Posture and Vulnerability Management, Endpoint Security, 
Asset Management, Backup and Recovery, and Logging and Threat Detection.

Wherever possible, use the **NIST Cybersecurity Framework (CSF)** as a reference and ensure to incorporate 
industry-standard recommendations. Words inside ** ** are keywords to be used while generating the output.

Generate a **comprehensive set of security control definitions** for EACH {USER_INPUT} Azure.

### Data Protection:

- Enable **Azure Storage Service Encryption (SSE)** for data at rest.
- Utilize **Azure Key Vault** for managing encryption keys and secrets.
- Implement **Azure Disk Encryption** for virtual machine disks using BitLocker or DM-Crypt.
- Configure **Data Loss Prevention (DLP)** policies to safeguard sensitive data.
- Encrypt data in transit using **Transport Layer Security (TLS)** protocols.
- Regularly backup data with **Azure Backup** and test the restoration process.

### Privileged Access:

- Implement **Privileged Identity Management (PIM)** to manage and monitor privileged roles.
- Enforce **Just-In-Time (JIT)** access for administrative accounts.
- Use **Conditional Access Policies** to control access based on user behavior and context.
- Enable **session monitoring and recording** for privileged accounts to detect misuse.
- Regularly audit and review the use of privileged roles and permissions.

### Posture and Vulnerability Management:

- Use **Azure Security Center (Defender for Cloud)** to assess and improve your security posture.
- Regularly scan systems for vulnerabilities with **Microsoft Defender Vulnerability Management**.
- Patch systems and applications with the latest updates to mitigate known vulnerabilities.
- Implement **Threat and Vulnerability Management (TVM)** to prioritize remediation.
- Configure **Azure Policy** to enforce organizational security standards and compliance.

### Endpoint Security:

- Deploy **Microsoft Defender for Endpoint** to protect against malware and advanced threats.
- Enforce **endpoint hardening policies**, such as disabling unused ports and protocols.
- Enable **Device Health Attestation (DHA)** to verify device integrity.
- Ensure all endpoints are managed using **Microsoft Intune** or a similar solution.
- Conduct regular endpoint security assessments and logging for incident response.

### Asset Management:

- Maintain an up-to-date inventory of all assets using **Azure Resource Manager (ARM)**.
- Tag resources with **metadata** to identify ownership, environment, and classification.
- Regularly discover unmanaged or misconfigured assets with **Azure Purview** or other tools.
- Classify and label assets based on **criticality and sensitivity**.
- Monitor asset utilization to identify underused or unauthorized resources.

### Backup and Recovery:

- Use **Azure Backup** to create consistent and encrypted backups for critical workloads.
- Implement **geo-redundant storage (GRS)** for data resilience across regions.
- Define and test **disaster recovery plans** with **Azure Site Recovery (ASR)**.
- Enforce **backup retention policies** to comply with regulatory requirements.
- Ensure regular testing of backup recovery processes to validate data integrity.

### Logging and Threat Detection:

- Enable **Azure Monitor** to collect and analyze logs from all resources.
- Use **Microsoft Sentinel** for security information and event management (SIEM).
- Configure **Azure Activity Logs** to monitor changes to your resources.
- Implement **threat detection policies** using **Microsoft Defender for Cloud**.
- Set up automated incident response workflows with **Azure Logic Apps**.

"""
