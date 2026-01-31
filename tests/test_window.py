"""WindowInfoCollector 단위 테스트"""

import pytest

from shadow.capture.models import WindowInfo
from shadow.capture.window import WindowInfoCollector, get_active_window


def test_window_collector_initialization():
    """초기화 테스트"""
    collector = WindowInfoCollector()
    assert collector._workspace is not None


def test_get_active_window():
    """활성 윈도우 정보 가져오기"""
    collector = WindowInfoCollector()
    info = collector.get_active_window()

    assert isinstance(info, WindowInfo)
    assert info.app_name is not None
    assert len(info.app_name) > 0


def test_window_info_has_app_name():
    """app_name 필드 존재 확인 (F-03 Pass 조건)"""
    collector = WindowInfoCollector()
    info = collector.get_active_window()

    assert hasattr(info, "app_name")
    assert info.app_name is not None


def test_window_info_has_window_title():
    """window_title 필드 존재 확인 (F-03 Pass 조건)"""
    collector = WindowInfoCollector()
    info = collector.get_active_window()

    assert hasattr(info, "window_title")
    assert info.window_title is not None


def test_window_info_fields():
    """WindowInfo 필드 확인"""
    collector = WindowInfoCollector()
    info = collector.get_active_window()

    # F-03 필수 필드
    assert hasattr(info, "app_name")
    assert hasattr(info, "window_title")

    # 추가 필드
    assert hasattr(info, "bundle_id")
    assert hasattr(info, "process_id")


def test_is_available():
    """플랫폼 지원 확인"""
    is_available = WindowInfoCollector.is_available()
    assert isinstance(is_available, bool)
    # macOS에서 테스트하므로 True여야 함
    assert is_available is True


def test_get_active_window_function():
    """편의 함수 get_active_window() 테스트"""
    info = get_active_window()

    assert isinstance(info, WindowInfo)
    assert info.app_name is not None
    assert info.window_title is not None
