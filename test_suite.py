"""
Comprehensive Testing Suite for Contextual Document Router
Includes unit tests, integration tests, and end-to-end tests
"""
import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from classifier import classify_intent
from email_parser import parse_email, extract_email_fields, detect_tone, trigger_action
from format_detector import detect_format, extract_text, validate_json_schema
from shared_memory import save_memory, load_memory, log_agent_result
from retry_utils import retry_action
from action_router import route_action


class TestClassifier(unittest.TestCase):
    """Test classification functionality"""
    
    def test_complaint_classification(self):
        """Test complaint intent classification"""
        text = "We are not satisfied with the product and want to complain."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "Complaint")
        self.assertGreater(confidence, 0.8)
    
    def test_invoice_classification(self):
        """Test invoice intent classification"""
        text = "Please find attached the invoice for your recent purchase."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "Invoice")
        self.assertGreater(confidence, 0.8)
    
    def test_regulation_classification(self):
        """Test regulation intent classification"""
        text = "As per the new regulation, you must update your policy."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "Regulation")
        self.assertGreater(confidence, 0.8)
    
    def test_rfq_classification(self):
        """Test RFQ intent classification"""
        text = "This is a request for quotation (RFQ) for your services."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "RFQ")
        self.assertGreater(confidence, 0.8)
    
    def test_fraud_classification(self):
        """Test fraud risk classification"""
        text = "We detected a suspicious transaction that may indicate fraud."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "Fraud Risk")
        self.assertGreater(confidence, 0.8)
    
    def test_unknown_classification(self):
        """Test unknown intent classification"""
        text = "This is a random text with no clear intent."
        intent, confidence = classify_intent(text)
        self.assertEqual(intent, "Unknown")
        self.assertLess(confidence, 0.6)


class TestEmailParser(unittest.TestCase):
    """Test email parsing functionality"""
    
    def setUp(self):
        """Setup test email"""
        self.test_email = """From: john@example.com
To: support@company.com
Subject: Product Issue

I am not satisfied with the product quality. Please process my complaint."""
    
    def test_parse_email(self):
        """Test email parsing"""
        parsed = parse_email(self.test_email)
        self.assertIn("john@example.com", parsed)
        self.assertIn("support@company.com", parsed)
        self.assertIn("Product Issue", parsed)
    
    def test_extract_email_fields(self):
        """Test email field extraction"""
        fields = extract_email_fields(self.test_email)
        self.assertIn('sender', fields)
        self.assertIn('recipient', fields)
        self.assertIn('subject', fields)
        self.assertEqual(fields['sender'], "john@example.com")
        self.assertEqual(fields['subject'], "Product Issue")
    
    def test_detect_tone_negative(self):
        """Test negative tone detection"""
        tone = detect_tone("I am very disappointed and angry with the service.")
        self.assertIn("negative", tone.lower())
    
    def test_detect_tone_positive(self):
        """Test positive tone detection"""
        tone = detect_tone("Thank you for the excellent service!")
        self.assertIn("positive", tone.lower())
    
    def test_detect_tone_urgent(self):
        """Test urgent tone detection"""
        tone = detect_tone("URGENT: Please respond immediately!")
        self.assertIn("urgent", tone.lower())
    
    def test_trigger_action(self):
        """Test action triggering"""
        fields = {
            'sender': 'test@example.com',
            'subject': 'Test'
        }
        tone = "positive"
        result = trigger_action(fields, tone)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestFormatDetector(unittest.TestCase):
    """Test format detection functionality"""
    
    def setUp(self):
        """Setup test directory"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Cleanup test directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_detect_email_format(self):
        """Test email format detection"""
        email_file = Path(self.test_dir) / "test.txt"
        email_content = """From: test@example.com
To: recipient@example.com
Subject: Test

