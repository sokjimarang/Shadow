"""Shadow E2E 파이프라인 모듈

실제 모듈만 사용하는 단순한 파이프라인 구조를 제공합니다.
"""

from shadow.pipeline.pipeline import Pipeline, PipelineResult, run_pipeline

__all__ = [
    "Pipeline",
    "PipelineResult",
    "run_pipeline",
]
