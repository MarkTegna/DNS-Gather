# DNS-Gather

A Windows command-line tool for collecting DNS zone information and exporting it to Excel workbooks.

**Author:** Mark Oldham  
**Version:** 0.0.1  
**Platform:** Windows

## Features

- Connect to DNS servers with TCP/UDP support
- TSIG authentication support for secure zone transfers
- Automatic zone discovery
- AXFR zone transfers for all discovered zones
- Export zone data to formatted Excel workbooks
- Timestamped output files and logs
- ASCII-only logging for Windows compatibility
- Comprehensive error handling and reporting

## Requirements

- Windows operating system
- DNS server with zone transfer permissions
- Network connectivity to DNS server

## Installation

1. Download the latest release ZIP file from the releases page
2. Extract the ZIP file to your desired location
3. The package contains:
   - `DNS-Gather.exe` - The main executable
   - `DNS-Gather.ini` - Configuration file

## Configuration

Edit `DNS-Gather.ini` to configure the application:

### DNS Settings
```ini
[DNS]
server_address = 192.168.168.55
port = 53
timeout = 10
use_tcp = True
```

### Authentication (Optional)
```ini
[Authentication]
# Uncomment and configure for TSIG authentication
# tsig_keyname = your-key-name
# tsig_secret = your-base64-secret
# tsig_algorithm = hmac-sha256
```

### Output Settings
```ini
[Output]
output_directory = ./Reports
filename_format = DNS-Gather_%Y%m%d-%H-%M.xlsx
```

### Excel Formatting
```ini
[Excel]
header_bg_color = 4472C4
header_font_color = FFFFFF
auto_adjust_columns = True
max_column_width = 50
```

### Logging
```ini
[Logging]
log_level = INFO
log_directory = ./Logs
log_filename_format = DNS-Gather_%Y%m%d-%H-%M.log
```

## Usage

### Basic Usage

1. Open PowerShell or Command Prompt
2. Navigate to the DNS-Gather directory
3. Run the executable:
   ```powershell
   .\DNS-Gather.exe
   ```

### What It Does

1. **Connects** to the configured DNS server
2. **Discovers** all available DNS zones
3. **Transfers** zone data using AXFR
4. **Exports** data to an Excel workbook with:
   - Zone List sheet (summary of all zones)
   - Individual sheets for each zone with all DNS records

### Output

- **Excel File:** `./Reports/DNS-Gather_YYYYMMDD-HH-MM.xlsx`
- **Log File:** `./Logs/DNS-Gather_YYYYMMDD-HH-MM.log`

### Excel Workbook Structure

**Zone List Sheet:**
- Zone Name
- Type (Primary/Secondary/Stub/Forward)
- Serial Number
- Record Count
- Transfer Status
- Error Message (if any)

**Individual Zone Sheets:**
- Name (record name)
- Type (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV, etc.)
- TTL (Time To Live)
- Data (record data)

## Supported DNS Record Types

- A (IPv4 address)
- AAAA (IPv6 address)
- CNAME (Canonical name)
- MX (Mail exchange)
- NS (Name server)
- SOA (Start of authority)
- TXT (Text)
- PTR (Pointer)
- SRV (Service)
- And all other standard DNS record types

## Error Handling

The application handles various error conditions:
- Connection failures
- Timeout errors
- Zone transfer denials
- Invalid configurations
- Network issues

All errors are logged to the log file and displayed in the console.

## Troubleshooting

### Connection Issues
- Verify DNS server address and port
- Check network connectivity
- Ensure firewall allows DNS traffic (port 53)

### Zone Transfer Failures
- Verify zone transfer permissions on DNS server
- Check TSIG authentication if required
- Review log files for detailed error messages

### Permission Errors
- Ensure write permissions for Reports and Logs directories
- Run as administrator if necessary

## Development

### Building from Source

Requirements:
- Python 3.11+
- Dependencies: `pip install -r requirements.txt`

Build executable:
```powershell
# Clear Python cache
.\build_scripts\clear_python_cache.ps1

# Increment version (automatic build)
python build_scripts\increment_build.py auto

# Build executable
python build_scripts\build_executable.py

# Create distribution package
.\build_scripts\create_distribution.ps1
```

### Running Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/property/ -v
```

## License

Copyright (c) 2026 Mark Oldham. All rights reserved.

## Support

For issues, questions, or feature requests, please contact the author.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
