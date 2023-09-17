import io
from typing import Any, Dict

import pytest
from pytest import raises
from pytest_mock import MockerFixture

from langchain.document_loaders.json_loader import JSONLoader
from langchain.schema.document import Document

pytestmark = pytest.mark.requires("jq")


def test_load_valid_string_content(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="value1",
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content="value2",
            metadata={"source": file_path, "seq_num": 2},
        ),
    ]

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "pathlib.Path.read_text",
        return_value='[{"text": "value1"}, {"text": "value2"}]',
    )

    loader = JSONLoader(file_path=file_path, jq_schema=".[].text", text_content=True)
    result = loader.load()

    assert result == expected_docs


def test_load_valid_dict_content(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content='{"text": "value1"}',
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content='{"text": "value2"}',
            metadata={"source": file_path, "seq_num": 2},
        ),
    ]

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "pathlib.Path.read_text",
        return_value="""
            [{"text": "value1"}, {"text": "value2"}]
        """,
    )

    loader = JSONLoader(file_path=file_path, jq_schema=".[]", text_content=False)
    result = loader.load()

    assert result == expected_docs


def test_load_valid_bool_content(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="False",
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content="True",
            metadata={"source": file_path, "seq_num": 2},
        ),
    ]

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "pathlib.Path.read_text",
        return_value="""
            [
                {"flag": false}, {"flag": true}
            ]
        """,
    )

    loader = JSONLoader(file_path=file_path, jq_schema=".[].flag", text_content=False)
    result = loader.load()

    assert result == expected_docs


def test_load_valid_numeric_content(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="99",
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content="99.5",
            metadata={"source": file_path, "seq_num": 2},
        ),
    ]

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "pathlib.Path.read_text",
        return_value="""
            [
                {"num": 99}, {"num": 99.5}
            ]
        """,
    )

    loader = JSONLoader(file_path=file_path, jq_schema=".[].num", text_content=False)
    result = loader.load()

    assert result == expected_docs


def test_load_invalid_test_content(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(
        "pathlib.Path.read_text",
        return_value="""
            [{"text": "value1"}, {"text": "value2"}]
        """,
    )

    loader = JSONLoader(file_path=file_path, jq_schema=".[]", text_content=True)

    with raises(ValueError):
        loader.load()


def test_load_jsonlines(mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="value1",
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content="value2",
            metadata={"source": file_path, "seq_num": 2},
        ),
    ]

    mocker.patch(
        "pathlib.Path.open",
        return_value=io.StringIO(
            """
            {"text": "value1"}
            {"text": "value2"}
            """
        ),
    )

    loader = JSONLoader(
        file_path=file_path, jq_schema=".", content_key="text", json_lines=True
    )
    result = loader.load()

    assert result == expected_docs


@pytest.mark.parametrize(
    "params",
    (
        {"jq_schema": ".[].text"},
        {"jq_schema": ".[]", "content_key": "text"},
    ),
)
def test_load_jsonlines_list(params: Dict, mocker: MockerFixture) -> None:
    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="value1",
            metadata={"source": file_path, "seq_num": 1},
        ),
        Document(
            page_content="value2",
            metadata={"source": file_path, "seq_num": 2},
        ),
        Document(
            page_content="value3",
            metadata={"source": file_path, "seq_num": 3},
        ),
        Document(
            page_content="value4",
            metadata={"source": file_path, "seq_num": 4},
        ),
    ]

    mocker.patch(
        "pathlib.Path.open",
        return_value=io.StringIO(
            """
            [{"text": "value1"}, {"text": "value2"}]
            [{"text": "value3"}, {"text": "value4"}]
            """
        ),
    )

    loader = JSONLoader(file_path=file_path, json_lines=True, **params)
    result = loader.load()

    assert result == expected_docs


def test_load_empty_jsonlines(mocker: MockerFixture) -> None:
    mocker.patch("pathlib.Path.open", return_value=io.StringIO(""))

    loader = JSONLoader(file_path="file_path", jq_schema=".[].text", json_lines=True)
    result = loader.load()

    assert result == []


@pytest.mark.parametrize(
    "patch_func,patch_func_value,kwargs",
    (
        # JSON content.
        (
            "pathlib.Path.read_text",
            '[{"text": "value1"}, {"text": "value2"}]',
            {"jq_schema": ".[]", "content_key": "text"},
        ),
        # JSON Lines content.
        (
            "pathlib.Path.open",
            io.StringIO(
                """
                {"text": "value1"}
                {"text": "value2"}
                """
            ),
            {"jq_schema": ".", "content_key": "text", "json_lines": True},
        ),
    ),
)
def test_json_meta_01(
    patch_func: str, patch_func_value: Any, kwargs: Dict, mocker: MockerFixture
) -> None:
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(patch_func, return_value=patch_func_value)

    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="value1",
            metadata={"source": file_path, "seq_num": 1, "x": "value1-meta"},
        ),
        Document(
            page_content="value2",
            metadata={"source": file_path, "seq_num": 2, "x": "value2-meta"},
        ),
    ]

    def metadata_func(record: Dict, metadata: Dict) -> Dict:
        metadata["x"] = f"{record['text']}-meta"
        return metadata

    loader = JSONLoader(file_path=file_path, metadata_func=metadata_func, **kwargs)
    result = loader.load()

    assert result == expected_docs


@pytest.mark.parametrize(
    "patch_func,patch_func_value,kwargs",
    (
        # JSON content.
        (
            "pathlib.Path.read_text",
            '[{"text": "value1"}, {"text": "value2"}]',
            {"jq_schema": ".[]", "content_key": "text"},
        ),
        # JSON Lines content.
        (
            "pathlib.Path.open",
            io.StringIO(
                """
                        {"text": "value1"}
                        {"text": "value2"}
                        """
            ),
            {"jq_schema": ".", "content_key": "text", "json_lines": True},
        ),
    ),
)
def test_json_meta_02(
    patch_func: str, patch_func_value: Any, kwargs: Dict, mocker: MockerFixture
) -> None:
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch(patch_func, return_value=patch_func_value)

    file_path = "/workspaces/langchain/test.json"
    expected_docs = [
        Document(
            page_content="value1",
            metadata={"source": file_path, "seq_num": 1, "x": "value1-meta"},
        ),
        Document(
            page_content="value2",
            metadata={"source": file_path, "seq_num": 2, "x": "value2-meta"},
        ),
    ]

    def metadata_func(record: Dict, metadata: Dict) -> Dict:
        return {**metadata, "x": f"{record['text']}-meta"}

    loader = JSONLoader(file_path=file_path, metadata_func=metadata_func, **kwargs)
    result = loader.load()

    assert result == expected_docs
