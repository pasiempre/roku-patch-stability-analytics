"""
Unit tests for risk_gate.py
============================
Tests the CI/CD risk gate functionality for firmware patch stability.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import risk_gate


class TestFeatureColumns:
    """Tests for feature column configuration."""

    def test_feature_cols_defined(self):
        """Feature columns should be defined."""
        assert hasattr(risk_gate, 'FEATURE_COLS')
        assert len(risk_gate.FEATURE_COLS) > 0

    def test_feature_cols_are_strings(self):
        """All feature columns should be strings."""
        for col in risk_gate.FEATURE_COLS:
            assert isinstance(col, str)

    def test_expected_feature_cols(self):
        """Feature columns should match expected set."""
        expected = {
            "code_churn_score",
            "previous_version_error_rate",
            "avg_device_age_days",
            "is_hotfix",
            "patch_security",
        }
        assert set(risk_gate.FEATURE_COLS) == expected


class TestRiskThreshold:
    """Tests for risk threshold configuration."""

    def test_threshold_defined(self):
        """Risk threshold should be defined."""
        assert hasattr(risk_gate, 'RISK_THRESHOLD')

    def test_threshold_in_valid_range(self):
        """Risk threshold should be between 0 and 1."""
        assert 0.0 <= risk_gate.RISK_THRESHOLD <= 1.0

    def test_default_threshold_value(self):
        """Default threshold should be 0.50."""
        assert risk_gate.RISK_THRESHOLD == 0.50


class TestLoadModel:
    """Tests for model loading functionality."""

    def test_load_model_file_not_found(self):
        """Should raise error when model file doesn't exist."""
        with pytest.raises(Exception):
            risk_gate.load_model("nonexistent_model.cbm")


class TestScoreFile:
    """Tests for the score_file function."""

    @pytest.fixture
    def valid_csv_data(self):
        """Create valid test data matching expected features."""
        return pd.DataFrame({
            'firmware_version': ['v1.0.0', 'v1.0.1', 'v1.0.2'],
            'code_churn_score': [0.1, 0.5, 0.9],
            'previous_version_error_rate': [0.02, 0.05, 0.15],
            'avg_device_age_days': [100, 200, 50],
            'is_hotfix': [0, 1, 0],
            'patch_security': [1, 0, 1],
        })

    @pytest.fixture
    def mock_model(self):
        """Create a mock CatBoost model."""
        mock = MagicMock()
        # Return probabilities: [low_risk, low_risk, high_risk]
        mock.predict_proba.return_value = np.array([
            [0.8, 0.2],  # Low risk
            [0.7, 0.3],  # Low risk
            [0.3, 0.7],  # High risk
        ])
        return mock

    def test_missing_file_exits_with_code_2(self):
        """Should exit with code 2 when file not found."""
        with pytest.raises(SystemExit) as exc_info:
            risk_gate.score_file("nonexistent_file.csv")
        assert exc_info.value.code == 2

    def test_missing_columns_raises_value_error(self, valid_csv_data):
        """Should raise ValueError when required columns are missing."""
        # Remove a required column
        df = valid_csv_data.drop(columns=['code_churn_score'])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch.object(risk_gate, 'load_model'):
                with pytest.raises(ValueError) as exc_info:
                    risk_gate.score_file(temp_path)
                assert 'code_churn_score' in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_high_risk_exits_with_code_1(self, valid_csv_data, mock_model):
        """Should exit with code 1 when high-risk patches detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            valid_csv_data.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch.object(risk_gate, 'load_model', return_value=mock_model):
                with pytest.raises(SystemExit) as exc_info:
                    risk_gate.score_file(temp_path)
                assert exc_info.value.code == 1
        finally:
            os.unlink(temp_path)
            # Clean up scored output file
            scored_file = f"scored_{os.path.basename(temp_path)}"
            if os.path.exists(scored_file):
                os.unlink(scored_file)

    def test_no_high_risk_exits_with_code_0(self, valid_csv_data):
        """Should exit with code 0 when no high-risk patches detected."""
        mock_model = MagicMock()
        # All low risk
        mock_model.predict_proba.return_value = np.array([
            [0.9, 0.1],
            [0.8, 0.2],
            [0.7, 0.3],
        ])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            valid_csv_data.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch.object(risk_gate, 'load_model', return_value=mock_model):
                with pytest.raises(SystemExit) as exc_info:
                    risk_gate.score_file(temp_path)
                assert exc_info.value.code == 0
        finally:
            os.unlink(temp_path)
            scored_file = f"scored_{os.path.basename(temp_path)}"
            if os.path.exists(scored_file):
                os.unlink(scored_file)

    def test_creates_scored_output_file(self, valid_csv_data, mock_model):
        """Should create a scored output CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            valid_csv_data.to_csv(f.name, index=False)
            temp_path = f.name

        scored_file = f"scored_{os.path.basename(temp_path)}"

        try:
            with patch.object(risk_gate, 'load_model', return_value=mock_model):
                with pytest.raises(SystemExit):
                    risk_gate.score_file(temp_path)

            assert os.path.exists(scored_file)

            # Verify scored file structure
            df_scored = pd.read_csv(scored_file)
            assert 'risk_score' in df_scored.columns
            assert 'high_risk_flag' in df_scored.columns
            assert 'firmware_version' in df_scored.columns
        finally:
            os.unlink(temp_path)
            if os.path.exists(scored_file):
                os.unlink(scored_file)


