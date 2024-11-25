def save_scd(scd_entries, output_file_path, format='md'):
    """Parse SCD entries and save them in the specified format."""
    if format == 'md':
        table_headers = ["Control ID", "Control Domain", "Security Control For Service", 
                         "Mapping to NIST CSF v1.1 control", "Policy Name", 
                         "Implementation Details", "Policy Description"]

        with open(output_file_path, 'w') as f:
            # Write table headers
            f.write(f"| {' | '.join(table_headers)} |\n")
            f.write(f"| {' | '.join(['-' * len(header) for header in table_headers])} |\n")

            # Process each entry
            for scd_entry in scd_entries:
                entry_data = {}
                implementation_details = []
                current_field = None

                # Parse the entry
                for line in scd_entry.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()

                        if key == 'Implementation Details':
                            current_field = 'Implementation Details'
                            implementation_details.append(value)
                        else:
                            current_field = key
                            entry_data[key] = value
                    elif current_field == 'Implementation Details':
                        implementation_details.append(line.strip())
                    elif current_field:
                        entry_data[current_field] += ' ' + line.strip()

                # Join Implementation Details
                entry_data['Implementation Details'] = '\n'.join(implementation_details)

                # Write the row in Markdown format
                row = f"| {entry_data.get('Control ID', '')} | {entry_data.get('Control Domain', '')} | " \
                      f"{entry_data.get('Security Control For Service', '')} | " \
                      f"{entry_data.get('Mapping to NIST CSF v1.1 control', '')} | " \
                      f"{entry_data.get('Policy Name', '')} | " \
                      f"{entry_data.get('Implementation Details', '').replace('\n', ' ')} | " \
                      f"{entry_data.get('Policy Description', '').replace('\n', ' ')} |\n"
                f.write(row)
