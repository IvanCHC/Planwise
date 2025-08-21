from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import streamlit_app
from streamlit_app import download_investment_projection, download_retirement_projection


def test_download_investment_projection_calls_download_buttons():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    current_age = 30
    retirement_age = 65

    with patch("streamlit_app.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock(), None, None]
        download_investment_projection(df, current_age, retirement_age)
        assert mock_st.download_button.call_count == 2


def test_download_retirement_projection_calls_download_buttons():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    current_age = 30
    retirement_age = 65

    with patch("streamlit_app.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock(), None, None]
        download_retirement_projection(df, current_age, retirement_age)
        assert mock_st.download_button.call_count == 2
