def save_scd(self, scd, output_file_path, format='md'):
    """Save SCD to a file in the specified format"""
    scd_entries = re.split(r'\n\s*\n', scd.strip())  # Split entries by double newlines

    if format == 'md':
        # Define table headers
        table_headers = [
            "Control ID", "Control Domain", "Control Title",
            "Mapping to NIST CSF v1.1 control", "Client Requirement if Any",
            "Policy Name", "Policy Description", "Responsibility",
            "Frequency", "Evidence", "Implementation Details"
        ]

        def parse_entry(entry):
            """Parse individual SCD entry into a dictionary"""
            entry_data = {}
            for line in entry.splitlines():
                if line.startswith("Control ID:"):
                    entry_data["Control ID"] = line.split("Control ID:")[1].strip()
                elif line.startswith("Control Domain:"):
                    entry_data["Control Domain"] = line.split("Control Domain:")[1].strip()
                elif line.startswith("Control Title:"):
                    entry_data["Control Title"] = line.split("Control Title:")[1].strip()
                elif line.startswith("Mapping to NIST CSF v1.1 control:"):
                    entry_data["Mapping to NIST CSF v1.1 control"] = line.split("Mapping to NIST CSF v1.1 control:")[1].strip()
                elif line.startswith("Client Requirement if Any:"):
                    entry_data["Client Requirement if Any"] = line.split("Client Requirement if Any:")[1].strip()
                elif line.startswith("Policy Name:"):
                    entry_data["Policy Name"] = line.split("Policy Name:")[1].strip()
                elif line.startswith("Policy Description:"):
                    entry_data["Policy Description"] = line.split("Policy Description:")[1].strip()
                elif line.startswith("Responsibility:"):
                    entry_data["Responsibility"] = line.split("Responsibility:")[1].strip()
                elif line.startswith("Frequency:"):
                    entry_data["Frequency"] = line.split("Frequency:")[1].strip()
                elif line.startswith("Evidence:"):
                    entry_data["Evidence"] = line.split("Evidence:")[1].strip()
                elif line.startswith("Implementation Details:"):
                    entry_data["Implementation Details"] = line.split("Implementation Details:")[1].strip()

            return entry_data

        # Write the Markdown table
        with open(output_file_path, 'w') as f:
            # Write headers
            f.write(f"| {' | '.join(table_headers)} |\n")
            f.write(f"| {' | '.join(['-' * len(header) for header in table_headers])} |\n")

            # Write each entry as a table row
            for entry in scd_entries:
                entry_data = parse_entry(entry)
                row = f"| {entry_data.get('Control ID', '')} | {entry_data.get('Control Domain', '')} | {entry_data.get('Control Title', '')} | {entry_data.get('Mapping to NIST CSF v1.1 control', '')} | {entry_data.get('Client Requirement if Any', '')} | {entry_data.get('Policy Name', '')} | {entry_data.get('Policy Description', '')} | {entry_data.get('Responsibility', '')} | {entry_data.get('Frequency', '')} | {entry_data.get('Evidence', '')} | {entry_data.get('Implementation Details', '')} |\n"
                f.write(row)

        print(f"SCD saved as a Markdown table to {output_file_path}")

    elif format == 'csv':
        # Add your existing CSV handling logic here
        print(f"SCD saved as a CSV file to {output_file_path}")
