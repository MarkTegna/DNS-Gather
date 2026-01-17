# Design Document: DNS-Gather

## Overview

DNS-Gather is a Windows command-line application that connects to DNS servers, automatically enumerates all available zones using the Windows dnscmd command, performs zone transfers (AXFR) to collect DNS records, and exports the data to an Excel workbook. The application is built in Python and packaged as a standalone Windows executable.

The tool provides network administrators with an automated way to document DNS infrastructure without relying on PowerShell cmdlets. It uses the native Windows dnscmd command for zone discovery, the dnspython library for DNS operations, and openpyxl for Excel file generation.

The application supports dual-server configuration, allowing zone discovery from one DNS server (e.g., a primary DNS server) while performing zone transfers from another (e.g., a secondary DNS server with less restrictive transfer policies).

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   User Input    │
│  (CLI/Config)   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Main Controller│
│   (Orchestrator)│
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         v              v              v              v
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ DNS Manager  │ │Config Manager│ │Excel Exporter│ │Logger        │
│ (Discovery)  │ └──────────────┘ └──────────────┘ └──────────────┘
└──────┬───────┘
       │
┌──────────────┐
│ DNS Manager  │
│ (Transfer)   │
└──────┬───────┘
       │
       ├──────────────┬──────────────┐
       v              v              v
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Zone Discovery│ │Zone Transfer │ │DNS Connection│
└──────────────┘ └──────────────┘ └──────────────┘
```

### Dual-Server Architecture

DNS-Gather supports using separate DNS servers for zone discovery and zone transfers. This is useful when:

- **Zone discovery server** (e.g., 10.9.1.81): Primary DNS server that has the complete list of zones but may restrict zone transfers
- **Zone transfer server** (e.g., 192.168.168.55): Secondary DNS server or dedicated server with less restrictive AXFR policies

**Configuration**:
- `server_address`: DNS server for zone transfers (required)
- `zone_discovery_server`: DNS server for zone enumeration (optional, defaults to server_address)

**Workflow**:
1. Connect to zone_discovery_server (or server_address if not specified)
2. Use dnscmd to enumerate all zones from discovery server
3. Connect to server_address for zone transfers
4. Perform AXFR zone transfers from transfer server
5. Export collected data to Excel

### Component Interaction Flow

1. Main Controller initializes Config Manager and Logger
2. Main Controller reads DNS server configuration (server_address for transfers, zone_discovery_server for discovery)
3. DNS Manager establishes connection to zone discovery server
4. DNS Manager establishes connection to zone transfer server (if different)
5. Zone Discovery component enumerates all zones using dnscmd command
6. Zone Transfer component performs AXFR for each zone using transfer server
7. Excel Exporter creates workbook with zone list and individual zone sheets
8. Logger records all operations and errors

## Components and Interfaces

### 1. Main Controller

**Responsibility**: Orchestrates the overall workflow and coordinates between components.

**Interface**:
```python
class DNSGatherApp:
    def __init__(self, config_path: str)
    def run(self) -> int
    def display_welcome(self) -> None
    def display_summary(self, results: dict) -> None
```

**Key Methods**:
- `run()`: Main execution loop that coordinates all operations
- `display_welcome()`: Shows application banner with version and author
- `display_summary()`: Displays final statistics (zones found, records collected, errors)

### 2. Configuration Manager

**Responsibility**: Manages application configuration from .ini files.

**Interface**:
```python
class ConfigManager:
    def __init__(self, config_path: str)
    def load_config(self) -> dict
    def create_default_config(self) -> None
    def get(self, section: str, key: str, default: Any) -> Any
    def validate_config(self) -> bool
```

**Configuration Structure** (DNS-Gather.ini):
```ini
[DNS]
# DNS server address (IP or hostname) - used for zone transfers
server_address = 192.168.168.55
# Zone discovery server (optional) - if different from server_address
# Leave empty to use server_address for both discovery and transfers
zone_discovery_server = 10.9.1.81
# DNS server port (default: 53)
port = 53
# Connection timeout in seconds
timeout = 10
# Use TCP for queries (default: True for zone transfers)
use_tcp = True

