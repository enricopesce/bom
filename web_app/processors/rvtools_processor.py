"""
RVTools Input Processor

Concrete implementation of VMAssessmentProcessor for RVTools ZIP exports
"""

import zipfile
import pandas as pd
import os
import tempfile
import shutil
from typing import List, Dict, Any
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.base_processor import VMAssessmentProcessor
from models.vm_models import (
    VMAssessment, VMSpec, VMStorage, VMNetwork, 
    OSType, PowerState, StorageType,
    detect_os_type, detect_power_state
)


class RVToolsProcessor(VMAssessmentProcessor):
    """
    Processor for RVTools ZIP export files
    """
    
    @property
    def supported_formats(self) -> List[str]:
        return ['.zip']
    
    @property
    def processor_name(self) -> str:
        return "RVTools"
    
    def validate_input(self) -> bool:
        """Validate that input is a valid RVTools ZIP file"""
        if not self.input_path.suffix.lower() == '.zip':
            return False
        
        try:
            with zipfile.ZipFile(self.input_path, 'r') as zf:
                # Check for typical RVTools CSV files
                file_list = [f.lower() for f in zf.namelist()]
                required_patterns = ['tabvcpu', 'tabvmemory', 'tabvdisk']
                
                for pattern in required_patterns:
                    if any(pattern in filename for filename in file_list):
                        return True
                        
                return False
        except zipfile.BadZipFile:
            return False
    
    def extract_vm_data(self) -> VMAssessment:
        """Extract VM data from RVTools ZIP file"""
        assessment = VMAssessment(
            assessment_name=f"RVTools Export - {self.input_path.name}",
            source_format=self.processor_name
        )
        
        # Extract ZIP to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(self.input_path, 'r') as zf:
                zf.extractall(temp_dir)
            
            # Read CSV files
            csv_data = self._read_csv_files(temp_dir)
            
            # Merge and process data
            merged_data = self._merge_vm_data(csv_data)
            
            # Convert to standardized VM specs
            vms = self._convert_to_vm_specs(merged_data)
            
            for vm in vms:
                assessment.add_vm(vm)
        
        return assessment
    
    def _read_csv_files(self, temp_dir: str) -> Dict[str, pd.DataFrame]:
        """Read relevant CSV files from extracted directory"""
        csv_data = {}
        
        # Define file patterns to look for
        file_patterns = {
            'cpu': 'tabvcpu',
            'memory': 'tabvmemory',
            'disk': 'tabvdisk',
            'info': 'tabvinfo',
            'tools': 'tabvtools',
            'network': 'tabvnetwork'
        }
        
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if not file.endswith('.csv'):
                    continue
                
                filepath = os.path.join(root, file)
                filename = file.lower()
                
                # Find matching pattern
                file_type = None
                for key, pattern in file_patterns.items():
                    if pattern in filename:
                        file_type = key
                        break
                
                if not file_type:
                    continue
                
                try:
                    # Read CSV with flexible encoding
                    df = self._read_csv_with_encoding(filepath)
                    
                    if df is not None and 'VM UUID' in df.columns and not df.empty:
                        csv_data[file_type] = df
                        self.logger.info(f"Loaded {file_type}: {len(df)} records")
                
                except Exception as e:
                    self.logger.warning(f"Error reading {filename}: {e}")
        
        return csv_data
    
    def _read_csv_with_encoding(self, filepath: str) -> pd.DataFrame:
        """Read CSV with automatic encoding detection"""
        encodings = ['cp1252', 'utf-8', 'iso-8859-1', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, delimiter=';', encoding=encoding, low_memory=False)
                df.columns = df.columns.str.strip()
                return df
            except Exception:
                continue
        
        self.logger.warning(f"Could not read CSV file with any encoding: {filepath}")
        return None
    
    def _convert_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert MiB/MB columns to GB"""
        df = df.copy()
        
        # Convert MiB to GB
        mib_cols = [col for col in df.columns if 'mib' in col.lower() and pd.api.types.is_numeric_dtype(df[col])]
        for col in mib_cols:
            new_col = col.replace(' MiB', ' GB').replace('MiB', '_GB')
            df[new_col] = (df[col] / 1024).round(2)
            df.drop(columns=[col], inplace=True)
        
        # Convert MB to GB
        mb_cols = [col for col in df.columns if 'mb' in col.lower() and 'mbps' not in col.lower() and pd.api.types.is_numeric_dtype(df[col])]
        for col in mb_cols:
            new_col = col.replace(' MB', ' GB').replace('MB', '_GB')
            df[new_col] = (df[col] / 1000).round(2)
            df.drop(columns=[col], inplace=True)
        
        return df
    
    def _aggregate_vm_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate data by VM UUID for files with multiple records per VM"""
        if 'VM UUID' not in df.columns or df.empty:
            return df
        
        vm_counts = df['VM UUID'].value_counts()
        if vm_counts.max() == 1:
            return self._convert_units(df)
        
        # Simple aggregation strategy
        agg_dict = {}
        for col in df.columns:
            if col == 'VM UUID':
                continue
            elif pd.api.types.is_numeric_dtype(df[col]):
                # Sum for size/capacity fields, mean for others
                if any(word in col.lower() for word in ['size', 'capacity', 'mib', 'gb', 'mb']):
                    agg_dict[col] = 'sum'
                else:
                    agg_dict[col] = 'mean'
            else:
                agg_dict[col] = 'first'
        
        try:
            aggregated = df.groupby('VM UUID').agg(agg_dict).reset_index()
            return self._convert_units(aggregated)
        except Exception as e:
            self.logger.warning(f"Aggregation failed: {e}, using first record per VM")
            return self._convert_units(df.groupby('VM UUID').first().reset_index())
    
    def _merge_vm_data(self, csv_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merge all VM data sources into single dataframe"""
        if not csv_data:
            raise ValueError("No CSV data to merge")
        
        # Use CPU as base, fallback to first available
        base_key = 'cpu' if 'cpu' in csv_data else list(csv_data.keys())[0]
        result_df = self._aggregate_vm_data(csv_data[base_key])
        
        # Rename columns to avoid conflicts
        result_df.columns = [f"{base_key}_{col}" if col != 'VM UUID' else col for col in result_df.columns]
        
        # Merge other sources
        for data_type, df in csv_data.items():
            if data_type == base_key:
                continue
            
            agg_df = self._aggregate_vm_data(df)
            if agg_df.empty:
                continue
            
            # Rename and merge
            agg_df.columns = [f"{data_type}_{col}" if col != 'VM UUID' else col for col in agg_df.columns]
            result_df = result_df.merge(agg_df, on='VM UUID', how='left')
        
        self.logger.info(f"Merged data: {len(result_df)} VMs with {len(result_df.columns)} columns")
        return result_df
    
    def _convert_to_vm_specs(self, df: pd.DataFrame) -> List[VMSpec]:
        """Convert merged dataframe to standardized VMSpec objects"""
        if df.empty:
            return []
        
        # Find key columns
        column_map = self._map_columns(df)
        
        vm_specs = []
        for _, row in df.iterrows():
            try:
                vm_spec = self._create_vm_spec_from_row(row, column_map)
                if vm_spec:
                    vm_specs.append(vm_spec)
            except Exception as e:
                vm_name = row.get(column_map.get('vm_name', ''), 'unknown')
                self.logger.warning(f"Error processing VM {vm_name}: {e}")
        
        self.logger.info(f"Converted {len(vm_specs)} VM specifications")
        return vm_specs
    
    def _map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map dataframe columns to standard VM fields"""
        column_map = {}
        
        for col in df.columns:
            col_lower = col.lower()
            
            if not column_map.get('vm_name') and ('vm' in col_lower and ('name' in col_lower or col_lower.endswith('_vm'))):
                column_map['vm_name'] = col
            elif not column_map.get('os_config') and ('os according' in col_lower or ('tools' in col_lower and 'os' in col_lower)):
                column_map['os_config'] = col
            elif not column_map.get('cpu') and ('cpus' in col_lower or col_lower == 'info_cpus' or col_lower == 'cpu_cpus'):
                column_map['cpu'] = col
            elif not column_map.get('memory') and ('size' in col_lower and 'gb' in col_lower and 'memory' in col_lower):
                column_map['memory'] = col
            elif not column_map.get('disk_capacity') and ('capacity' in col_lower and 'gb' in col_lower and ('disk' in col_lower or 'total' in col_lower)):
                column_map['disk_capacity'] = col
            elif not column_map.get('annotation') and ('annotation' in col_lower):
                column_map['annotation'] = col
            elif not column_map.get('powerstate') and ('powerstate' in col_lower):
                column_map['powerstate'] = col
            elif not column_map.get('cluster') and ('cluster' in col_lower):
                column_map['cluster'] = col
            elif not column_map.get('host') and ('host' in col_lower and 'name' in col_lower):
                column_map['host'] = col
            elif not column_map.get('datacenter') and ('datacenter' in col_lower):
                column_map['datacenter'] = col
        
        return column_map
    
    def _create_vm_spec_from_row(self, row: pd.Series, column_map: Dict[str, str]) -> VMSpec:
        """Create VMSpec from dataframe row"""
        # Extract basic fields
        vm_id = str(row.get('VM UUID', ''))
        vm_name = str(row.get(column_map.get('vm_name', ''), '')).strip()
        
        if not vm_name or not vm_id:
            return None
        
        # Extract numeric fields with error handling
        cpu_cores = self._safe_int(row.get(column_map.get('cpu', ''), 0))
        memory_gb = self._safe_float(row.get(column_map.get('memory', ''), 0.0))
        
        if cpu_cores == 0 and memory_gb == 0:
            return None
        
        # Create VM spec
        vm_spec = VMSpec(
            vm_id=vm_id,
            vm_name=vm_name,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            os_type=detect_os_type(str(row.get(column_map.get('os_config', ''), ''))),
            os_config=str(row.get(column_map.get('os_config', ''), '')).strip(),
            power_state=detect_power_state(str(row.get(column_map.get('powerstate', ''), 'poweredOn'))),
            cluster=str(row.get(column_map.get('cluster', ''), '')).strip() or None,
            host=str(row.get(column_map.get('host', ''), '')).strip() or None,
            datacenter=str(row.get(column_map.get('datacenter', ''), '')).strip() or None,
            annotation=str(row.get(column_map.get('annotation', ''), '')).strip() or None,
            source_format=self.processor_name,
            assessment_date=datetime.now()
        )
        
        # Add storage if capacity found
        disk_capacity = self._safe_float(row.get(column_map.get('disk_capacity', ''), 0.0))
        if disk_capacity > 0:
            vm_spec.add_storage(disk_capacity, storage_type=StorageType.BLOCK)
        
        return vm_spec
    
    def _safe_int(self, value) -> int:
        """Safely convert value to int"""
        try:
            return int(float(value)) if pd.notna(value) else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if pd.notna(value) else 0.0
        except (ValueError, TypeError):
            return 0.0


# Register the processor
from processors.base_processor import ProcessorFactory
ProcessorFactory.register_processor(RVToolsProcessor)