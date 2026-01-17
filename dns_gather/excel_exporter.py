"""Excel export functionality for DNS-Gather"""

from datetime import datetime
from pathlib import Path
from typing import List
import re

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from dns_gather.models import ZoneInfo, DNSRecord


class ExcelExporter:
    """Exports DNS zone data to Excel workbooks"""
    
    def __init__(self, output_directory: str = './Reports'):
        """
        Initialize Excel Exporter
        
        Args:
            output_directory: Directory for output files
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Excel formatting settings
        self.header_bg_color = '4472C4'
        self.header_font_color = 'FFFFFF'
        self.max_column_width = 50
    
    def create_workbook(self, zones: List[ZoneInfo], records_by_zone: dict) -> str:
        """
        Create Excel workbook with zone data
        
        Args:
            zones: List of ZoneInfo objects
            records_by_zone: Dictionary mapping zone names to lists of DNSRecord objects
        
        Returns:
            Path to created workbook file
        """
        # Create workbook
        wb = Workbook()
        
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        # Create zone list sheet
        self.create_zone_list_sheet(wb, zones)
        
        # Create individual zone sheets
        for zone in zones:
            records = records_by_zone.get(zone.name, [])
            self.create_zone_sheet(wb, zone, records)
        
        # Generate filename with timestamp
        filename = self.generate_filename()
        filepath = self.output_directory / filename
        
        # Save workbook
        wb.save(filepath)
        
        return str(filepath)
    
    def create_zone_list_sheet(self, wb: Workbook, zones: List[ZoneInfo]) -> None:
        """
        Create zone list summary sheet
        
        Args:
            wb: Workbook object
            zones: List of ZoneInfo objects
        """
        ws = wb.create_sheet('Zone List', 0)
        
        # Headers
        headers = ['Zone Name', 'Type', 'Serial', 'Record Count', 'Transfer Status', 'Error Message']
        ws.append(headers)
        
        # Apply header formatting
        self.apply_formatting(ws, len(headers))
        
        # Add zone data
        for zone in zones:
            ws.append([
                zone.name,
                zone.zone_type,
                zone.serial,
                zone.record_count,
                zone.transfer_status,
                zone.error_message
            ])
        
        # Auto-adjust column widths
        self.auto_adjust_columns(ws)
    
    def create_zone_sheet(self, wb: Workbook, zone: ZoneInfo, records: List[DNSRecord]) -> None:
        """
        Create sheet for individual zone
        
        Args:
            wb: Workbook object
            zone: ZoneInfo object
            records: List of DNSRecord objects for this zone
        """
        # Sanitize sheet name for Excel compatibility
        sheet_name = self.sanitize_sheet_name(zone.name)
        
        ws = wb.create_sheet(sheet_name)
        
        # Headers
        headers = ['Name', 'Type', 'TTL', 'Data']
        ws.append(headers)
        
        # Apply header formatting
        self.apply_formatting(ws, len(headers))
        
        # Add record data
        for record in records:
            ws.append([
                record.name,
                record.record_type,
                record.ttl,
                record.data
            ])
        
        # Auto-adjust column widths
        self.auto_adjust_columns(ws)
    
    def sanitize_sheet_name(self, name: str) -> str:
        r"""
        Sanitize zone name for Excel sheet name compatibility
        
        Excel sheet names cannot contain: \ / ? * [ ] :
        Excel sheet names must be <= 31 characters
        
        Args:
            name: Original zone name
        
        Returns:
            Sanitized sheet name
        """
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[\\/*?:\[\]]', '_', name)
        
        # Truncate to 31 characters
        if len(sanitized) > 31:
            sanitized = sanitized[:31]
        
        # Remove trailing/leading spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'Zone'
        
        return sanitized
    
    def apply_formatting(self, ws, num_columns: int) -> None:
        """
        Apply formatting to header row
        
        Args:
            ws: Worksheet object
            num_columns: Number of columns to format
        """
        # Header row styling
        header_fill = PatternFill(start_color=self.header_bg_color, 
                                  end_color=self.header_bg_color, 
                                  fill_type='solid')
        header_font = Font(color=self.header_font_color, bold=True)
        header_alignment = Alignment(horizontal='left', vertical='center')
        
        for col in range(1, num_columns + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
    
    def auto_adjust_columns(self, ws) -> None:
        """
        Auto-adjust column widths based on content
        
        Args:
            ws: Worksheet object
        """
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass
            
            # Set column width with max limit
            adjusted_width = min(max_length + 2, self.max_column_width)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def generate_filename(self) -> str:
        """
        Generate timestamped filename
        
        Returns:
            Filename in format: DNS-Gather_YYYYMMDD-HH-MM.xlsx
        """
        timestamp = datetime.now().strftime('%Y%m%d-%H-%M')
        return f'DNS-Gather_{timestamp}.xlsx'