[Authentication]
# TSIG key name (if required)
# tsig_keyname = 
# TSIG key secret (if required)
# tsig_secret = 
# TSIG algorithm (default: hmac-sha256)
# tsig_algorithm = hmac-sha256

[Output]
# Output directory for Excel files
output_directory = ./Reports
# Filename format (uses strftime format)
filename_format = DNS-Gather_%Y%m%d-%H-%M.xlsx

[Excel]
# Header row background color (hex)
header_bg_color = 4472C4
# Header row font color (hex)
header_font_color = FFFFFF
# Auto-adjust column widths
auto_adjust_columns = True
# Maximum column width
max_column_width = 50

[Logging]
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level = INFO
# Log directory
log_directory = ./Logs
# Log filename format (uses strftime format)
log_filename_format = DNS-Gather_%Y%m%d-%H-%M.log
```

### 3. DNS Manager

**Responsibility**: Handles all DNS operations including connection, zone discovery, and zone transfers.

**Interface**:
```python
class DNSManager:
    def __init__(self, server: str, port: int, timeout: int, use_tcp: bool)
    def connect(self) -> bool
    def set_tsig_key(self, keyname: str, secret: str, algorithm: str) -> None
    def discover_zones(self) -> List[ZoneInfo]
    def transfer_zone(self, zone_name: str) -> Zone
    def test_connection(self) -> bool
```

**Key Classes**:
```python
@dataclass
class ZoneInfo:
    name: str
    zone_type: str  # "Primary", "Secondary", "Stub", "Unknown"
    serial: int
    transfer_status: str  # "Success", "Denied", "Failed", "Pending"
    record_count: int
    error_message: str

@dataclass
class DNSRecord:
    name: str
    record_type: str  # A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV, etc.
    ttl: int
    data: str
```

### 4. Zone Discovery Component

**Responsibility**: Automatically enumerates all zones available on Windows DNS servers using dnscmd.

**Interface**:
```python
class ZoneDiscovery:
    def __init__(self, dns_manager: DNSManager)
    def enumerate_zones(self) -> List[ZoneInfo]
    def get_zone_metadata(self, zone_name: str) -> ZoneInfo
    def discover_zones_from_list(self, zone_names: List[str]) -> List[ZoneInfo]
```

**Implementation Notes**:
- Uses Windows dnscmd command for automatic zone enumeration
- Command: `dnscmd <server_ip> /EnumZones`
- Parses dnscmd output to extract zone names and types
- No PowerShell dependency required
- Skips special system zones (TrustAnchors, ..cache, ..roothints)
- Returns empty list if dnscmd is not available or fails
- Supports 30-second timeout to prevent hanging
- Gracefully handles errors without crashing

**dnscmd Output Format**:
```
Enumerated zone list:
    Zone count = 1885

 Zone name                      Type       Storage         Properties
 _msdcs.example.com             Primary    AD-Domain       Secure
 0.1.10.in-addr.arpa            Primary    AD-Domain       Secure Rev
 ...
```

**Parsing Logic**:
1. Execute `dnscmd server /EnumZones` using subprocess
2. Parse whitespace-separated columns
3. Extract zone name (column 1) and type (column 2)
4. Skip header lines and special zones
5. Create ZoneInfo objects for each zone

### 5. Zone Transfer Component

**Responsibility**: Performs AXFR zone transfers to collect all DNS records.

**Interface**:
```python
class ZoneTransfer:
    def __init__(self, dns_manager: DNSManager)
    def perform_axfr(self, zone_name: str) -> Tuple[List[DNSRecord], str]
    def parse_zone_data(self, zone: dns.zone.Zone) -> List[DNSRecord]
