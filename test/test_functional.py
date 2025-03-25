import pytest
import inspect
import re
import sys
from io import StringIO
from test.TestUtils import TestUtils
from badminton_court_reservation_system import Court, Reservation, ReservationSystem, ReservationException, CourtUnavailableError, PaymentFailedError, generate_report

class TestFunctional:
    """Consolidated test cases covering core functionality and error handling."""
    
    def test_court_and_reservation_classes(self):
        """Test Court and Reservation classes with proper error handling."""
        try:
            # Test Court creation and validation
            court = Court("A", 20.0)
            assert court.court_id == "A"
            assert court.hourly_rate == 20.0
            assert isinstance(court.schedule, dict)
            
            # Verify Court.__init__ error handling structure
            source = inspect.getsource(Court.__init__)
            assert "try:" in source
            assert "except" in source 
            assert "else:" in source
            
            # Test Court.is_available with error handling
            assert court.is_available("2023-07-01", "10:00") is True
            
            # Make a time slot unavailable
            court.schedule["2023-07-01"] = ["10:00"]
            
            # This should raise an exception
            try:
                court.is_available("2023-07-01", "10:00")
                assert False, "Should raise CourtUnavailableError"
            except CourtUnavailableError:
                pass
                
            # Verify Court.is_available error handling structure
            source = inspect.getsource(Court.is_available)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            
            # Test Reservation creation
            reservation = Reservation("R1", "John", court, "2023-07-02", "11:00")
            assert reservation.reservation_id == "R1"
            assert reservation.player_name == "John"
            assert reservation.court == court
            assert reservation.date == "2023-07-02"
            assert reservation.status == "pending"
            
            # Verify Reservation.__init__ error handling structure
            source = inspect.getsource(Reservation.__init__)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            
            TestUtils.yakshaAssert("test_court_and_reservation_classes", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_court_and_reservation_classes", False, "functional")
            raise e
    
    def test_reservation_system_operations(self):
        """Test ReservationSystem core operations with error handling."""
        try:
            system = ReservationSystem()
            
            # Test add_court
            court = system.add_court("A", 20.0)
            assert "A" in system.courts
            assert system.courts["A"].hourly_rate == 20.0
            assert len(system.transaction_log) == 1
            assert system.transaction_log[0]["status"] == "completed"
            
            # Verify add_court error handling structure
            source = inspect.getsource(ReservationSystem.add_court)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            assert "finally:" in source
            assert not re.search(r"except\s*:", source)
            
            # Test make_reservation
            reservation = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            assert reservation.reservation_id == "R1"
            assert "10:00" in system.courts["A"].schedule["2023-07-01"]
            
            # Verify make_reservation error handling structure
            source = inspect.getsource(ReservationSystem.make_reservation)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            assert "finally:" in source
            
            # Test get_available_time_slots
            available_slots = system.get_available_time_slots("A", "2023-07-01")
            assert "10:00" not in available_slots
            assert "11:00" in available_slots
            
            # Verify get_available_time_slots error handling structure
            source = inspect.getsource(ReservationSystem.get_available_time_slots)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            
            # Test cancel_reservation with stdout capture
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                result = system.cancel_reservation("R1")
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
            
            assert result is True
            assert system.reservations["R1"].status == "cancelled"
            assert "Cancellation transaction: completed" in output
            assert "10:00" in system.get_available_time_slots("A", "2023-07-01")
            
            # Verify cancel_reservation error handling structure
            source = inspect.getsource(ReservationSystem.cancel_reservation)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            assert "finally:" in source
            
            # Verify _rollback_cancellation error handling structure
            source = inspect.getsource(ReservationSystem._rollback_cancellation)
            assert "try:" in source
            assert "except" in source
            assert "finally:" in source
            
            TestUtils.yakshaAssert("test_reservation_system_operations", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_reservation_system_operations", False, "functional")
            raise e
    
    def test_payment_processing(self):
        """Test payment processing with error handling."""
        try:
            system = ReservationSystem()
            system.add_court("A", 20.0)
            reservation = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            
            # Capture stdout to verify finally block execution
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                payment_result = reservation.process_payment("cash")
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
            
            assert payment_result["status"] == "successful"
            assert reservation.status == "confirmed"
            assert "Payment processing completed" in output
            
            # Verify process_payment error handling structure
            source = inspect.getsource(Reservation.process_payment)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            assert "finally:" in source
            assert not re.search(r"except\s*:", source)
            assert re.search(r"except\s+\(?\w+", source)
            
            # Test invalid payment method
            reservation = system.make_reservation("R2", "Mary", "A", "2023-07-01", "11:00")
            try:
                reservation.process_payment("bitcoin")
                assert False, "Should raise ValueError for invalid payment method"
            except ValueError as e:
                assert "Invalid payment method" in str(e)
            
            # Test payment for already confirmed reservation
            reservation.process_payment("cash")
            try:
                reservation.process_payment("cash")
                assert False, "Should raise ReservationException for already confirmed reservation"
            except ReservationException as e:
                assert "Cannot process payment" in str(e)
            
            TestUtils.yakshaAssert("test_payment_processing", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_payment_processing", False, "functional")
            raise e
    
    def test_report_generation(self):
        """Test report generation with error handling."""
        try:
            system = ReservationSystem()
            system.add_court("A", 20.0)
            system.add_court("B", 25.0)
            
            # Make and confirm reservations
            res1 = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            res1.process_payment("cash")
            
            res2 = system.make_reservation("R2", "Mary", "B", "2023-07-01", "11:00")
            res2.process_payment("credit")
            
            # Capture stdout to verify finally block execution
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                report = generate_report(system)
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
            
            assert "date" in report
            assert report["total_courts"] == 2
            assert report["total_reservations"] == 2
            assert report["confirmed_reservations"] == 2
            assert report["total_revenue"] == 45.0
            assert "Report generation process completed" in output
            
            # Verify generate_report error handling structure
            source = inspect.getsource(generate_report)
            assert "try:" in source
            assert "except" in source
            assert "else:" in source
            assert "finally:" in source
            
            # Check specific error message
            empty_system = ReservationSystem()
            try:
                generate_report(empty_system)
                assert False, "Should raise exception for empty system"
            except Exception as e:
                assert "No reservations" in str(e)
            
            TestUtils.yakshaAssert("test_report_generation", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_report_generation", False, "functional")
            raise e
    
    def test_exception_classes(self):
        """Test exception classes and their messages."""
        try:
            # Test base exception class
            base_exception = ReservationException("Test message", "E000")
            assert str(base_exception) == "[E000] Test message"
            
            # Exception without error code
            simple_exception = ReservationException("Simple message")
            assert str(simple_exception) == "Simple message"
            
            # Test specific exception classes
            court_error = CourtUnavailableError("A", "10:00")
            assert "Court A is unavailable at 10:00" in str(court_error)
            assert "C001" in str(court_error)
            
            payment_error = PaymentFailedError("R1", 20.0)
            assert "Payment failed for reservation R1" in str(payment_error)
            assert "P001" in str(payment_error)
            
            TestUtils.yakshaAssert("test_exception_classes", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_exception_classes", False, "functional")
            raise e
    
    def test_error_handling_patterns(self):
        """Test all required methods implement proper error handling patterns."""
        try:
            import badminton_court_reservation_system as module
            
            # Methods that should have specific error handling patterns
            methods_to_check = {
                "Court.__init__": ["try", "except", "else"],
                "Court.is_available": ["try", "except", "else"],
                "Reservation.__init__": ["try", "except", "else"],
                "Reservation.process_payment": ["try", "except", "else", "finally"],
                "ReservationSystem.add_court": ["try", "except", "else", "finally"],
                "ReservationSystem.make_reservation": ["try", "except", "else", "finally"],
                "ReservationSystem.cancel_reservation": ["try", "except", "else", "finally"],
                "ReservationSystem._rollback_cancellation": ["try", "except", "finally"],
                "ReservationSystem.get_available_time_slots": ["try", "except", "else"],
                "generate_report": ["try", "except", "else", "finally"]
            }
            
            missing_patterns = []
            
            # Check each method for required error handling patterns
            for method_path, required_blocks in methods_to_check.items():
                # Handle module-level functions (without class)
                if '.' not in method_path:
                    try:
                        # Get function directly from module
                        method = getattr(module, method_path)
                        source = inspect.getsource(method)
                        
                        # Check for required blocks
                        for block in required_blocks:
                            if block == "try":
                                assert "try:" in source, f"{method_path} missing try block"
                            elif block == "except":
                                assert re.search(r"except\s+(\w+|[\(\w+,\s*\w+\)])", source) is not None, f"{method_path} missing except block"
                            elif block == "else":
                                assert "else:" in source, f"{method_path} missing else block"
                            elif block == "finally":
                                assert "finally:" in source, f"{method_path} missing finally block"
                        
                        # Check for bare except
                        if "except" in required_blocks:
                            assert not re.search(r"except\s*:", source), f"{method_path} uses bare except (should specify exception types)"
                    except AttributeError:
                        missing_patterns.append(f"Could not find function {method_path}")
                    continue
                
                # Handle class methods
                try:
                    class_name, method_name = method_path.split(".")
                    
                    # Get the class and method
                    cls = getattr(module, class_name)
                    method = cls.__init__ if method_name == "__init__" else getattr(cls, method_name)
                    
                    # Check method source code
                    source = inspect.getsource(method)
                    
                    # Check for required blocks
                    for block in required_blocks:
                        if block == "try":
                            assert "try:" in source, f"{method_path} missing try block"
                        elif block == "except":
                            assert re.search(r"except\s+(\w+|[\(\w+,\s*\w+\)])", source) is not None, f"{method_path} missing except block"
                        elif block == "else":
                            assert "else:" in source, f"{method_path} missing else block"
                        elif block == "finally":
                            assert "finally:" in source, f"{method_path} missing finally block"
                    
                    # Check for bare except
                    if "except" in required_blocks:
                        assert not re.search(r"except\s*:", source), f"{method_path} uses bare except (should specify exception types)"
                except (AttributeError, ValueError) as e:
                    missing_patterns.append(f"Error checking {method_path}: {str(e)}")
            
            assert len(missing_patterns) == 0, f"Missing patterns: {', '.join(missing_patterns)}"
            
            # Test transaction logging for error cases
            system = ReservationSystem()
            system.add_court("A", 20.0)
            
            # Try to add a duplicate court to test error logging
            try:
                system.add_court("A", 30.0)
            except ReservationException:
                failed_transactions = [t for t in system.transaction_log if t["status"] == "failed"]
                assert len(failed_transactions) > 0
                assert "failed" in failed_transactions[-1]["status"]
                assert "error" in failed_transactions[-1]
            
            TestUtils.yakshaAssert("test_error_handling_patterns", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_error_handling_patterns", False, "functional")
            raise e