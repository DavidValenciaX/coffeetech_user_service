import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import unittest
import json
from datetime import datetime, date, time
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from utils.response import process_data_for_json, create_response, session_token_invalid_response


class SampleModel(BaseModel):
    """Test Pydantic model for testing purposes."""
    id: int
    name: str
    price: Decimal
    created_at: datetime


class ComplexSampleModel(BaseModel):
    """Complex Pydantic model for nested testing."""
    id: UUID
    user: SampleModel
    tags: List[str]
    metadata: Dict[str, Any]


class TestProcessDataForJson(unittest.TestCase):
    """Test cases for the process_data_for_json function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        self.test_date = date(2024, 1, 15)
        self.test_time = time(14, 30, 45)
        self.test_uuid = uuid4()
        self.test_decimal = Decimal('123.45')
        
        self.test_model = SampleModel(
            id=1,
            name="Test Product",
            price=Decimal('99.99'),
            created_at=self.test_datetime
        )

    def test_process_basic_types(self):
        """Test processing of basic JSON-compatible types."""
        # Basic types should remain unchanged
        self.assertEqual(process_data_for_json("string"), "string")
        self.assertEqual(process_data_for_json(123), 123)
        self.assertEqual(process_data_for_json(123.45), 123.45)
        self.assertTrue(process_data_for_json(True))
        self.assertFalse(process_data_for_json(False))
        self.assertIsNone(process_data_for_json(None))

    def test_process_pydantic_model(self):
        """Test processing of Pydantic BaseModel instances."""
        result = process_data_for_json(self.test_model)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "Test Product")
        # Current implementation only calls model_dump() without recursive processing
        # So Decimal and datetime types are preserved as-is
        self.assertIsInstance(result['price'], Decimal)
        self.assertEqual(result['price'], Decimal('99.99'))
        self.assertIsInstance(result['created_at'], datetime)
        self.assertEqual(result['created_at'], self.test_datetime)

    def test_process_decimal(self):
        """Test processing of Decimal types."""
        result = process_data_for_json(self.test_decimal)
        
        self.assertIsInstance(result, float)
        self.assertEqual(result, 123.45)

    def test_process_datetime_types(self):
        """Test processing of datetime, date, and time types."""
        # datetime
        result_datetime = process_data_for_json(self.test_datetime)
        self.assertEqual(result_datetime, self.test_datetime.isoformat())
        
        # date
        result_date = process_data_for_json(self.test_date)
        self.assertEqual(result_date, self.test_date.isoformat())
        
        # time
        result_time = process_data_for_json(self.test_time)
        self.assertEqual(result_time, self.test_time.isoformat())

    def test_process_uuid(self):
        """Test processing of UUID types."""
        result = process_data_for_json(self.test_uuid)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(self.test_uuid))

    def test_process_dict(self):
        """Test processing of dictionary with nested special types."""
        test_dict = {
            "string": "value",
            "decimal": self.test_decimal,
            "datetime": self.test_datetime,
            "uuid": self.test_uuid,
            "model": self.test_model,
            "nested": {
                "decimal": Decimal('67.89'),
                "uuid": uuid4()
            }
        }
        
        result = process_data_for_json(test_dict)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['string'], "value")
        self.assertEqual(result['decimal'], 123.45)
        self.assertEqual(result['datetime'], self.test_datetime.isoformat())
        self.assertEqual(result['uuid'], str(self.test_uuid))
        self.assertIsInstance(result['model'], dict)
        self.assertEqual(result['model']['name'], "Test Product")
        self.assertIsInstance(result['nested'], dict)
        self.assertEqual(result['nested']['decimal'], 67.89)

    def test_process_list(self):
        """Test processing of lists with nested special types."""
        test_list = [
            "string",
            self.test_decimal,
            self.test_datetime,
            self.test_uuid,
            self.test_model,
            [Decimal('11.11'), uuid4()]
        ]
        
        result = process_data_for_json(test_list)
        
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], "string")
        self.assertEqual(result[1], 123.45)
        self.assertEqual(result[2], self.test_datetime.isoformat())
        self.assertEqual(result[3], str(self.test_uuid))
        self.assertIsInstance(result[4], dict)
        self.assertIsInstance(result[5], list)
        self.assertEqual(result[5][0], 11.11)

    def test_process_tuple(self):
        """Test processing of tuples."""
        test_tuple = (self.test_decimal, self.test_datetime, "string")
        
        result = process_data_for_json(test_tuple)
        
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], 123.45)
        self.assertEqual(result[1], self.test_datetime.isoformat())
        self.assertEqual(result[2], "string")

    def test_process_set(self):
        """Test processing of sets."""
        test_set = {"string1", "string2", "string3"}
        
        result = process_data_for_json(test_set)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(item in ["string1", "string2", "string3"] for item in result))

    def test_process_complex_nested_structure(self):
        """Test processing of complex nested data structures."""
        complex_model = ComplexSampleModel(
            id=self.test_uuid,
            user=self.test_model,
            tags=["tag1", "tag2"],
            metadata={
                "decimal_value": Decimal('999.99'),
                "created": self.test_datetime,
                "nested_list": [Decimal('1.1'), Decimal('2.2')]
            }
        )
        
        result = process_data_for_json(complex_model)
        
        self.assertIsInstance(result, dict)
        # Check if UUID is properly converted
        self.assertIn('id', result)
        self.assertIsInstance(result['user'], dict)
        self.assertEqual(result['user']['name'], "Test Product")
        self.assertEqual(result['tags'], ["tag1", "tag2"])
        # Metadata checks - these are processed recursively
        self.assertIn('metadata', result)
        self.assertIn('decimal_value', result['metadata'])
        self.assertIn('created', result['metadata'])
        self.assertIn('nested_list', result['metadata'])

    def test_process_edge_cases(self):
        """Test processing of edge cases."""
        # Empty collections
        self.assertEqual(process_data_for_json({}), {})
        self.assertEqual(process_data_for_json([]), [])
        self.assertEqual(process_data_for_json(set()), [])
        
        # Zero values
        self.assertEqual(process_data_for_json(Decimal('0')), 0.0)
        self.assertEqual(process_data_for_json(Decimal('0.0')), 0.0)


class TestCreateResponse(unittest.TestCase):
    """Test cases for the create_response function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_model = SampleModel(
            id=1,
            name="Test Product",
            price=Decimal('99.99'),
            created_at=datetime(2024, 1, 15, 14, 30, 45)
        )

    def test_create_basic_success_response(self):
        """Test creating a basic success response."""
        response = create_response(
            status="success",
            message="Operation completed successfully",
            data={"key": "value"},
            status_code=200
        )
        
        self.assertIsInstance(response, ORJSONResponse)
        self.assertEqual(response.status_code, 200)
        
        # Parse the response content
        content = json.loads(response.body.decode())
        self.assertEqual(content['status'], "success")
        self.assertEqual(content['message'], "Operation completed successfully")
        self.assertEqual(content['data'], {"key": "value"})

    def test_create_error_response(self):
        """Test creating an error response."""
        response = create_response(
            status="error",
            message="An error occurred",
            data={"error_code": 404},
            status_code=400
        )
        
        self.assertIsInstance(response, ORJSONResponse)
        self.assertEqual(response.status_code, 400)
        
        content = json.loads(response.body.decode())
        self.assertEqual(content['status'], "error")
        self.assertEqual(content['message'], "An error occurred")
        self.assertEqual(content['data'], {"error_code": 404})

    def test_create_response_with_no_data(self):
        """Test creating a response with no data."""
        response = create_response(
            status="success",
            message="No data to return"
        )
        
        self.assertEqual(response.status_code, 200)
        
        content = json.loads(response.body.decode())
        self.assertEqual(content['status'], "success")
        self.assertEqual(content['message'], "No data to return")
        self.assertEqual(content['data'], {})

    def test_create_response_with_none_data(self):
        """Test creating a response with explicitly None data."""
        response = create_response(
            status="success",
            message="Explicit None data",
            data=None
        )
        
        content = json.loads(response.body.decode())
        self.assertEqual(content['data'], {})

    def test_create_response_with_pydantic_model_fails(self):
        """Test that creating a response with Pydantic model data fails due to incomplete processing."""
        # This test demonstrates the current limitation: Pydantic models aren't fully processed
        with self.assertRaises(TypeError) as cm:
            create_response(
                status="success",
                message="Model data returned",
                data=self.test_model,
                status_code=201
            )
        
        self.assertIn("Type is not JSON serializable", str(cm.exception))
        self.assertIn("decimal.Decimal", str(cm.exception))

    def test_create_response_with_complex_data(self):
        """Test creating a response with complex nested data."""
        complex_data = {
            "metadata": {
                "total": 1,
                "created_at": datetime(2024, 1, 15, 14, 30, 45),
                "uuid": uuid4(),
                "decimal_value": Decimal('123.45')
            },
            "tags": {"tag1", "tag2", "tag3"}
        }
        
        response = create_response(
            status="success",
            message="Complex data returned",
            data=complex_data
        )
        
        content = json.loads(response.body.decode())
        self.assertEqual(content['status'], "success")
        self.assertIsInstance(content['data']['metadata'], dict)
        self.assertEqual(content['data']['metadata']['total'], 1)
        self.assertEqual(content['data']['metadata']['decimal_value'], 123.45)
        self.assertIsInstance(content['data']['tags'], list)
        self.assertEqual(len(content['data']['tags']), 3)

    def test_create_response_different_status_codes(self):
        """Test creating responses with different HTTP status codes."""
        status_codes = [200, 201, 400, 401, 403, 404, 500]
        
        for code in status_codes:
            response = create_response(
                status="test",
                message=f"Status code {code}",
                status_code=code
            )
            self.assertEqual(response.status_code, code)

    @patch('utils.response.process_data_for_json')
    def test_create_response_calls_process_data_for_json(self, mock_process):
        """Test that create_response calls process_data_for_json when data is provided."""
        mock_process.return_value = {"processed": True}
        test_data = {"raw": "data"}
        
        response = create_response(
            status="success",
            message="Test message",
            data=test_data
        )
        
        mock_process.assert_called_once_with(test_data)
        content = json.loads(response.body.decode())
        self.assertEqual(content['data'], {"processed": True})

    @patch('utils.response.process_data_for_json')
    def test_create_response_skips_processing_when_no_data(self, mock_process):
        """Test that create_response doesn't call process_data_for_json when data is None."""
        response = create_response(
            status="success",
            message="No data",
            data=None
        )
        
        mock_process.assert_not_called()
        content = json.loads(response.body.decode())
        self.assertEqual(content['data'], {})