```

**Implementation Details**:
- Uses dnspython's `dns.query.xfr()` and `dns.zone.from_xfr()` functions
- Handles TSIG authentication if configured
- Gracefully handles zone transfer denials
- Supports all common DNS record types

### 6. Excel Exporter

**Responsibility**: Creates Excel workbooks with zone data.

**Interface**:
```python
class ExcelExporter:
    def __init__(self, config: dict)
    def create_workbook(self, zones: List[ZoneInfo], zone_data: Dict[str, List[DNSRecord]]) -> str
    def create_zone_list_sheet(self, workbook: Workbook, zones: List[ZoneInfo]) -> None
    def create_zone_sheet(self, workbook: Workbook, zone_name: str, records: List[DNSRecord]) -> None
    def sanitize_sheet_name(self, name: str) -> str
    def apply_formatting(self, worksheet: Worksheet) -> None
```

**Excel Structure**:

**Sheet 1: Zone List**
| Zone Name | Zone Type | Record Count | Transfer Status | Error Message |
|-----------|-----------|--------------|-----------------|---------------|
| example.com | Primary | 150 | Success | |
| test.local | Secondary | 75 | Denied | Transfer not allowed |

**Sheet 2+: Individual Zones** (one per zone)
| Record Name | Record Type | TTL | Data |
|-------------|-------------|-----|------|
| @ | SOA | 3600 | ns1.example.com. admin.example.com. 2024011601 3600 600 86400 3600 |
| @ | NS | 3600 | ns1.example.com. |
| www | A | 300 | 192.168.1.10 |
| mail | MX | 3600 | 10 mail.example.com. |

**Sheet Naming**:
- Sanitize zone names for Excel compatibility (max 31 chars, no special chars)
- Handle duplicate names by appending numbers
- Truncate long zone names intelligently

### 7. Logger

**Responsibility**: Provides comprehensive logging with ASCII-only output.

**Interface**:
```python
class ASCIILogger:
    def __init__(self, log_file: str, log_level: str)
    def info(self, message: str) -> None
    def warning(self, message: str) -> None
    def error(self, message: str) -> None
    def debug(self, message: str) -> None
    def log_operation(self, operation: str, status: str, details: str) -> None
```

**ASCII Character Mapping**:
- Box drawing: `+`, `-`, `|` instead of Unicode box characters
- Status indicators: `[OK]`, `[FAIL]`, `[WARN]` instead of ✓, ✗
- Progress: `[=====>    ]` instead of Unicode progress bars

## Data Models

### Zone Information Model
```python
@dataclass
class ZoneInfo:
    name: str                    # Zone name (e.g., "example.com")
    zone_type: str              # "Primary", "Secondary", "Stub", "Unknown"
    serial: int                 # SOA serial number
    transfer_status: str        # "Success", "Denied", "Failed", "Pending"
    record_count: int           # Number of records in zone
    error_message: str          # Error details if transfer failed
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Excel export"""
        return {
            'Zone Name': self.name,
            'Zone Type': self.zone_type,
            'Record Count': self.record_count,
            'Transfer Status': self.transfer_status,
            'Error Message': self.error_message
        }
```

### DNS Record Model
```python
@dataclass
class DNSRecord:
    name: str                   # Record name (e.g., "www", "@")
    record_type: str           # A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV
    ttl: int                   # Time to live in seconds
    data: str                  # Record data (varies by type)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Excel export"""
        return {
            'Record Name': self.name,
            'Record Type': self.record_type,
            'TTL': self.ttl,
            'Data': self.data
        }
```

### Application State Model
```python
@dataclass
class ApplicationState:
    zones_discovered: int
    zones_transferred: int
    zones_failed: int
    total_records: int
    errors: List[str]
    start_time: datetime
    end_time: datetime
    
    def get_summary(self) -> dict:
        """Generate summary statistics"""
        duration = (self.end_time - self.start_time).total_seconds()
        return {
            'zones_discovered': self.zones_discovered,
            'zones_transferred': self.zones_transferred,
            'zones_failed': self.zones_failed,
            'total_records': self.total_records,
            'duration_seconds': duration,
            'error_count': len(self.errors)
        }
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: DNS Connection Establishment
*For any* valid DNS server address (IP or hostname), when provided to the DNS Manager, the application should successfully establish a connection or return a descriptive error message.
**Validates: Requirements 1.3, 1.4**

