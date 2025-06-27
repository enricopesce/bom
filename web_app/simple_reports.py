"""
Simplified Report Generator for VM Assessment BOM Tool
Creates exactly 3 optimized output files: Excel, Text, and CSV
"""

import csv
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from models.vm_models import VMAssessment, BillOfMaterials, OSType


class SimplifiedReportGenerator:
    """Simplified report generator that creates exactly 3 files: Excel, Text, CSV"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_reports(self, bom: BillOfMaterials) -> Dict[str, str]:
        """
        Generate all three report formats
        
        Returns:
            Dict with file paths for each format
        """
        files = {}
        
        # Generate Excel report
        if EXCEL_AVAILABLE:
            excel_file = self.output_dir / "assessment_report.xlsx"
            self._generate_excel_report(bom, excel_file)
            files['excel'] = str(excel_file)
        
        # Generate Text report
        text_file = self.output_dir / "assessment_report.txt"
        self._generate_text_report(bom, text_file)
        files['text'] = str(text_file)
        
        # Generate CSV report
        csv_file = self.output_dir / "assessment_report.csv"
        self._generate_csv_report(bom, csv_file)
        files['csv'] = str(csv_file)
        
        return files
    
    def _generate_excel_report(self, bom: BillOfMaterials, output_file: Path):
        """Generate comprehensive Excel report with multiple sheets"""
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # 1. Summary Sheet
        self._create_summary_sheet(wb, bom)
        
        # 2. VM Details Sheet
        self._create_vm_details_sheet(wb, bom)
        
        # 3. Cost Breakdown Sheet
        self._create_cost_breakdown_sheet(wb, bom)
        
        # 4. BOM Lines Sheet
        self._create_bom_lines_sheet(wb, bom)
        
        # Save workbook
        wb.save(output_file)
    
    def _create_summary_sheet(self, wb, bom):
        """Create executive summary sheet"""
        ws = wb.create_sheet("Executive Summary", 0)
        
        # Header styling
        header_font = Font(size=16, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Title
        ws.merge_cells("A1:F1")
        ws["A1"] = "VM Assessment - Bill of Materials Report"
        ws["A1"].font = header_font
        ws["A1"].fill = header_fill
        ws["A1"].alignment = Alignment(horizontal="center")
        
        # Summary metrics
        ws["A3"] = "Report Generated:"
        ws["B3"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ws["A4"] = "Total VMs:"
        ws["B4"] = len(bom.vms)
        
        ws["A5"] = "Powered On VMs:"
        ws["B5"] = len([vm for vm in bom.vms if vm.is_powered_on])
        
        ws["A6"] = "Total Monthly Cost:"
        ws["B6"] = f"€{bom.total_monthly_cost:.2f}"
        
        ws["A7"] = "Currency:"
        ws["B7"] = bom.currency
        
        # OS Distribution
        ws["A9"] = "Operating System Distribution:"
        os_counts = {}
        for vm in bom.vms:
            os_name = vm.os_type.value if vm.os_type else "Unknown"
            os_counts[os_name] = os_counts.get(os_name, 0) + 1
        
        row = 10
        for os_name, count in os_counts.items():
            ws[f"A{row}"] = f"  {os_name}:"
            ws[f"B{row}"] = count
            row += 1
        
        # Cost breakdown by component
        ws[f"A{row + 1}"] = "Cost Breakdown by Component:"
        component_costs = {}
        for line in bom.lines:
            comp_type = line.component_type
            component_costs[comp_type] = component_costs.get(comp_type, 0) + line.total_cost
        
        row += 2
        for comp_type, cost in component_costs.items():
            ws[f"A{row}"] = f"  {comp_type}:"
            ws[f"B{row}"] = f"€{cost:.2f}"
            row += 1
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_vm_details_sheet(self, wb, bom):
        """Create detailed VM information sheet"""
        ws = wb.create_sheet("VM Details")
        
        # Headers
        headers = [
            "VM Name", "OS Type", "Power State", "CPU Cores", "Memory (GB)", 
            "Storage (GB)", "Network Adapters", "Monthly Cost (€)"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
        
        # VM data
        for row, vm in enumerate(bom.vms, 2):
            ws.cell(row=row, column=1, value=vm.name)
            ws.cell(row=row, column=2, value=vm.os_type.value if vm.os_type else "Unknown")
            ws.cell(row=row, column=3, value="Powered On" if vm.is_powered_on else "Powered Off")
            ws.cell(row=row, column=4, value=vm.cpu_cores)
            ws.cell(row=row, column=5, value=vm.memory_gb)
            ws.cell(row=row, column=6, value=vm.total_storage_gb)
            ws.cell(row=row, column=7, value=vm.network_adapters)
            
            # Calculate VM monthly cost
            vm_cost = sum(line.total_cost for line in bom.lines if line.vm_name == vm.name)
            ws.cell(row=row, column=8, value=vm_cost)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_cost_breakdown_sheet(self, wb, bom):
        """Create cost breakdown sheet"""
        ws = wb.create_sheet("Cost Breakdown")
        
        # Headers
        headers = [
            "VM Name", "Component Type", "Description", "Quantity", 
            "Unit", "Unit Price (€)", "Total Cost (€)"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
        
        # Cost data
        for row, line in enumerate(bom.lines, 2):
            ws.cell(row=row, column=1, value=line.vm_name)
            ws.cell(row=row, column=2, value=line.component_type)
            ws.cell(row=row, column=3, value=line.description)
            ws.cell(row=row, column=4, value=line.quantity)
            ws.cell(row=row, column=5, value=line.unit)
            ws.cell(row=row, column=6, value=line.unit_price)
            ws.cell(row=row, column=7, value=line.total_cost)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_bom_lines_sheet(self, wb, bom):
        """Create detailed BOM lines sheet"""
        ws = wb.create_sheet("BOM Lines")
        
        # Headers
        headers = [
            "VM Name", "Component", "Description", "Qty", "Unit", 
            "Unit Price", "Total", "Pricing Model", "Notes"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D4E6F1", end_color="D4E6F1", fill_type="solid")
        
        # BOM data grouped by VM
        current_vm = None
        row = 2
        
        # Sort lines by VM name for better organization
        sorted_lines = sorted(bom.lines, key=lambda x: x.vm_name)
        
        for line in sorted_lines:
            if current_vm != line.vm_name:
                if current_vm is not None:
                    # Add VM subtotal
                    ws.merge_cells(f"A{row}:F{row}")
                    vm_total = sum(l.total_cost for l in bom.lines if l.vm_name == current_vm)
                    ws[f"A{row}"] = f"VM SUBTOTAL:"
                    ws[f"G{row}"] = f"€{vm_total:.2f}"
                    ws[f"A{row}"].font = Font(bold=True)
                    ws[f"G{row}"].font = Font(bold=True)
                    row += 1
                    
                    # Add separator
                    for col in range(1, 10):
                        ws.cell(row=row, column=col, value="-" * 20)
                    row += 1
                
                current_vm = line.vm_name
            
            ws.cell(row=row, column=1, value=line.vm_name)
            ws.cell(row=row, column=2, value=line.component_type)
            ws.cell(row=row, column=3, value=line.description)
            ws.cell(row=row, column=4, value=f"{line.quantity:.2f}")
            ws.cell(row=row, column=5, value=line.unit)
            ws.cell(row=row, column=6, value=f"€{line.unit_price:.4f}")
            ws.cell(row=row, column=7, value=f"€{line.total_cost:.2f}")
            ws.cell(row=row, column=8, value=getattr(line, 'pricing_model', 'on-demand'))
            ws.cell(row=row, column=9, value=getattr(line, 'notes', ''))
            row += 1
        
        # Final VM subtotal
        if current_vm:
            ws.merge_cells(f"A{row}:F{row}")
            vm_total = sum(l.total_cost for l in bom.lines if l.vm_name == current_vm)
            ws[f"A{row}"] = f"VM SUBTOTAL:"
            ws[f"G{row}"] = f"€{vm_total:.2f}"
            ws[f"A{row}"].font = Font(bold=True)
            ws[f"G{row}"].font = Font(bold=True)
            row += 2
        
        # Grand total
        ws.merge_cells(f"A{row}:F{row}")
        ws[f"A{row}"] = "GRAND TOTAL:"
        ws[f"G{row}"] = f"€{bom.total_monthly_cost:.2f}"
        ws[f"A{row}"].font = Font(bold=True, size=14)
        ws[f"G{row}"].font = Font(bold=True, size=14)
        ws[f"A{row}"].fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
        ws[f"G{row}"].fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _generate_text_report(self, bom: BillOfMaterials, output_file: Path):
        """Generate human-readable text report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("VM ASSESSMENT - BILL OF MATERIALS REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Currency: {bom.currency}\n")
            f.write("\n")
            
            # Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total VMs: {len(bom.vms)}\n")
            f.write(f"Powered On VMs: {len([vm for vm in bom.vms if vm.is_powered_on])}\n")
            f.write(f"Total Monthly Cost: €{bom.total_monthly_cost:.2f}\n")
            f.write("\n")
            
            # OS Distribution
            os_counts = {}
            for vm in bom.vms:
                os_name = vm.os_type.value if vm.os_type else "Unknown"
                os_counts[os_name] = os_counts.get(os_name, 0) + 1
            
            f.write("Operating System Distribution:\n")
            for os_name, count in os_counts.items():
                f.write(f"  {os_name}: {count} VMs\n")
            f.write("\n")
            
            # Cost breakdown by VM
            f.write("DETAILED COST BREAKDOWN BY VM\n")
            f.write("-" * 80 + "\n")
            
            # Group lines by VM
            vm_lines = {}
            for line in bom.lines:
                if line.vm_name not in vm_lines:
                    vm_lines[line.vm_name] = []
                vm_lines[line.vm_name].append(line)
            
            for vm_name, lines in vm_lines.items():
                # Find VM details
                vm = next((v for v in bom.vms if v.name == vm_name), None)
                os_type = vm.os_type.value if vm and vm.os_type else "Unknown"
                
                f.write(f"\n{vm_name:<30} {os_type:<10}\n")
                f.write("-" * 80 + "\n")
                
                vm_total = 0
                for line in lines:
                    f.write(f"  {line.component_type:<20} {line.description:<35} ")
                    f.write(f"{line.quantity:>6.2f} {line.unit:<8} ")
                    f.write(f"€{line.unit_price:>8.4f} €{line.total_cost:>10.2f}\n")
                    vm_total += line.total_cost
                
                f.write(f"VM SUBTOTAL:{'':<55} €{vm_total:>10.2f}\n")
                f.write("-" * 80 + "\n")
            
            # Grand total
            f.write(f"\nGRAND TOTAL:{'':<60} €{bom.total_monthly_cost:>10.2f}\n")
            f.write("=" * 80 + "\n")
    
    def _generate_csv_report(self, bom: BillOfMaterials, output_file: Path):
        """Generate CSV report for analysis"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow([
                'VM_Name', 'OS_Type', 'Power_State', 'CPU_Cores', 'Memory_GB', 
                'Storage_GB', 'Network_Adapters', 'Component_Type', 'Component_Description',
                'Quantity', 'Unit', 'Unit_Price_EUR', 'Total_Cost_EUR', 'Pricing_Model'
            ])
            
            # Data rows
            for line in bom.lines:
                # Find corresponding VM
                vm = next((v for v in bom.vms if v.name == line.vm_name), None)
                
                if vm:
                    writer.writerow([
                        line.vm_name,
                        vm.os_type.value if vm.os_type else 'Unknown',
                        'Powered_On' if vm.is_powered_on else 'Powered_Off',
                        vm.cpu_cores,
                        vm.memory_gb,
                        vm.total_storage_gb,
                        vm.network_adapters,
                        line.component_type,
                        line.description,
                        line.quantity,
                        line.unit,
                        line.unit_price,
                        line.total_cost,
                        getattr(line, 'pricing_model', 'on-demand')
                    ])