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


def test_main_ui_calls():
    with patch("streamlit_app.st") as mock_st, patch(
        "streamlit_app.Image.open", return_value="favicon"
    ), patch("streamlit_app.sidebar_inputs", return_value=MagicMock()), patch(
        "streamlit_app.pw.project_investment", return_value=MagicMock()
    ), patch(
        "streamlit_app.pw.project_retirement", return_value=MagicMock()
    ), patch(
        "streamlit_app.render_pre_retirement_analysis"
    ), patch(
        "streamlit_app.render_post_retirement_analysis"
    ), patch(
        "streamlit_app.download_investment_projection"
    ), patch(
        "streamlit_app.download_retirement_projection"
    ):
        mock_tab_ctx = MagicMock()
        mock_st.tabs.return_value = [mock_tab_ctx, mock_tab_ctx]
        mock_tab_ctx.__enter__.return_value = None
        mock_tab_ctx.__exit__.return_value = None

        streamlit_app.main()

        mock_st.set_page_config.assert_called_once()
        mock_st.title.assert_called_once()
        mock_st.markdown.assert_called_once()
        mock_st.tabs.assert_called_once()
