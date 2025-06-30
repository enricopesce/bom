"""
Enhanced Excel Report Generator with Advanced Features
Uses xlsxwriter for better performance and more features than openpyxl
"""

import xlsxwriter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from models.vm_models import VMAssessment, BillOfMaterials, OSType
from currency_utils import get_excel_currency_format, get_currency_symbol


class EnhancedExcelGenerator:
    """Advanced Excel generator with charts, conditional formatting, and performance optimization"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme
        self.colors = {
            'primary': '#366092',
            'secondary': '#4472C4', 
            'accent': '#70AD47',
            'warning': '#FFC000',
            'danger': '#C5504B',
            'light_gray': '#F2F2F2',
            'dark_gray': '#404040',
            'white': '#FFFFFF'
        }
    
    def generate_excel_report(self, bom: BillOfMaterials, assessment: VMAssessment, 
                            output_file: Path) -> str:
        """Generate enhanced Excel report with charts and advanced formatting"""
        
        # Create workbook with xlsxwriter for better performance
        workbook = xlsxwriter.Workbook(str(output_file), {
            'constant_memory': True,  # Memory optimization for large files
            'tmpdir': '/tmp',
            'default_date_format': 'yyyy-mm-dd',
            'remove_timezone': True
        })
        
        # Define formats
        formats = self._create_formats(workbook, bom.currency)
        
        # Create worksheets
        self._create_executive_summary(workbook, formats, bom, assessment)
        self._create_vm_inventory(workbook, formats, bom, assessment)  
        self._create_cost_analysis(workbook, formats, bom, assessment)
        self._create_charts_dashboard(workbook, formats, bom, assessment)
        self._create_detailed_bom(workbook, formats, bom, assessment)
        
        workbook.close()
        return str(output_file)
    
    def _create_formats(self, workbook, currency: str = "EUR") -> Dict[str, Any]:
        """Create all Excel formats for consistent styling"""
        currency_format = get_excel_currency_format(currency)
        
        return {
            'title': workbook.add_format({
                'font_size': 18,
                'bold': True,
                'font_color': self.colors['white'],
                'bg_color': self.colors['primary'],
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'header': workbook.add_format({
                'font_size': 12,
                'bold': True,
                'font_color': self.colors['white'],
                'bg_color': self.colors['secondary'],
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'text_wrap': True
            }),
            'subheader': workbook.add_format({
                'font_size': 10,
                'bold': True,
                'bg_color': self.colors['light_gray'],
                'border': 1,
                'align': 'left'
            }),
            'currency': workbook.add_format({
                'num_format': currency_format,
                'border': 1,
                'align': 'right'
            }),
            'number': workbook.add_format({
                'num_format': '#,##0',
                'border': 1,
                'align': 'right'
            }),
            'percentage': workbook.add_format({
                'num_format': '0.0%',
                'border': 1,
                'align': 'right'
            }),
            'data': workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'top'
            }),
            'data_center': workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'total': workbook.add_format({
                'font_size': 11,
                'bold': True,
                'bg_color': self.colors['accent'],
                'font_color': self.colors['white'],
                'num_format': currency_format,
                'border': 2,
                'align': 'right'
            }),
            'kpi': workbook.add_format({
                'font_size': 14,
                'bold': True,
                'font_color': self.colors['primary'],
                'align': 'center',
                'border': 1
            })
        }
    
    def _create_executive_summary(self, workbook, formats, bom: BillOfMaterials, 
                                assessment: VMAssessment):
        """Create executive summary with KPIs and charts"""
        worksheet = workbook.add_worksheet('Executive Summary')
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:F', 15)
        
        row = 0
        
        # Title
        worksheet.merge_range('A1:F1', 'VM Assessment Executive Summary', formats['title'])
        worksheet.set_row(0, 30)
        row += 2
        
        # Generation info
        worksheet.write(row, 0, 'Report Generated:', formats['subheader'])
        worksheet.write(row, 1, datetime.now().strftime('%Y-%m-%d %H:%M'), formats['data'])
        row += 1
        
        worksheet.write(row, 0, 'Source File:', formats['subheader']) 
        worksheet.write(row, 1, assessment.metadata.get('source_file', 'Unknown'), formats['data'])
        row += 2
        
        # KPI Section
        worksheet.merge_range(row, 0, row, 5, 'Key Performance Indicators', formats['header'])
        row += 1
        
        # Calculate KPIs
        active_vms = len([vm for vm in assessment.vms if vm.power_state == 'poweredOn'])
        total_vcpus = sum(vm.num_cpu for vm in assessment.vms if vm.power_state == 'poweredOn')
        total_memory_gb = sum(vm.memory_mb / 1024 for vm in assessment.vms if vm.power_state == 'poweredOn')
        total_storage_gb = sum(vm.provisioned_space_mb / 1024 for vm in assessment.vms if vm.power_state == 'poweredOn')
        monthly_cost = bom.total_monthly_cost
        annual_cost = monthly_cost * 12
        
        # KPI Table
        kpis = [
            ('Active VMs', active_vms, formats['kpi']),
            ('Total vCPUs', total_vcpus, formats['kpi']),
            ('Total Memory (GB)', f'{total_memory_gb:,.0f}', formats['kpi']),
            ('Total Storage (GB)', f'{total_storage_gb:,.0f}', formats['kpi']),
            ('Monthly Cost', monthly_cost, formats['currency']),
            ('Annual Cost', annual_cost, formats['currency'])
        ]
        
        for i, (metric, value, fmt) in enumerate(kpis):
            col = i % 3
            if i == 3:
                row += 1
            worksheet.write(row, col*2, metric, formats['subheader'])
            if isinstance(value, (int, float)) and 'currency' in str(fmt):
                worksheet.write(row, col*2 + 1, value, fmt)
            else:
                worksheet.write(row, col*2 + 1, value, fmt)
        
        row += 3
        
        # OS Distribution
        worksheet.merge_range(row, 0, row, 5, 'Operating System Distribution', formats['header'])
        row += 1
        
        # Headers
        headers = ['OS Family', 'VM Count', 'Percentage', 'vCPUs', 'Memory (GB)', 'Est. Monthly Cost']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['subheader'])
        row += 1
        
        # Calculate OS distribution
        os_stats = self._calculate_os_distribution(assessment, bom)
        
        for os_name, stats in os_stats.items():
            worksheet.write(row, 0, os_name, formats['data'])
            worksheet.write(row, 1, stats['count'], formats['number'])
            worksheet.write(row, 2, stats['percentage'], formats['percentage'])
            worksheet.write(row, 3, stats['vcpus'], formats['number'])
            worksheet.write(row, 4, stats['memory_gb'], formats['number'])
            worksheet.write(row, 5, stats['monthly_cost'], formats['currency'])
            row += 1
        
        # Add conditional formatting for costs
        worksheet.conditional_format(f'F{row-len(os_stats)}:F{row-1}', {
            'type': '3_color_scale',
            'min_color': '#63BE7B',
            'mid_color': '#FFEB9C', 
            'max_color': '#FFC7CE'
        })
        
        # Add chart space
        row += 2
        worksheet.write(row, 0, 'OS Distribution Chart:', formats['subheader'])
        
        # Create pie chart for OS distribution
        chart = workbook.add_chart({'type': 'pie'})
        chart.add_series({
            'name': 'VM Count by OS',
            'categories': f'=\'Executive Summary\'!$A${row-len(os_stats)}:$A${row-1}',
            'values': f'=\'Executive Summary\'!$B${row-len(os_stats)}:$B${row-1}',
            'data_labels': {'percentage': True},
        })
        chart.set_title({'name': 'VM Distribution by Operating System'})
        chart.set_size({'width': 400, 'height': 300})
        worksheet.insert_chart(row + 1, 0, chart)
    
    def _create_vm_inventory(self, workbook, formats, bom: BillOfMaterials, 
                           assessment: VMAssessment):
        """Create detailed VM inventory with filtering and sorting"""
        worksheet = workbook.add_worksheet('VM Inventory')
        
        # Filter to only active VMs
        active_vms = [vm for vm in assessment.vms if vm.power_state == 'poweredOn']
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # VM Name
        worksheet.set_column('B:B', 15)  # OS
        worksheet.set_column('C:C', 10)  # vCPU
        worksheet.set_column('D:D', 12)  # Memory
        worksheet.set_column('E:E', 12)  # Storage
        worksheet.set_column('F:F', 15)  # Monthly Cost
        worksheet.set_column('G:G', 12)  # Power State
        worksheet.set_column('H:H', 20)  # Folder
        
        row = 0
        
        # Title
        worksheet.merge_range('A1:H1', f'VM Inventory - {len(active_vms)} Active VMs', formats['title'])
        worksheet.set_row(0, 25)
        row += 2
        
        # Headers
        headers = ['VM Name', 'Operating System', 'vCPUs', 'Memory (GB)', 
                  'Storage (GB)', 'Monthly Cost', 'Power State', 'Folder']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['header'])
        row += 1
        
        # Data rows
        for vm in sorted(active_vms, key=lambda x: x.vm_name):
            worksheet.write(row, 0, vm.vm_name, formats['data'])
            worksheet.write(row, 1, vm.guest_os, formats['data'])
            worksheet.write(row, 2, vm.num_cpu, formats['number'])
            worksheet.write(row, 3, vm.memory_mb / 1024, formats['number'])
            worksheet.write(row, 4, vm.provisioned_space_mb / 1024, formats['number'])
            
            # Find cost for this VM
            vm_cost = 0
            for line in bom.lines:
                if hasattr(line, 'vm_name') and line.vm_name == vm.vm_name:
                    vm_cost += line.monthly_cost
            
            worksheet.write(row, 5, vm_cost, formats['currency'])
            worksheet.write(row, 6, vm.power_state, formats['data_center'])
            worksheet.write(row, 7, vm.folder or 'Root', formats['data'])
            row += 1
        
        # Add autofilter
        worksheet.autofilter(2, 0, row - 1, 7)
        
        # Add conditional formatting for high-cost VMs
        worksheet.conditional_format(f'F3:F{row}', {
            'type': 'top',
            'value': 10,
            'format': workbook.add_format({'bg_color': '#FFC7CE'})
        })
    
    def _create_cost_analysis(self, workbook, formats, bom: BillOfMaterials, 
                            assessment: VMAssessment):
        """Create detailed cost analysis with breakdown and trends"""
        worksheet = workbook.add_worksheet('Cost Analysis')
        
        # Set column widths
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:F', 15)
        
        row = 0
        
        # Title
        worksheet.merge_range('A1:F1', 'Oracle Cloud Cost Analysis', formats['title'])
        worksheet.set_row(0, 25)
        row += 2
        
        # Cost breakdown by category
        worksheet.merge_range(row, 0, row, 5, 'Cost Breakdown by Category', formats['header'])
        row += 1
        
        # Headers
        headers = ['Category', 'Monthly Cost', 'Annual Cost', 'Percentage', 'VM Count', 'Avg per VM']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['subheader'])
        row += 1
        
        # Calculate cost breakdown
        cost_breakdown = self._calculate_cost_breakdown(bom)
        total_monthly = sum(item['monthly'] for item in cost_breakdown.values())
        
        for category, costs in cost_breakdown.items():
            percentage = costs['monthly'] / total_monthly if total_monthly > 0 else 0
            avg_per_vm = costs['monthly'] / costs['vm_count'] if costs['vm_count'] > 0 else 0
            
            worksheet.write(row, 0, category, formats['data'])
            worksheet.write(row, 1, costs['monthly'], formats['currency'])
            worksheet.write(row, 2, costs['monthly'] * 12, formats['currency'])
            worksheet.write(row, 3, percentage, formats['percentage'])
            worksheet.write(row, 4, costs['vm_count'], formats['number'])
            worksheet.write(row, 5, avg_per_vm, formats['currency'])
            row += 1
        
        # Total row
        worksheet.write(row, 0, 'TOTAL', formats['total'])
        worksheet.write(row, 1, total_monthly, formats['total'])
        worksheet.write(row, 2, total_monthly * 12, formats['total'])
        worksheet.write(row, 3, 1.0, formats['percentage'])
        worksheet.write(row, 4, len([vm for vm in assessment.vms if vm.power_state == 'poweredOn']), formats['number'])
        row += 3
        
        # Create cost breakdown chart
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Monthly Cost by Category',
            'categories': f'=\'Cost Analysis\'!$A${row-len(cost_breakdown)-2}:$A${row-3}',
            'values': f'=\'Cost Analysis\'!$B${row-len(cost_breakdown)-2}:$B${row-3}',
        })
        chart.set_title({'name': 'Monthly Cost Breakdown by Category'})
        chart.set_x_axis({'name': 'Category'})
        currency_symbol = get_currency_symbol(bom.currency)
        chart.set_y_axis({'name': f'Monthly Cost ({currency_symbol})'})
        chart.set_size({'width': 500, 'height': 300})
        worksheet.insert_chart(row, 0, chart)
    
    def _create_charts_dashboard(self, workbook, formats, bom: BillOfMaterials, 
                               assessment: VMAssessment):
        """Create dashboard with multiple charts and visualizations"""
        worksheet = workbook.add_worksheet('Charts Dashboard')
        
        # Title
        worksheet.merge_range('A1:H1', 'VM Assessment Dashboard', formats['title'])
        worksheet.set_row(0, 30)
        
        # Create multiple charts side by side
        
        # 1. VM Size Distribution (Scatter plot)
        chart1 = workbook.add_chart({'type': 'scatter'})
        
        # Prepare data for scatter plot (CPU vs Memory)
        active_vms = [vm for vm in assessment.vms if vm.power_state == 'poweredOn']
        
        # We'll create a simple representation
        worksheet.write(2, 0, 'VM Sizing Analysis', formats['header'])
        
        # 2. Cost Trend Chart (if we have time-based data)
        chart2 = workbook.add_chart({'type': 'line'})
        chart2.set_title({'name': 'Projected Monthly Costs'})
        
        # Add sample trend data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        base_cost = bom.total_monthly_cost
        
        # Write sample data
        worksheet.write(10, 0, 'Month', formats['subheader'])
        worksheet.write(10, 1, 'Projected Cost', formats['subheader'])
        
        for i, month in enumerate(months):
            worksheet.write(11 + i, 0, month, formats['data'])
            # Add some variance to show growth
            cost = base_cost * (1 + i * 0.02)  # 2% monthly growth
            worksheet.write(11 + i, 1, cost, formats['currency'])
        
        chart2.add_series({
            'categories': f'=\'Charts Dashboard\'!$A$11:$A${11 + len(months) - 1}',
            'values': f'=\'Charts Dashboard\'!$B$11:$B${11 + len(months) - 1}',
            'name': 'Monthly Cost Projection'
        })
        
        worksheet.insert_chart(2, 2, chart2)
    
    def _create_detailed_bom(self, workbook, formats, bom: BillOfMaterials, 
                           assessment: VMAssessment):
        """Create detailed Bill of Materials with all line items"""
        worksheet = workbook.add_worksheet('Detailed BOM')
        
        # Set column widths for BOM
        worksheet.set_column('A:A', 25)  # Item Description
        worksheet.set_column('B:B', 15)  # VM Name
        worksheet.set_column('C:C', 10)  # Quantity
        worksheet.set_column('D:D', 12)  # Unit Cost
        worksheet.set_column('E:E', 15)  # Monthly Cost
        worksheet.set_column('F:F', 15)  # Annual Cost
        worksheet.set_column('G:G', 20)  # Category
        
        row = 0
        
        # Title
        worksheet.merge_range('A1:G1', 'Detailed Bill of Materials', formats['title'])
        worksheet.set_row(0, 25)
        row += 2
        
        # Headers
        headers = ['Description', 'VM Name', 'Quantity', 'Unit Cost', 
                  'Monthly Cost', 'Annual Cost', 'Category']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['header'])
        row += 1
        
        # BOM Line items
        current_vm = None
        vm_subtotal = 0
        
        for line in sorted(bom.lines, key=lambda x: getattr(x, 'vm_name', 'Unknown')):
            # Check if we're starting a new VM
            vm_name = getattr(line, 'vm_name', 'Unknown')
            if current_vm != vm_name:
                # Add subtotal for previous VM
                if current_vm is not None:
                    worksheet.write(row, 0, f'Subtotal for {current_vm}', formats['subheader'])
                    worksheet.write(row, 4, vm_subtotal, formats['currency'])
                    worksheet.write(row, 5, vm_subtotal * 12, formats['currency'])
                    row += 1
                
                current_vm = vm_name
                vm_subtotal = 0
            
            # Write line item
            worksheet.write(row, 0, line.description, formats['data'])
            worksheet.write(row, 1, vm_name, formats['data'])
            worksheet.write(row, 2, line.quantity, formats['number'])
            worksheet.write(row, 3, line.unit_cost, formats['currency'])
            worksheet.write(row, 4, line.monthly_cost, formats['currency'])
            worksheet.write(row, 5, line.monthly_cost * 12, formats['currency'])
            worksheet.write(row, 6, getattr(line, 'category', 'Compute'), formats['data'])
            
            vm_subtotal += line.monthly_cost
            row += 1
        
        # Final subtotal
        if current_vm is not None:
            worksheet.write(row, 0, f'Subtotal for {current_vm}', formats['subheader'])
            worksheet.write(row, 4, vm_subtotal, formats['currency'])
            worksheet.write(row, 5, vm_subtotal * 12, formats['currency'])
            row += 2
        
        # Grand total
        worksheet.write(row, 0, 'GRAND TOTAL', formats['total'])
        worksheet.write(row, 4, bom.total_monthly_cost, formats['total'])
        worksheet.write(row, 5, bom.total_monthly_cost * 12, formats['total'])
        
        # Add autofilter
        worksheet.autofilter(2, 0, row - 1, 6)
    
    def _calculate_os_distribution(self, assessment: VMAssessment, bom: BillOfMaterials) -> Dict[str, Dict]:
        """Calculate OS distribution statistics"""
        active_vms = [vm for vm in assessment.vms if vm.power_state == 'poweredOn']
        total_vms = len(active_vms)
        
        os_stats = {}
        
        for vm in active_vms:
            os_name = self._normalize_os_name(vm.guest_os)
            
            if os_name not in os_stats:
                os_stats[os_name] = {
                    'count': 0,
                    'vcpus': 0,
                    'memory_gb': 0,
                    'monthly_cost': 0
                }
            
            os_stats[os_name]['count'] += 1
            os_stats[os_name]['vcpus'] += vm.num_cpu
            os_stats[os_name]['memory_gb'] += vm.memory_mb / 1024
            
            # Find cost for this VM
            for line in bom.lines:
                if hasattr(line, 'vm_name') and line.vm_name == vm.vm_name:
                    os_stats[os_name]['monthly_cost'] += line.monthly_cost
        
        # Calculate percentages
        for os_name in os_stats:
            os_stats[os_name]['percentage'] = os_stats[os_name]['count'] / total_vms if total_vms > 0 else 0
        
        return os_stats
    
    def _calculate_cost_breakdown(self, bom: BillOfMaterials) -> Dict[str, Dict]:
        """Calculate cost breakdown by category"""
        breakdown = {}
        
        for line in bom.lines:
            category = getattr(line, 'category', 'Compute')
            
            if category not in breakdown:
                breakdown[category] = {
                    'monthly': 0,
                    'vm_count': 0
                }
            
            breakdown[category]['monthly'] += line.monthly_cost
            breakdown[category]['vm_count'] += 1
        
        return breakdown
    
    def _normalize_os_name(self, os_name: str) -> str:
        """Normalize OS names for better grouping"""
        if not os_name:
            return 'Unknown'
        
        os_lower = os_name.lower()
        
        if 'windows' in os_lower:
            return 'Windows'
        elif any(term in os_lower for term in ['linux', 'ubuntu', 'centos', 'rhel', 'suse', 'unix']):
            return 'Linux'
        elif 'vmware' in os_lower:
            return 'VMware'
        else:
            return 'Other'