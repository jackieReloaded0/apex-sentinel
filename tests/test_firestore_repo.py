"""
Firestore リポジトリの単体テスト (モック使用)
"""
from services.firestore_repo import FirestoreRepository, COLLECTION_NAME


def test_save_log(mocker):
    """Firestore へのログ保存が正しく呼び出されるかを検証"""
    mock_client = mocker.Mock()
    mock_collection = mocker.Mock()
    mock_doc = mocker.Mock()

    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc
    mocker.patch("google.cloud.firestore.Client", return_value=mock_client)

    repo = FirestoreRepository(project_id="test-project")
    log_data = {
        "target_url": "https://apex.oracle.com/test",
        "status_code": 200,
        "response_time_ms": 150,
        "is_healthy": True,
        "error_message": None,
    }

    doc_id = repo.save_log(log_data)

    assert doc_id is not None
    mock_client.collection.assert_called_with(COLLECTION_NAME)
    mock_doc.set.assert_called_once()
    saved_payload = mock_doc.set.call_args[0][0]
    assert saved_payload["status_code"] == 200
    assert saved_payload["is_healthy"] is True


def test_get_recent_logs(mocker):
    """直近のログ取得が DESC 順・リミット付きで実行されるかを検証"""
    mock_client = mocker.Mock()
    mock_collection = mocker.Mock()
    mock_query = mocker.Mock()
    mock_doc = mocker.Mock()
    mock_doc.to_dict.return_value = {
        "id": "20261122-120000",
        "status_code": 200,
        "is_healthy": True,
    }

    mock_client.collection.return_value = mock_collection
    mock_collection.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.stream.return_value = [mock_doc]
    mocker.patch("google.cloud.firestore.Client", return_value=mock_client)

    repo = FirestoreRepository(project_id="test-project")
    logs = repo.get_recent_logs(limit=5)

    assert len(logs) == 1
    assert logs[0]["status_code"] == 200
    mock_query.limit.assert_called_with(5)
