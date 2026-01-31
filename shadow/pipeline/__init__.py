"""Shadow E2E 파이프라인 모듈

Mock/실제 구현을 교체 가능한 파이프라인 구조를 제공합니다.
"""

from shadow.pipeline.pipeline import Pipeline, PipelineResult
from shadow.pipeline.protocols import (
    AnalyzerProtocol,
    RecorderProtocol,
    ResponseHandlerProtocol,
    SlackClientProtocol,
)
from shadow.pipeline.mocks import (
    MockAnalyzer,
    MockRecorder,
    MockResponseHandler,
    MockSlackClient,
    create_mock_pipeline,
)

__all__ = [
    # Pipeline
    "Pipeline",
    "PipelineResult",
    # Protocols
    "RecorderProtocol",
    "AnalyzerProtocol",
    "SlackClientProtocol",
    "ResponseHandlerProtocol",
    # Mocks
    "MockRecorder",
    "MockAnalyzer",
    "MockSlackClient",
    "MockResponseHandler",
    "create_mock_pipeline",
]
