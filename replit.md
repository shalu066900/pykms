# Overview

This repository contains **py-kms**, a Python-based KMS (Key Management Service) server emulator for testing and activating Microsoft Windows and Office products. It's a fork of the original SystemRage implementation, providing a local KMS server that can activate volume-licensed Microsoft products without requiring connection to Microsoft's servers. The project includes a web-based GUI for monitoring clients, viewing activation logs, and managing GVLK (Generic Volume License Key) products.

The system is designed for educational and testing purposes, allowing users to understand KMS protocol structure and test their own systems. It supports KMS protocol versions 4, 5, and 6, and can activate various versions of Windows (Vista through 11) and Office (2010-2021) products.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core KMS Server Architecture
The system follows a client-server model where the py-kms server acts as a KMS host that responds to activation requests from Microsoft products. The server implements the KMS protocol stack with multiple version support:

- **Protocol Handling**: Supports KMS v4, v5, and v6 protocols with appropriate encryption (AES) and authentication mechanisms
- **Request Processing**: Handles different request types through specialized classes (kmsRequestV4, kmsRequestV5, kmsRequestV6)
- **Response Generation**: Creates proper KMS responses with EPID (Enhanced Privacy ID) generation and hardware ID management
- **Multi-threading**: Uses Python's ThreadingMixIn for concurrent client handling

## Web Interface Architecture
The Flask-based web interface provides real-time monitoring and management capabilities:

- **Flask Application**: Simple web server running on port 5000 for Replit compatibility
- **Template System**: Uses Jinja2 templates with Bulma CSS framework for responsive UI
- **Real-time Data**: Displays server status, client connections, and activation logs
- **Product Database**: Shows available GVLK keys for different Microsoft products

## Database and Storage
The system uses SQLite for persistent data storage:

- **Client Tracking**: Stores information about connected clients, activation history, and machine IDs
- **Database Schema**: Maintains tables for client machines, activation requests, and timestamps
- **Optional Database**: SQLite support is optional and can be disabled for minimal installations

## Networking and Communication
The server implements flexible networking options:

- **Multi-address Support**: Can listen on multiple IP addresses simultaneously
- **IPv4/IPv6 Dual Stack**: Supports both IPv4 and IPv6 connections
- **Port Configuration**: Default port 1688 with configurable alternatives
- **Socket Management**: Uses selectors for efficient connection handling

## Security and Encryption
Implements Microsoft's KMS security model:

- **AES Encryption**: Different encryption keys and methods for v4, v5, and v6 protocols
- **HMAC Authentication**: Message authentication for v6 protocol
- **Salt Generation**: Random salt generation for request/response security
- **Hardware ID Management**: Configurable HWID for server identification

## Configuration Management
The system provides extensive configuration options:

- **Command Line Interface**: Full argument parsing for server configuration
- **Environment Variables**: Docker-compatible environment variable support
- **Logging System**: Configurable logging levels with file rotation support
- **Service Integration**: Support for systemd, Docker, and Kubernetes deployment

# External Dependencies

## Core Python Dependencies
- **Flask**: Web framework for the GUI interface
- **dnspython**: DNS resolution capabilities for KMS discovery
- **tzlocal**: Timezone handling for proper timestamp management

## Optional Dependencies
- **sqlite3**: Database functionality (built into Python, optional for minimal setups)
- **gunicorn**: WSGI HTTP server for production Flask deployments

## Development and Deployment Tools
- **Docker**: Containerization support with multi-architecture builds
- **Kubernetes/Helm**: Container orchestration with provided Helm charts
- **Sphinx**: Documentation generation system

## Microsoft Protocol Implementation
- **Custom Protocol Stack**: Implements Microsoft's RPC and KMS protocols without external libraries
- **Encryption Libraries**: Uses built-in Python cryptographic capabilities for AES encryption
- **UUID Generation**: Leverages Python's uuid module for client and server identification

The architecture is designed to be self-contained with minimal external dependencies, making it suitable for educational use and easy deployment across different environments.