### Property 2: TSIG Authentication Support
*For any* valid TSIG credentials (keyname, secret, algorithm), when configured, the DNS Manager should successfully authenticate with the DNS server.
**Validates: Requirements 1.5**

### Property 3: Zone Discovery Completeness
*For any* connected Windows DNS server, the zone discovery component should automatically enumerate all available zones using dnscmd and return complete metadata (name, type).
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 4: Zone Discovery Error Resilience
*For any* zone that fails during discovery or if dnscmd is unavailable, the application should log the error and continue processing without terminating.
**Validates: Requirements 2.4, 2.5, 2.8**

### Property 5: Zone Transfer Execution
*For any* discovered zone, the application should attempt an AXFR zone transfer to retrieve all DNS records.
**Validates: Requirements 3.1**

### Property 6: Record Type Collection Completeness
*For any* zone containing multiple record types (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV), the zone transfer should collect all record types present.
**Validates: Requirements 3.2**

### Property 7: Zone Transfer Error Resilience
*For any* zone transfer that is denied or fails, the application should log the error and continue processing remaining zones.
**Validates: Requirements 3.3**

### Property 8: Excel Workbook Creation
*For any* collected zone data (including empty results), the application should create a valid Excel workbook.
**Validates: Requirements 4.1**

### Property 9: Zone List Sheet Structure
*For any* created workbook, the first worksheet should be named "Zone List" and contain columns for zone name, zone type, record count, and transfer status.
**Validates: Requirements 4.2, 4.3**

### Property 10: Zone Sheet Creation
*For any* successfully transferred zone, the workbook should contain a corresponding worksheet with that zone's records.
**Validates: Requirements 4.4**

### Property 11: Zone Sheet Structure
*For any* zone worksheet, it should contain columns for record name, record type, TTL, and data.
**Validates: Requirements 4.5**

