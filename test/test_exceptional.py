import pytest
import inspect
import re
from datetime import datetime
from test.TestUtils import TestUtils
from badminton_court_reservation_system import Court, Reservation, ReservationSystem, ReservationException, CourtUnavailableError, PaymentFailedError, generate_report

class TestExceptional:
    """Test cases for exception handling in the badminton court reservation system."""
    
    def test_exception_handling(self):
        """Test exception handling throughout the badminton court reservation system."""
        try:
            # Test exception hierarchy
            # Base exception class
            base_exception = ReservationException("Test message", "E000")
            assert str(base_exception) == "[E000] Test message"
            
            # Exception without error code
            simple_exception = ReservationException("Simple message")
            assert str(simple_exception) == "Simple message"
            
            # Specific exception classes
            court_error = CourtUnavailableError("A", "10:00")
            assert "Court A is unavailable at 10:00" in str(court_error)
            assert "C001" in str(court_error)
            
            payment_error = PaymentFailedError("R1", 20.0)
            assert "Payment failed for reservation R1" in str(payment_error)
            assert "P001" in str(payment_error)
            
            # Test Court validation exceptions
            try:
                Court(None, 20.0)
                assert False, "Should raise ReservationException for None court ID"
            except ReservationException as e:
                assert "must be a non-empty string" in str(e)
            
            try:
                Court(123, 20.0)  # Non-string ID
                assert False, "Should raise ReservationException for non-string court ID"
            except ReservationException as e:
                assert "must be a non-empty string" in str(e)
            
            try:
                Court("A", "twenty")  # Non-numeric rate
                assert False, "Should raise ReservationException for non-numeric rate"
            except ReservationException as e:
                assert "Invalid" in str(e)
            
            # Test Reservation creation exceptions
            system = ReservationSystem()
            court_a = system.add_court("A", 20.0)
            
            try:
                Reservation("", "John", court_a, "2023-07-01", "10:00")
                assert False, "Should raise ReservationException for empty reservation ID"
            except ReservationException as e:
                assert "required" in str(e)
            
            try:
                Reservation("R1", "", court_a, "2023-07-01", "10:00")
                assert False, "Should raise ReservationException for empty player name"
            except ReservationException as e:
                assert "required" in str(e)
            
            try:
                Reservation("R1", "John", "not a court object", "2023-07-01", "10:00")
                assert False, "Should raise ReservationException for invalid court object"
            except ReservationException as e:
                assert "Valid Court object" in str(e)
            
            # Test ReservationSystem exceptions
            try:
                system.make_reservation("R1", "John", "Z", "2023-07-01", "10:00")
                assert False, "Should raise ReservationException for non-existent court"
            except ReservationException as e:
                assert "does not exist" in str(e)
            
            # Make a valid reservation for further testing
            system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            
            # Test duplicate reservation ID
            try:
                system.make_reservation("R1", "Mary", "A", "2023-07-01", "11:00")
                assert False, "Should raise ReservationException for duplicate reservation ID"
            except ReservationException as e:
                assert "already exists" in str(e)
            
            # Test court availability exception
            try:
                system.make_reservation("R2", "Mary", "A", "2023-07-01", "10:00")
                assert False, "Should raise CourtUnavailableError for double booking"
            except CourtUnavailableError as e:
                assert "Court A is unavailable" in str(e)
            
            # Test cancellation exceptions
            try:
                system.cancel_reservation("R999")
                assert False, "Should raise ReservationException for non-existent reservation"
            except ReservationException as e:
                assert "does not exist" in str(e)
            
            # Test payment processing exceptions
            reservation = system.reservations["R1"]
            
            # Test invalid payment method
            try:
                reservation.process_payment("bitcoin")
                assert False, "Should raise ValueError for invalid payment method"
            except ValueError as e:
                assert "Invalid payment method" in str(e)
            
            # Process valid payment
            reservation.process_payment("cash")
            
            # Test payment for already confirmed reservation
            try:
                reservation.process_payment("cash")
                assert False, "Should raise ReservationException for already confirmed reservation"
            except ReservationException as e:
                assert "Cannot process payment" in str(e)
            
            # Test report generation exceptions
            # Create a new system with no reservations
            empty_system = ReservationSystem()
            
            # Should raise exception for empty system
            try:
                generate_report(empty_system)
                assert False, "Should raise ReservationException for empty system"
            except ReservationException as e:
                assert "No reservations" in str(e)
            
            # Test transaction logging
            # Check that failed transactions are logged correctly
            try:
                system.add_court("A", 30.0)  # Duplicate court
            except ReservationException:
                # Check transaction log for the failed transaction
                failed_transactions = [t for t in system.transaction_log if t["status"] == "failed"]
                assert len(failed_transactions) > 0
                assert "failed" in failed_transactions[-1]["status"]
                assert "error" in failed_transactions[-1]
            
            TestUtils.yakshaAssert("test_exception_handling", True, "exceptional")
        except Exception as e:
            TestUtils.yakshaAssert("test_exception_handling", False, "exceptional")
            raise e
            
    def test_try_except_else_finally_pattern(self):
        """Test proper implementation of try-except-else-finally pattern."""
        try:
            # Import module to examine structure
            import badminton_court_reservation_system as module
            
            # Define methods that should have specific error handling patterns
            methods_to_check = {
                # Class initialization methods
                "Court.__init__": ["try", "except", "else"],
                "Reservation.__init__": ["try", "except", "else"],
                
                # Key operations
                "Court.is_available": ["try", "except", "else"],
                "Reservation.process_payment": ["try", "except", "else", "finally"],
                "ReservationSystem.add_court": ["try", "except", "else", "finally"],
                "ReservationSystem.make_reservation": ["try", "except", "else", "finally"],
                "ReservationSystem.cancel_reservation": ["try", "except", "else", "finally"],
                "ReservationSystem._rollback_cancellation": ["try", "except", "finally"],
                "ReservationSystem.get_available_time_slots": ["try", "except", "else"],
                # Module level function
                "generate_report": ["try", "except", "else", "finally"]
            }
            
            missing_patterns = []
            
            for method_path, required_blocks in methods_to_check.items():
                # Handle module-level functions (without class)
                if '.' not in method_path:
                    try:
                        # Get function directly from module
                        method = getattr(module, method_path)
                        source = inspect.getsource(method)
                        
                        # Check for required blocks
                        blocks_present = {}
                        blocks_present["try"] = "try:" in source
                        blocks_present["except"] = re.search(r"except\s+(\w+|[\(\w+,\s*\w+\)])", source) is not None
                        blocks_present["else"] = "else:" in source
                        blocks_present["finally"] = "finally:" in source
                        
                        # Check if any required blocks are missing
                        missing_blocks = [block for block in required_blocks if not blocks_present[block]]
                        
                        if missing_blocks:
                            missing_patterns.append(f"{method_path} missing {', '.join(missing_blocks)}")
                        
                        # Check for bare except (except without specific exception)
                        if "except" in required_blocks:
                            has_bare_except = re.search(r"except\s*:", source) is not None
                            if has_bare_except:
                                missing_patterns.append(f"{method_path} uses bare except (should specify exception types)")
                    except AttributeError:
                        missing_patterns.append(f"Could not find function {method_path}")
                    continue
                
                # Handle class methods
                try:
                    parts = method_path.split('.')
                    if len(parts) != 2:
                        missing_patterns.append(f"Invalid method path: {method_path}")
                        continue
                        
                    class_name, method_name = parts
                    
                    # Get method
                    cls = getattr(module, class_name)
                    method = cls.__init__ if method_name == "__init__" else getattr(cls, method_name)
                    
                    # Get source code
                    source = inspect.getsource(method)
                    
                    # Check for required blocks
                    blocks_present = {}
                    blocks_present["try"] = "try:" in source
                    blocks_present["except"] = re.search(r"except\s+(\w+|[\(\w+,\s*\w+\)])", source) is not None
                    blocks_present["else"] = "else:" in source
                    blocks_present["finally"] = "finally:" in source
                    
                    # Check if any required blocks are missing
                    missing_blocks = [block for block in required_blocks if not blocks_present[block]]
                    
                    if missing_blocks:
                        missing_patterns.append(f"{method_path} missing {', '.join(missing_blocks)}")
                    
                    # Check for bare except (except without specific exception)
                    if "except" in required_blocks:
                        has_bare_except = re.search(r"except\s*:", source) is not None
                        if has_bare_except:
                            missing_patterns.append(f"{method_path} uses bare except (should specify exception types)")
                except (AttributeError, ValueError) as e:
                    missing_patterns.append(f"Error checking {method_path}: {str(e)}")
            
            # Make sure no methods are missing required patterns
            assert len(missing_patterns) == 0, f"Missing patterns: {', '.join(missing_patterns)}"
            
            # Test execution flow for key methods to ensure blocks execute correctly
            # 1. Test Court.is_available flow
            court = Court("A", 20.0)
            # This should go through the try and else blocks
            assert court.is_available("2023-07-01", "10:00") is True
            
            # Now make a time slot unavailable
            court.schedule["2023-07-01"] = ["10:00"]
            
            # This should raise an exception, bypassing the else block
            try:
                court.is_available("2023-07-01", "10:00")
                assert False, "Should raise CourtUnavailableError"
            except CourtUnavailableError:
                pass
            
            # 2. Test Reservation.process_payment to verify finally block
            system = ReservationSystem()
            court = system.add_court("A", 20.0)
            reservation = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            
            # Capture stdout to verify finally block execution
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                # This should succeed
                reservation.process_payment("cash")
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
                
            # Verify finally block executed (should see the completion message)
            assert "Payment processing completed" in output
            
            # 3. Test ReservationSystem.cancel_reservation for finally block
            system = ReservationSystem()
            court = system.add_court("A", 20.0)
            reservation = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                system.cancel_reservation("R1")
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
                
            # Verify the cancellation was recorded and finally block message is present
            assert "Cancellation transaction: completed" in output
            
            # 4. Test generate_report finally block
            system = ReservationSystem()
            court = system.add_court("A", 20.0)
            reservation = system.make_reservation("R1", "John", "A", "2023-07-01", "10:00")
            reservation.process_payment("cash")
            
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                report = generate_report(system)
            finally:
                sys.stdout = old_stdout
                output = mystdout.getvalue()
                
            # Verify the report was generated and finally block message is present
            assert "Report generation process completed" in output
            
            TestUtils.yakshaAssert("test_try_except_else_finally_pattern", True, "exceptional")
        except Exception as e:
            TestUtils.yakshaAssert("test_try_except_else_finally_pattern", False, "exceptional")
            raise e