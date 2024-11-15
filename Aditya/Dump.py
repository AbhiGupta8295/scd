import pandas as pd

class IOHandler:
    @staticmethod
    def load_csv(file_paths):
        """
        Loads cloud control data and policy data from multiple dataset files.
        """
        dataframes = []

        # Define expected columns for each dataset type
        best_practices_columns = {'Control ID', 'Control Description', 'Guidance', 'Cloud Service'}
        policy_columns = {'PolicyName', 'Resource name', 'Description'}
        azure_policy_columns = {'name', 'displayName', 'description'}
        azure_benchmarks_columns = {'Control Domain', 'ASB Control ID', 'ASB Control Title', 'Guidance'}
        nist_benchmark_columns = {'Function', 'Category', 'Subcategory', 'Informative References'}

        for file_path in file_paths:
            try:
                # Try reading the file with UTF-8 encoding first, fallback to latin-1 if there's an error
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")
                    continue

            # Check for the presence of at least one expected column set
            if (
                best_practices_columns.intersection(df.columns) or
                policy_columns.intersection(df.columns) or
                azure_policy_columns.intersection(df.columns) or
                azure_benchmarks_columns.intersection(df.columns) or
                nist_benchmark_columns.intersection(df.columns)
            ):
                # Add missing columns as 'N/A' if needed
                for col in (best_practices_columns | policy_columns | azure_policy_columns |
                            azure_benchmarks_columns | nist_benchmark_columns):
                    if col not in df.columns:
                        df[col] = 'N/A'
                
                dataframes.append(df)
            else:
                print(f"Warning: Unrecognized structure in {file_path}. Skipping this file.")

        # Concatenate all dataframes if there are any
        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            return combined_df

        return None