### Property 12: Sheet Name Sanitization
*For any* zone name, the corresponding worksheet name should be sanitized to comply with Excel naming rules (max 31 characters, no invalid characters like `:`, `\`, `/`, `?`, `*`, `[`, `]`).
**Validates: Requirements 4.6**

### Property 13: Timestamped Filename Format
*For any* saved Excel workbook, the filename should include a timestamp in YYYYMMDD-HH-MM format.
**Validates: Requirements 4.7**

### Property 14: Configuration File Reading
*For any* valid .ini configuration file, the application should successfully parse and apply the configuration values, including dual-server configuration (server_address and zone_discovery_server).
**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

### Property 15: Invalid Configuration Handling
*For any* invalid configuration value, the application should use the default value and log a warning without crashing.
**Validates: Requirements 5.5**

### Property 16: Error Logging Completeness
*For any* error that occurs during execution, the application should write a detailed log entry to the log file.
**Validates: Requirements 6.1, 6.4**

### Property 17: ASCII Character Compliance
*For any* log output or console output, all characters should be ASCII-compatible to prevent encoding errors on Windows.
**Validates: Requirements 6.2, 7.4**

### Property 18: Timestamped Log File Creation
*For any* application execution, a log file should be created with a timestamp in YYYYMMDD-HH-MM format.
**Validates: Requirements 6.3**

### Property 19: User-Friendly Error Messages
*For any* critical error, the application should display a user-friendly error message (not just a stack trace).
**Validates: Requirements 6.5**

## Error Handling

### Error Categories

1. **Connection Errors**
   - DNS server unreachable
   - Authentication failure
   - Network timeout
   - **Handling**: Display error message, log details, allow retry

2. **Zone Discovery Errors**
   - No zones found
   - Partial zone enumeration failure
   - **Handling**: Log error, continue with discovered zones

3. **Zone Transfer Errors**
   - Transfer denied (REFUSED)
   - Transfer timeout
   - Malformed zone data
   - **Handling**: Log error, mark zone as failed, continue with remaining zones

4. **Configuration Errors**
   - Missing configuration file → Create default
   - Invalid configuration values → Use defaults, log warning
   - Invalid file paths → Create directories if possible, otherwise use current directory

5. **Excel Export Errors**
   - Disk full
   - Permission denied
   - Invalid characters in data
   - **Handling**: Display error, log details, attempt to save to alternate location

6. **System Errors**
   - Out of memory
   - Disk I/O errors
   - **Handling**: Display critical error, save partial results if possible, exit gracefully

### Error Recovery Strategies

- **Graceful Degradation**: Continue operation with reduced functionality when non-critical errors occur
- **Retry Logic**: Implement exponential backoff for transient network errors
- **Partial Results**: Save successfully collected data even if some operations fail
- **User Notification**: Always inform user of errors with actionable information

### Logging Strategy

All errors are logged with:
- Timestamp
- Error severity (INFO, WARNING, ERROR, CRITICAL)
- Component that generated the error
- Detailed error message
- Stack trace (for unexpected errors)

## Testing Strategy

### Dual Testing Approach

The application will use both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both approaches are complementary and necessary for comprehensive correctness validation

### Unit Testing

Unit tests will focus on:

1. **Specific Examples**
   - Connecting to a known test DNS server
   - Parsing a sample zone file
   - Creating an Excel file with known data

2. **Edge Cases**
   - Empty zone list
   - Zone with no records
   - Zone names with special characters
   - Very long zone names (>31 characters)

3. **Error Conditions**
   - Connection timeout
   - Authentication failure
   - Zone transfer denial
   - Invalid configuration values

4. **Integration Points**
   - Config file creation and reading
   - Log file creation and writing
   - Excel file creation and formatting

### Property-Based Testing

Property-based tests will use the **Hypothesis** library for Python and will run a minimum of 100 iterations per test.

Each property test will:
- Generate random valid inputs
- Execute the operation
- Verify the property holds
- Be tagged with a comment referencing the design property

**Tag Format**: `# Feature: dns-zone-exporter, Property {number}: {property_text}`

**Property Test Coverage**:

1. **DNS Connection (Property 1)**
   - Generate random valid IP addresses and hostnames
   - Verify connection succeeds or returns descriptive error

2. **Zone Discovery (Property 3)**
   - Generate random zone configurations
   - Verify all zones are discovered with complete metadata

3. **Record Type Collection (Property 6)**
   - Generate zones with random combinations of record types
   - Verify all record types are collected

4. **Sheet Name Sanitization (Property 12)**
   - Generate random zone names with various special characters
   - Verify sanitized names comply with Excel rules

5. **Timestamp Format (Properties 13, 18)**
   - Generate random timestamps
   - Verify filenames match YYYYMMDD-HH-MM format

6. **ASCII Compliance (Property 17)**
   - Generate random log messages and console output
   - Verify all characters are ASCII-compatible

7. **Configuration Handling (Properties 14, 15)**
   - Generate random valid and invalid configuration values
   - Verify valid configs are applied, invalid configs use defaults

8. **Error Resilience (Properties 4, 7)**
   - Generate random error conditions during zone operations
   - Verify application continues processing remaining zones

### Test Environment

- **Mock DNS Server**: Use a mock DNS server for controlled testing
- **Test Zones**: Create test zones with known data for validation
- **File System Mocking**: Mock file operations for testing without disk I/O
- **Network Simulation**: Simulate network conditions (timeouts, failures)

### Testing Tools

- **pytest**: Test framework
- **Hypothesis**: Property-based testing library
- **pytest-mock**: Mocking framework
- **dnspython**: DNS library (also used in production)
- **openpyxl**: Excel library (also used in production)

### Continuous Testing

- Run unit tests on every code change
- Run property tests before commits
- Maintain test coverage above 80%
- Test on Windows environments (primary target platform)

## Implementation Notes

### Python Libraries

**Required Dependencies**:
- `dnspython>=2.6.0`: DNS operations, zone transfers
- `openpyxl>=3.1.0`: Excel file creation and manipulation
- `configparser`: Configuration file handling (standard library)
- `logging`: Logging functionality (standard library)
- `dataclasses`: Data models (standard library, Python 3.7+)

### Windows Executable Packaging

**Build Process**:
1. Clear Python bytecode cache (`clear_python_cache.ps1`)
2. Run PyInstaller with appropriate options
3. Test executable
4. Create distribution ZIP

**PyInstaller Configuration**:
```python
# build_spec.py
a = Analysis(
    ['dns_gather/main.py'],
    pathex=[],
    binaries=[],
    datas=[('DNS-Gather.ini', '.')],
    hiddenimports=['dns', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DNS-Gather',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### Version Management

Following the local version steering rules:
- Automatic builds: Increment letter suffix (0.0.1a, 0.0.1b, etc.)
- User builds: Remove letter, increment PATCH (0.0.2)
- Version stored in `dns_gather/version.py`

### File Structure

```
DNS-Gather/
├── dns_gather/
│   ├── __init__.py
│   ├── main.py                 # Main controller
│   ├── version.py              # Version information
│   ├── config_manager.py       # Configuration handling
│   ├── dns_manager.py          # DNS operations
│   ├── zone_discovery.py       # Zone enumeration
│   ├── zone_transfer.py        # AXFR operations
│   ├── excel_exporter.py       # Excel generation
│   ├── logger.py               # ASCII logging
│   └── models.py               # Data models
├── tests/
│   ├── unit/
│   │   ├── test_config_manager.py
│   │   ├── test_dns_manager.py
│   │   ├── test_zone_discovery.py
│   │   ├── test_zone_transfer.py
│   │   ├── test_excel_exporter.py
│   │   └── test_logger.py
│   └── property/
│       ├── test_properties_dns.py
│       ├── test_properties_excel.py
│       ├── test_properties_config.py
│       └── test_properties_logging.py
├── build_scripts/
│   ├── clear_python_cache.ps1
│   ├── build_executable.py
│   ├── increment_build.py
│   └── create_distribution.ps1
├── DNS-Gather.ini              # Configuration file
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
└── CHANGELOG.md                # Version history
```

### Performance Considerations

- **Streaming Zone Transfers**: Process zone data incrementally to handle large zones
- **Connection Pooling**: Reuse DNS connections when possible
- **Batch Excel Writing**: Write to Excel in batches to improve performance
- **Memory Management**: Clear processed zone data after writing to Excel
- **Progress Indicators**: Update progress every N records to avoid UI lag
- **Dual-Server Optimization**: Use separate servers to distribute load and avoid transfer restrictions

### Security Considerations

- **Credential Storage**: Never log TSIG secrets
- **Input Validation**: Validate all user inputs and configuration values
- **Error Messages**: Don't expose sensitive information in error messages
- **File Permissions**: Create output files with appropriate permissions
- **Network Timeouts**: Implement reasonable timeouts to prevent hanging

### Platform Requirements

- **Operating System**: Windows (required for dnscmd)
- **DNS Server**: Windows DNS Server (for zone discovery)
- **dnscmd**: Built-in Windows command-line tool (included with Windows DNS Server)
- **Network Access**: Connectivity to DNS servers
- **Permissions**: Sufficient permissions to query DNS servers and enumerate zones

### Zone Discovery Implementation Details

**dnscmd Command**:
```cmd
dnscmd <server_ip> /EnumZones
```

**Advantages**:
- No PowerShell dependency
- Native Windows tool
- Fast execution (~1 second for 1,885 zones)
- Standard DNS server permissions
- Simple and reliable

**Error Handling**:
- Timeout after 30 seconds
- Returns empty list if dnscmd not found
- Returns empty list if access denied
- Logs errors without crashing

**Tested Performance**:
- Server 10.9.1.81: 1,885 zones discovered in ~1 second
- Server 192.168.168.55: Multiple zones discovered in <1 second
- Success rate: 100% zone discovery
- Zone transfer success: 99.8% (1,881 of 1,885 zones)