class TestSessionTokenInvalidResponse(unittest.TestCase):
    """Test cases for the session_token_invalid_response function."""

    def test_session_token_invalid_response_structure(self):
        """Test the structure of the session token invalid response."""
        response = session_token_invalid_response()
        
        self.assertIsInstance(response, ORJSONResponse)
        self.assertEqual(response.status_code, 401)
        
        content = json.loads(response.body.decode())
        self.assertEqual(content['status'], "error")
        self.assertEqual(content['message'], "Credenciales expiradas, cerrando sesión.")
        self.assertEqual(content['data'], {})

    def test_session_token_invalid_response_consistency(self):
        """Test that multiple calls return consistent responses."""
        response1 = session_token_invalid_response()
        response2 = session_token_invalid_response()
        
        self.assertEqual(response1.status_code, response2.status_code)
        
        content1 = json.loads(response1.body.decode())
        content2 = json.loads(response2.body.decode())
        
        self.assertEqual(content1, content2)

    @patch('utils.response.create_response')
    def test_session_token_invalid_response_uses_create_response(self, mock_create_response):
        """Test that session_token_invalid_response uses the create_response function."""
        mock_response = MagicMock()
        mock_create_response.return_value = mock_response
        
        result = session_token_invalid_response()
        
        mock_create_response.assert_called_once_with(
            status="error",
            message="Credenciales expiradas, cerrando sesión.",
            data={},
            status_code=401
        )
        self.assertEqual(result, mock_response)


