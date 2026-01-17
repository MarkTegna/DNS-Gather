"""Main application controller for DNS-Gather"""

import sys
from pathlib import Path
from datetime import datetime

from dns_gather.version import __version__, __author__
from dns_gather.config_manager import ConfigManager
from dns_gather.logger import ASCIILogger
from dns_gather.dns_manager import DNSManager
from dns_gather.zone_discovery import ZoneDiscovery
from dns_gather.zone_transfer import ZoneTransfer
from dns_gather.excel_exporter import ExcelExporter
from dns_gather.models import ApplicationState


class DNSGatherApp:
    """Main application controller"""
    
    def __init__(self, config_path: str = 'DNS-Gather.ini'):
        """
        Initialize DNS-Gather application
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigManager(config_path)
        self.config.validate_config()
        
        # Initialize logger with timestamped filename
        log_dir = Path(self.config.get('Logging', 'log_directory', './Logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H-%M')
        log_file = log_dir / f'DNS-Gather_{timestamp}.log'
        log_level = self.config.get('Logging', 'log_level', 'INFO')
        self.logger = ASCIILogger(log_file=str(log_file), log_level=log_level)
        
        # Initialize state
        self.state = ApplicationState(
            zones_discovered=0,
            zones_transferred=0,
            zones_failed=0,
            total_records=0,
            errors=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
    
    def run(self):
        """Run the DNS-Gather application"""
        try:
            self.display_welcome()
            
            # Get DNS servers from config or user
            dns_server = self.config.get('DNS', 'server_address')
            if not dns_server:
                dns_server = input("Enter DNS server address (for zone transfers): ").strip()
            
            # Get zone discovery server (may be different from transfer server)
            zone_discovery_server = self.config.get('DNS', 'zone_discovery_server', '')
            if not zone_discovery_server:
                zone_discovery_server = dns_server  # Use same server if not specified
            
            port = self.config.get('DNS', 'port', 53)
            timeout = self.config.get('DNS', 'timeout', 10)
            use_tcp = self.config.get('DNS', 'use_tcp', True)
            
            self.logger.info(f"Zone discovery server: {zone_discovery_server}:{port}")
            self.logger.info(f"Zone transfer server: {dns_server}:{port}")
            
            # Initialize DNS manager for zone transfers
            dns_manager = DNSManager(dns_server, port=port, timeout=timeout, use_tcp=use_tcp)
            
            # Initialize DNS manager for zone discovery (may be different server)
            if zone_discovery_server != dns_server:
                discovery_manager = DNSManager(zone_discovery_server, port=port, timeout=timeout, use_tcp=use_tcp)
                self.logger.info(f"Using separate server for zone discovery: {zone_discovery_server}")
            else:
                discovery_manager = dns_manager
            
            # Test connection to transfer server
            success, message = dns_manager.test_connection()
            if not success:
                self.logger.error(f"Connection failed to transfer server: {message}")
                print(f"\n[ERROR] Transfer server connection failed: {message}")
                return 1
            
            self.logger.log_operation("DNS Connection (Transfer)", "OK", message)
            print(f"[OK] Transfer server: {message}")
            
            # Test connection to discovery server (if different)
            if zone_discovery_server != dns_server:
                success, message = discovery_manager.test_connection()
                if not success:
                    self.logger.error(f"Connection failed to discovery server: {message}")
                    print(f"\n[ERROR] Discovery server connection failed: {message}")
                    return 1
                
                self.logger.log_operation("DNS Connection (Discovery)", "OK", message)
                print(f"[OK] Discovery server: {message}")
            
            # Discover zones using discovery server
            print("\n[+] Discovering DNS zones...")
            self.logger.info("Starting zone discovery")
            
            discovery = ZoneDiscovery(discovery_manager)
            zones = discovery.enumerate_zones()
            
            if not zones:
                self.logger.warning("No zones discovered")
                print("[WARN] No zones found")
                return 0
            
            self.logger.log_operation("Zone Discovery", "OK", f"Found {len(zones)} zones")
            print(f"[OK] Found {len(zones)} zones")
            
            # Transfer zones using transfer server
            print("\n[+] Transferring zone data...")
            self.logger.info("Starting zone transfers")
            
            transfer = ZoneTransfer(dns_manager)  # Use transfer server
            records_by_zone = {}
            
            for i, zone in enumerate(zones, 1):
                print(f"  [{i}/{len(zones)}] Transferring {zone.name}...", end='', flush=True)
                
                records, error = transfer.perform_axfr(zone.name)
                records_by_zone[zone.name] = records
                
                zone.record_count = len(records)
                if error:
                    zone.transfer_status = 'Failed'
                    zone.error_message = error
                    self.logger.warning(f"Zone transfer failed for {zone.name}: {error}")
                    print(f" [FAIL] {error}")
                else:
                    zone.transfer_status = 'Success'
                    self.logger.info(f"Zone transfer successful for {zone.name}: {len(records)} records")
                    print(f" [OK] {len(records)} records")
            
            # Export to Excel
            print("\n[+] Exporting to Excel...")
            self.logger.info("Starting Excel export")
            
            output_dir = self.config.get('Output', 'output_directory', './Reports')
            exporter = ExcelExporter(output_directory=output_dir)
            
            filepath = exporter.create_workbook(zones, records_by_zone)
            
            self.logger.log_operation("Excel Export", "OK", f"Created: {filepath}")
            print(f"[OK] Created: {filepath}")
            
            # Display summary
            self.display_summary(zones, filepath)
            
            return 0
            
        except KeyboardInterrupt:
            self.logger.warning("Operation cancelled by user")
            print("\n\n[WARN] Operation cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            print(f"\n[ERROR] Unexpected error: {str(e)}")
            return 1
    
    def display_welcome(self):
        """Display welcome message"""
        print("=" * 60)
        print(f"  DNS-Gather v{__version__}")
        print(f"  Author: {__author__}")
        print("=" * 60)
        print()
        
        self.logger.info(f"DNS-Gather v{__version__} started")
    
    def display_summary(self, zones, output_file):
        """
        Display summary of operations
        
        Args:
            zones: List of ZoneInfo objects
            output_file: Path to output Excel file
        """
        print("\n" + "=" * 60)
        print("  Summary")
        print("=" * 60)
        
        total_zones = len(zones)
        successful = sum(1 for z in zones if z.transfer_status == 'Success')
        failed = sum(1 for z in zones if z.transfer_status == 'Failed')
        total_records = sum(z.record_count for z in zones)
        
        print(f"  Total Zones:      {total_zones}")
        print(f"  Successful:       {successful}")
        print(f"  Failed:           {failed}")
        print(f"  Total Records:    {total_records}")
        print(f"  Output File:      {output_file}")
        print("=" * 60)
        print()
        
        self.logger.info(f"Summary: {total_zones} zones, {successful} successful, {failed} failed, {total_records} records")


def main():
    """Main entry point"""
    app = DNSGatherApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
