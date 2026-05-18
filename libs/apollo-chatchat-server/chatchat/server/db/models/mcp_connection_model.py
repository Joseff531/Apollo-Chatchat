from datetime import datetime
from typing import Dict, List, Optional, Union
from sqlalchemy import Boolean, Column, DateTime, Integer, String, JSON, Text, func

from chatchat.server.db.base import Base


class MCPConnectionModel(Base):
    """
    MCP connection configuration model - supports StdioConnection and SSEConnection types.
    """

    __tablename__ = "mcp_connection"

    # Basic information
    id = Column(String(32), primary_key=True, comment="MCP connection ID")
    server_name = Column(String(100), unique=True, nullable=False, comment="Server name")
    transport = Column(String(20), nullable=False, comment="Transport: stdio, sse")
    args = Column(JSON, default=[], comment="List of command arguments")
    env = Column(JSON, default={}, comment="Environment variable dictionary")
    cwd = Column(String(500), nullable=True, comment="Working directory")

    # Connection state
    timeout = Column(Integer, default=30, comment="Connection timeout (seconds)")
    enabled = Column(Boolean, default=True, comment="Whether the connection is enabled")
    description = Column(Text, nullable=True, comment="Connector description")

    # Transport-specific configuration
    config = Column(JSON, default={}, comment="Transport-specific configuration, including fields such as `command`")

    # Metadata
    last_connected_at = Column(DateTime, nullable=True, comment="Last connection time")
    connection_status = Column(String(50), default="disconnected", comment="Connection status")
    error_message = Column(Text, nullable=True, comment="Error message")

    create_time = Column(DateTime, default=func.now(), comment="Creation time")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Update time")

    def __repr__(self):
        return f"<MCPConnection(id='{self.id}', server_name='{self.server_name}', transport='{self.transport}', enabled={self.enabled})>"

    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "server_name": self.server_name,
            "transport": self.transport,
            "args": self.args or [],
            "env": self.env or {},
            "cwd": self.cwd,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "description": self.description,
            "config": self.config or {},
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "connection_status": self.connection_status,
            "error_message": self.error_message,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }



class MCPProfileModel(Base):
    """
    MCP global configuration model.
    """

    __tablename__ = "mcp_profile"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Configuration ID")
    timeout = Column(Integer, default=30, nullable=False, comment="Default connection timeout (seconds)")
    working_dir = Column(String(500), default="/tmp", nullable=False, comment="Default working directory")
    env_vars = Column(JSON, default={}, nullable=False, comment="Default environment variable configuration")
    create_time = Column(DateTime, default=func.now(), comment="Creation time")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Update time")

    def __repr__(self):
        return f"<MCPProfile(id={self.id}, timeout={self.timeout}, working_dir='{self.working_dir}', update_time='{self.update_time}')>"