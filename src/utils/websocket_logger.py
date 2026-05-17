"""
WebSocket Logger Handler - Broadcasts log messages to connected WebSocket clients.
"""

import logging
from typing import List, Optional
from fastapi import WebSocket
import asyncio
import json
import threading


class WebSocketLogHandler(logging.Handler):
    """Custom logging handler that broadcasts to WebSocket clients."""
    
    def __init__(self, connection_manager=None):
        super().__init__()
        self.connection_manager = connection_manager
        self.log_queue = []
        self.queue_lock = threading.Lock()
    
    def emit(self, record):
        """Emit a log record to WebSocket clients."""
        try:
            log_entry = self.format(record)
            
            # Parse log level
            level_map = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'error'
            }
            
            log_type = level_map.get(record.levelname, 'info')
            
            # Extract structured information from log message
            message = {
                'type': 'log',
                'level': log_type,
                'message': record.getMessage(),
                'timestamp': record.created,
                'module': record.module
            }
            
            # Try to parse structured log messages
            msg = record.getMessage()
            
            # Check for subtask logs
            if '[SUBTASK' in msg:
                message['category'] = 'subtask'
                # Extract subtask ID
                if 'SUBTASK' in msg and ']' in msg:
                    try:
                        subtask_id = msg.split('[SUBTASK')[1].split(']')[0].strip()
                        message['subtask_id'] = subtask_id
                    except:
                        pass
            elif 'Retrieved:' in msg and 'similarity:' in msg:
                message['category'] = 'function_retrieval'
                # Parse function name and similarity
                try:
                    parts = msg.split('Retrieved:')[1].strip()
                    if '[' in parts and ']' in parts:
                        func_part = parts.split('[')[0].strip()
                        file_part = parts.split('[')[1].split(']')[0].strip()
                        sim_part = parts.split('similarity:')[1].strip() if 'similarity:' in parts else '0.0'
                        message['function_name'] = func_part
                        message['file_path'] = file_part
                        message['similarity'] = float(sim_part)
                except:
                    pass
            elif 'Semantic similarity threshold:' in msg:
                message['category'] = 'threshold'
                try:
                    threshold = msg.split(':')[-1].strip()
                    message['threshold'] = float(threshold)
                except:
                    pass
            elif 'Found' in msg and 'dependent file' in msg.lower():
                message['category'] = 'dependent_files'
            elif '[LLM VALIDATION]' in msg:
                message['category'] = 'llm_validation'
                message['report'] = msg.split('[LLM VALIDATION]')[1].strip()
            
            # Broadcast the message
            if self.connection_manager:
                self._broadcast_message(message)
                    
        except Exception as e:
            self.handleError(record)
    
    def _broadcast_message(self, message):
        """Broadcast message to all connected clients."""
        try:
            # Try to get the running event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine in the running loop
                asyncio.run_coroutine_threadsafe(
                    self.connection_manager.broadcast(message),
                    loop
                )
            else:
                # No loop running, queue the message
                with self.queue_lock:
                    self.log_queue.append(message)
        except RuntimeError:
            # No event loop at all, queue the message
            with self.queue_lock:
                self.log_queue.append(message)
    
    def flush_queue(self):
        """Flush queued messages (call this from async context)."""
        with self.queue_lock:
            messages = self.log_queue.copy()
            self.log_queue.clear()
        
        return messages


def setup_websocket_logging(connection_manager):
    """
    Setup WebSocket logging handler.
    
    Args:
        connection_manager: WebSocket connection manager
    """
    from src.utils.logger import get_logger
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Create and add WebSocket handler
    ws_handler = WebSocketLogHandler(connection_manager)
    ws_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ws_handler.setFormatter(formatter)
    
    root_logger.addHandler(ws_handler)
    
    return ws_handler


# Made with Bob