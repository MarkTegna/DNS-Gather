# Requirements Document

## Introduction

This document specifies the requirements for a Windows executable that connects to a DNS server, collects all available zones and their records, and exports the data to an Excel workbook. The tool provides DNS zone enumeration and zone transfer functionality without PowerShell dependencies, using pure Python DNS libraries.

## Glossary

- **DNS_Gather**: The DNS zone collection and export application (executable name: DNS-Gather.exe)
- **DNS_Server**: The Domain Name System server that hosts DNS zones
- **Zone**: A portion of the DNS namespace that is managed as a single administrative unit
- **Zone_Transfer**: The process of copying DNS records from a primary DNS server (AXFR protocol)
- **DNS_Record**: An individual entry in a DNS zone (A, AAAA, CNAME, MX, etc.)
- **Excel_Workbook**: An Excel file (.xlsx) containing multiple worksheets
- **Zone_List_Sheet**: The Excel worksheet containing a summary of all discovered zones
- **Zone_Sheet**: An individual Excel worksheet containing all records for a specific zone

## Requirements

### Requirement 1: DNS Server Connection

**User Story:** As a network administrator, I want to connect to DNS servers, so that I can retrieve zone information.

#### Acceptance Criteria

1. WHEN DNS_Gather starts, THE DNS_Gather SHALL prompt for DNS server address if not configured
2. WHEN DNS_Gather starts, THE DNS_Gather SHALL prompt for authentication credentials if required
3. WHEN a valid DNS server address is provided, THE DNS_Gather SHALL establish a connection to the DNS_Server
4. IF the connection fails, THEN THE DNS_Gather SHALL display a descriptive error message and allow retry
5. WHEN the DNS_Server requires authentication, THE DNS_Gather SHALL support credential-based authentication
6. THE DNS_Gather SHALL support separate servers for zone discovery and zone transfers
7. WHEN a zone_discovery_server is configured, THE DNS_Gather SHALL use it for zone enumeration
8. WHEN zone_discovery_server is not configured, THE DNS_Gather SHALL use server_address for both discovery and transfers

### Requirement 2: Zone Discovery

**User Story:** As a network administrator, I want to automatically discover all available DNS zones, so that I can enumerate what zones exist on the server without manual input.

#### Acceptance Criteria

1. WHEN connected to a Windows DNS_Server, THE DNS_Gather SHALL automatically enumerate all available zones using dnscmd
2. THE DNS_Gather SHALL use the dnscmd /EnumZones command to discover zones without PowerShell dependency
3. WHEN zones are discovered, THE DNS_Gather SHALL retrieve zone metadata (zone name, zone type)
4. IF no zones are found, THEN THE DNS_Gather SHALL display a message indicating no zones are available
5. WHEN zone discovery fails for a specific zone, THE DNS_Gather SHALL log the error and continue with remaining zones
6. THE DNS_Gather SHALL display progress information during zone discovery
7. THE DNS_Gather SHALL skip special system zones (TrustAnchors, ..cache, ..roothints)
8. IF dnscmd is not available, THE DNS_Gather SHALL return an empty zone list and log the error

### Requirement 3: Zone Transfer

**User Story:** As a network administrator, I want to perform zone transfers for each discovered zone, so that I can collect all DNS records.

#### Acceptance Criteria

1. WHEN a zone is discovered, THE DNS_Gather SHALL perform an AXFR zone transfer to retrieve all DNS_Records
2. WHEN performing zone transfers, THE DNS_Gather SHALL collect all record types (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR, SRV)
3. IF a zone transfer is denied, THEN THE DNS_Gather SHALL log the error and continue with remaining zones
4. WHEN zone transfers are in progress, THE DNS_Gather SHALL display progress information
5. THE DNS_Gather SHALL handle large zones without memory issues

### Requirement 4: Excel Workbook Generation

**User Story:** As a network administrator, I want DNS data exported to an Excel workbook, so that I can analyze and share the information easily.

#### Acceptance Criteria

1. WHEN all zone data is collected, THE DNS_Gather SHALL create an Excel_Workbook
2. THE DNS_Gather SHALL create a Zone_List_Sheet as the first worksheet
3. WHEN creating the Zone_List_Sheet, THE DNS_Gather SHALL include columns for zone name, zone type, record count, and transfer status
4. THE DNS_Gather SHALL create a separate Zone_Sheet for each successfully transferred zone
5. WHEN creating Zone_Sheets, THE DNS_Gather SHALL include columns for record name, record type, record data, and TTL
6. THE DNS_Gather SHALL name each Zone_Sheet using the zone name (sanitized for Excel compatibility)
7. WHEN the Excel_Workbook is complete, THE DNS_Gather SHALL save it with a timestamped filename using YYYYMMDD-HH-MM format
8. THE DNS_Gather SHALL display the output file location upon completion

### Requirement 5: Configuration Management

**User Story:** As a network administrator, I want to configure application settings, so that I can customize behavior without modifying code.

#### Acceptance Criteria

1. THE DNS_Gather SHALL read configuration from a .ini file
2. WHEN the .ini file does not exist, THE DNS_Gather SHALL create it with default values and all available options commented out
3. THE DNS_Gather SHALL support configuration of DNS server address for zone transfers (server_address)
4. THE DNS_Gather SHALL support configuration of optional zone discovery server (zone_discovery_server)
5. THE DNS_Gather SHALL support configuration of timeout values and output directory
6. THE DNS_Gather SHALL support configuration of Excel formatting options (header styles, column widths)
7. WHEN invalid configuration is detected, THE DNS_Gather SHALL use default values and log a warning

### Requirement 6: Error Handling and Logging

**User Story:** As a network administrator, I want comprehensive error handling and logging, so that I can troubleshoot issues.

#### Acceptance Criteria

1. WHEN errors occur, THE DNS_Gather SHALL log detailed error information to a log file
2. THE DNS_Gather SHALL use ASCII characters for log output to prevent Unicode encoding errors on Windows
3. WHEN DNS_Gather starts, THE DNS_Gather SHALL create a timestamped log file using YYYYMMDD-HH-MM format
4. THE DNS_Gather SHALL log all connection attempts, zone discoveries, and zone transfers
5. IF critical errors occur, THEN THE DNS_Gather SHALL display user-friendly error messages

### Requirement 7: User Interface

**User Story:** As a network administrator, I want a clear command-line interface, so that I can easily use the tool.

#### Acceptance Criteria

1. WHEN DNS_Gather starts, THE DNS_Gather SHALL display a welcome message with version and author information
2. THE DNS_Gather SHALL display progress indicators during long-running operations
3. WHEN operations complete, THE DNS_Gather SHALL display a summary of results (zones found, records collected, errors encountered)
4. THE DNS_Gather SHALL use ASCII characters for all console output to prevent encoding errors
5. THE DNS_Gather SHALL provide clear prompts for user input

### Requirement 8: Windows Executable Distribution

**User Story:** As a network administrator, I want a standalone Windows executable, so that I can run the tool without installing Python.

#### Acceptance Criteria

1. THE DNS_Gather SHALL be packaged as a Windows .exe file named DNS-Gather.exe
2. THE DNS_Gather SHALL include all required dependencies in the executable
3. WHEN distributed, THE DNS_Gather SHALL be packaged in a ZIP file with version number in the filename
4. THE DNS_Gather SHALL include the .ini configuration file in the distribution
5. THE DNS_Gather SHALL run on Windows without requiring Python installation
6. THE DNS_Gather SHALL display author name "Mark Oldham" in documentation and help output
7. THE DNS_Gather SHALL display version number and compile date in help output
