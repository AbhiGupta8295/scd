import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List
import logging
from sklearn.preprocessing import LabelEncoder
import os

class SecurityDatasetAnalyzer:
    def __init__(self, log_level=logging.INFO):
        """Initialize the analyzer with logging configuration."""
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(__name__)
        self.label_encoders = {}
        self.data = None
        self.analysis_results = None

    def load_and_analyze_data(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load and analyze security-related CSV data, with specific handling for security categories
        and preparation for GenAI model input.
        
        Args:
            file_path (str): Path to the CSV file containing security data
            
        Returns:
            Tuple containing:
                - Processed DataFrame
                - Dictionary with analysis results and metadata
        """
        try:
            self.logger.info(f"Loading data from {file_path}")
            
            # Load the CSV file
            self.data = pd.read_csv(file_path)
            
            # Basic data cleaning
            self.data.columns = self.data.columns.str.strip().str.lower()
            
            # Identify key security-related columns
            security_columns = {
                'identify': [col for col in self.data.columns if 'identify' in col.lower()],
                'category': [col for col in self.data.columns if 'category' in col.lower()],
                'subcategory': [col for col in self.data.columns if 'subcategory' in col.lower()],
                'references': [col for col in self.data.columns if 'reference' in col.lower()]
            }
            
            # Analyze data characteristics
            self.analysis_results = {
                "file_info": {
                    "filename": Path(file_path).name,
                    "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
                    "total_rows": len(self.data),
                    "total_columns": len(self.data.columns)
                },
                "security_analysis": {
                    "security_columns_found": security_columns,
                    "unique_categories": self.data[security_columns['category']].nunique().to_dict() if security_columns['category'] else {},
                    "unique_subcategories": self.data[security_columns['subcategory']].nunique().to_dict() if security_columns['subcategory'] else {}
                },
                "data_quality": {
                    "missing_values": self.data.isnull().sum().to_dict(),
                    "missing_percentage": (self.data.isnull().sum() / len(self.data) * 100).round(2).to_dict()
                }
            }
            
            # Clean and prepare data for GenAI
            self.data = self._prepare_for_genai()
            
            self.logger.info("Data analysis completed successfully")
            return self.data, self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Error during data analysis: {str(e)}")
            raise

    def _prepare_for_genai(self) -> pd.DataFrame:
        """Prepare the data specifically for GenAI model input."""
        df = self.data.copy()
        
        # Fill missing values appropriately
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna('unknown')
            else:
                df[col] = df[col].fillna(-1)
        
        # Encode categorical columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            self.label_encoders[col] = LabelEncoder()
            df[col] = self.label_encoders[col].fit_transform(df[col])
        
        return df

    def get_text_for_training(self) -> List[str]:
        """
        Generate formatted text strings for training the GenAI model.
        Returns a list of formatted strings combining relevant security information.
        """
        if self.data is None:
            raise ValueError("Data not loaded. Please run load_and_analyze_data first.")
        
        training_texts = []
        for _, row in self.data.iterrows():
            # Combine relevant columns into a meaningful text string
            text = f"Category: {row.get('category', '')} | "
            text += f"Subcategory: {row.get('subcategory', '')} | "
            text += f"ID: {row.get('identify', '')} | "
            text += f"References: {row.get('references', '')}"
            training_texts.append(text.strip())
        
        return training_texts

    def export_analysis_report(self, output_path: str):
        """Export the analysis results to a JSON file."""
        if self.analysis_results is None:
            raise ValueError("No analysis results available. Please run load_and_analyze_data first.")
        
        import json
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        self.logger.info(f"Analysis report exported to {output_path}")