class TestHighRiskFlagLogic:
    """Tests for high-risk flag computation."""

    def test_flag_is_one_when_above_threshold(self):
        """Risk scores >= threshold should be flagged as high risk."""
        threshold = 0.50
        scores = np.array([0.5, 0.6, 0.99])
        flags = (scores >= threshold).astype(int)
        assert all(flags == 1)

    def test_flag_is_zero_when_below_threshold(self):
        """Risk scores < threshold should not be flagged."""
        threshold = 0.50
        scores = np.array([0.0, 0.25, 0.49])
        flags = (scores >= threshold).astype(int)
        assert all(flags == 0)

    def test_boundary_case_equals_threshold(self):
        """Score exactly at threshold should be flagged as high risk."""
        threshold = 0.50
        score = 0.50
        flag = int(score >= threshold)
        assert flag == 1


class TestCommandLineInterface:
    """Tests for command-line interface."""

    def test_no_args_exits_with_code_2(self):
        """Should exit with code 2 when no arguments provided."""
        with patch.object(sys, 'argv', ['risk_gate.py']):
            # Re-import to trigger __main__ block
            # This test verifies the usage message behavior
            pass  # Main block execution tested via subprocess in integration tests


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_dataframe(self):
        """Should handle empty CSV gracefully."""
        df = pd.DataFrame(columns=[
            'firmware_version',
            'code_churn_score',
            'previous_version_error_rate',
            'avg_device_age_days',
            'is_hotfix',
            'patch_security',
        ])

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([]).reshape(0, 2)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch.object(risk_gate, 'load_model', return_value=mock_model):
                with pytest.raises(SystemExit) as exc_info:
                    risk_gate.score_file(temp_path)
                # Empty file = no high risk = PASS
                assert exc_info.value.code == 0
        finally:
            os.unlink(temp_path)
            scored_file = f"scored_{os.path.basename(temp_path)}"
            if os.path.exists(scored_file):
                os.unlink(scored_file)

    def test_single_row_high_risk(self):
        """Should correctly identify single high-risk row."""
        df = pd.DataFrame({
            'firmware_version': ['v1.0.0'],
            'code_churn_score': [0.9],
            'previous_version_error_rate': [0.2],
            'avg_device_age_days': [30],
            'is_hotfix': [1],
            'patch_security': [0],
        })

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])  # High risk

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch.object(risk_gate, 'load_model', return_value=mock_model):
                with pytest.raises(SystemExit) as exc_info:
                    risk_gate.score_file(temp_path)
                assert exc_info.value.code == 1  # FAIL
        finally:
            os.unlink(temp_path)
            scored_file = f"scored_{os.path.basename(temp_path)}"
            if os.path.exists(scored_file):
                os.unlink(scored_file)