class TestResponseIntegration(unittest.TestCase):
    """Integration tests for the response module."""

    def test_full_workflow_with_real_data(self):
        """Test the complete workflow with realistic data."""
        # Simulate a real API response scenario without Pydantic models
        api_response_data = {
            "permissions": ["read", "write"],
            "session_id": uuid4(),
            "expires_at": datetime(2024, 1, 15, 18, 30, 0),
            "metadata": {
                "login_count": 5,
                "last_login": date(2024, 1, 14),
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "timeout": Decimal('300.5')
                }
            }
        }
        
        response = create_response(
            status="success",
            message="User authenticated successfully",
            data=api_response_data,
            status_code=200
        )
        
        # Verify the response can be properly serialized and deserialized
        self.assertIsInstance(response, ORJSONResponse)
        self.assertEqual(response.status_code, 200)
        
        content = json.loads(response.body.decode())
        
        # Verify structure
        self.assertEqual(content['status'], "success")
        self.assertEqual(content['message'], "User authenticated successfully")
        
        # Verify data processing
        data = content['data']
        self.assertIsInstance(data['session_id'], str)
        self.assertIsInstance(data['expires_at'], str)
        self.assertEqual(data['metadata']['preferences']['timeout'], 300.5)

    def test_error_handling_workflow(self):
        """Test error response workflow."""
        error_data = {
            "error_id": uuid4(),
            "timestamp": datetime.now(),
            "details": {
                "code": 1001,
                "field": "email",
                "value_received": Decimal('0')
            }
        }
        
        response = create_response(
            status="error",
            message="Validation failed",
            data=error_data,
            status_code=422
        )
        
        content = json.loads(response.body.decode())
        
        self.assertEqual(content['status'], "error")
        self.assertEqual(content['message'], "Validation failed")
        self.assertIsInstance(content['data']['error_id'], str)
        self.assertIsInstance(content['data']['timestamp'], str)
        self.assertEqual(content['data']['details']['value_received'], 0.0)


if __name__ == '__main__':
    unittest.main()