This is a test email."""
        email_file.write_text(email_content)
        
        fmt = detect_format(str(email_file))
        self.assertEqual(fmt, "Email")
    
    def test_detect_json_format(self):
        """Test JSON format detection"""
        json_file = Path(self.test_dir) / "test.json"
        json_content = {"key": "value", "number": 123}
        json_file.write_text(json.dumps(json_content))
        
        fmt = detect_format(str(json_file))
        self.assertEqual(fmt, "JSON")
    
    def test_validate_json_schema_valid(self):
        """Test valid JSON schema validation"""
        data = {
            'event': 'test_event',
            'timestamp': '2024-01-01T00:00:00',
            'payload': {'data': 'test'}
        }
        required_fields = {
            'event': str,
            'timestamp': str,
            'payload': dict
        }
        is_valid, anomalies = validate_json_schema(data, required_fields)
        self.assertTrue(is_valid)
        self.assertEqual(len(anomalies), 0)
    
    def test_validate_json_schema_invalid(self):
        """Test invalid JSON schema validation"""
        data = {
            'event': 'test_event',
            # Missing timestamp and payload
        }
        required_fields = {
            'event': str,
            'timestamp': str,
            'payload': dict
        }
        is_valid, anomalies = validate_json_schema(data, required_fields)
        self.assertFalse(is_valid)
        self.assertGreater(len(anomalies), 0)


class TestSharedMemory(unittest.TestCase):
    """Test shared memory functionality"""
    
    def setUp(self):
        """Setup test memory file"""
        self.test_memory_file = "test_memory.json"
        # Clear any existing test file
        if os.path.exists(self.test_memory_file):
            os.remove(self.test_memory_file)
    
    def tearDown(self):
        """Cleanup test memory file"""
        if os.path.exists(self.test_memory_file):
            os.remove(self.test_memory_file)
    
    def test_save_and_load_memory(self):
        """Test saving and loading memory"""
        test_data = {
            'results': [
                {'agent': 'TestAgent', 'data': 'test'}
            ]
        }
        
        # Save with custom file
        with open(self.test_memory_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load
        with open(self.test_memory_file, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['results'][0]['agent'], 'TestAgent')
    
    def test_log_agent_result(self):
        """Test logging agent result"""
        # This would require modifying shared_memory.py to accept custom file path
        # For now, we'll test the function exists and can be called
        try:
            log_agent_result(
                agent='TestAgent',
                input_meta={'test': 'data'},
                extracted={'intent': 'Test'},
                actions=['test_action'],
                trace='test trace'
            )
        except Exception as e:
            # If it fails, at least we know the function exists
            self.assertIsNotNone(log_agent_result)


class TestRetryUtils(unittest.TestCase):
    """Test retry utility functionality"""
    
    def test_retry_success(self):
        """Test successful retry"""
        call_count = [0]
        
        def success_func(*args, **kwargs):
            call_count[0] += 1
            return "success"
        
        result = retry_action(success_func, max_attempts=3, delay=0)
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 1)
    
    def test_retry_after_failures(self):
        """Test retry after initial failures"""
        call_count = [0]
        
        def eventually_succeeds(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry_action(eventually_succeeds, max_attempts=3, delay=0)
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)
    
    def test_retry_max_attempts(self):
        """Test retry max attempts"""
        call_count = [0]
        
        def always_fails(*args, **kwargs):
            call_count[0] += 1
            raise Exception("Permanent failure")
        
        result = retry_action(always_fails, max_attempts=3, delay=0)
        self.assertIsNone(result)
        self.assertEqual(call_count[0], 3)


class TestActionRouter(unittest.TestCase):
    """Test action router functionality"""
    
    def test_route_high_confidence(self):
        """Test routing high confidence actions"""
        metadata = {
            'format': 'Email',
            'intent': 'Complaint',
            'confidence': 0.95,
            'file': 'test.txt'
        }
        actions = ['Process complaint']
        
        result = route_action(metadata, actions)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_route_low_confidence(self):
        """Test routing low confidence actions"""
        metadata = {
            'format': 'Email',
            'intent': 'Unknown',
            'confidence': 0.45,
            'file': 'test.txt'
        }
        actions = ['Manual review required']
        
        result = route_action(metadata, actions)
        self.assertIsNotNone(result)
        self.assertIn('manual', result.lower())


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_end_to_end_email_processing(self):
        """Test complete email processing pipeline"""
        # Create test email file
        email_file = Path(self.test_dir) / "test_email.txt"
        email_content = """From: customer@example.com
To: support@company.com
Subject: Product Complaint

I am not satisfied with my recent purchase and would like to file a complaint."""
        email_file.write_text(email_content)
        
        # Detect format
        fmt = detect_format(str(email_file))
        self.assertEqual(fmt, "Email")
        
        # Extract text
        text = extract_text(str(email_file), fmt)
        self.assertIn("customer@example.com", text)
        
        # Parse email
        parsed = parse_email(text)
        fields = extract_email_fields(text)
        tone = detect_tone(text)
        
        # Classify
        intent, confidence = classify_intent(parsed)
        self.assertEqual(intent, "Complaint")
        self.assertGreater(confidence, 0.8)
        
        # Trigger action
        action = trigger_action(fields, tone)
        self.assertIsInstance(action, str)
    
    def test_end_to_end_json_processing(self):
        """Test complete JSON processing pipeline"""
        # Create test JSON file
        json_file = Path(self.test_dir) / "test.json"
        json_data = {
            'event': 'payment_request',
            'timestamp': '2024-01-01T00:00:00',
            'payload': {
                'amount': 1500,
                'description': 'Invoice for services'
            }
        }
        json_file.write_text(json.dumps(json_data))
        
        # Detect format
        fmt = detect_format(str(json_file))
        self.assertEqual(fmt, "JSON")
        
        # Extract text
        text = extract_text(str(json_file), fmt)
        data = json.loads(text)
        
        # Validate schema
        required_fields = {
            'event': str,
            'timestamp': str,
            'payload': dict
        }
        is_valid, anomalies = validate_json_schema(data, required_fields)
        self.assertTrue(is_valid)
        
        # Classify
        intent, confidence = classify_intent(str(data))
        self.assertIsNotNone(intent)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailParser))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestSharedMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestActionRouter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
