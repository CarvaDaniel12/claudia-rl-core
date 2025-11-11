"""
Flows module
"""
from .ultimate_platform_flow_V2 import UltimatePlatformFlowV2 as UltimatePlatformFlow
from .pipeline_flow import PipelineFlow
from .cleanup_flow import CleanupFlow
from .golden_path_master import GoldenPathMaster
from .inbox_message import InboxMessageFlow
from .base_flow import BaseFlow

__all__ = [
    'UltimatePlatformFlow',
    'PipelineFlow',
    'CleanupFlow',
    'GoldenPathMaster',
    'InboxMessageFlow',
    'BaseFlow'
]
