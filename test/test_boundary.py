import pytest
from datetime import datetime, timedelta
from test.TestUtils import TestUtils
from badminton_court_reservation_system import Court, Reservation, ReservationSystem, ReservationException, CourtUnavailableError, PaymentFailedError

class TestBoundary:
    """Test cases for boundary conditions in the badminton court reservation system."""
    
    def test_system_boundaries(self):
        """Test all boundary conditions for the badminton court reservation system."""
        try:
            # Test Court validation boundary conditions
            # Valid court data
            court1 = Court("A", 20.0)
            assert court1.court_id == "A"
            assert court1.hourly_rate == 20.0
            assert isinstance(court1.schedule, dict)
            
            # Minimum valid values
            court2 = Court("B", 0.01)
            assert court2.court_id == "B"
            assert court2.hourly_rate == 0.01
            
            # Invalid court ID - empty
            try:
                Court("", 20.0)
                assert False, "Should raise ReservationException for empty court ID"
            except ReservationException:
                pass  # Expected behavior
            
            # Invalid hourly rate - zero
            try:
                Court("C", 0)
                assert False, "Should raise ReservationException for zero hourly rate"
            except ReservationException:
                pass  # Expected behavior
            
            # Invalid hourly rate - negative
            try:
                Court("C", -10.0)
                assert False, "Should raise ReservationException for negative hourly rate"
            except ReservationException:
                pass  # Expected behavior
            
            # Invalid hourly rate - non-numeric
            try:
                Court("C", "twenty")
                assert False, "Should raise ReservationException for non-numeric hourly rate"
            except ReservationException:
                pass  # Expected behavior
            
            # Test ReservationSystem operations
            system = ReservationSystem()
            
            # Add courts to system
            assert system.add_court("A", 20.0) is not None
            assert system.add_court("B", 25.0) is not None
            
            # Boundary check: duplicate court ID
            try:
                system.add_court("A", 30.0)
                assert False, "Should raise ReservationException for duplicate court ID"
            except ReservationException:
                pass  # Expected behavior
            
            # Test court availability
            date = "2023-07-01"
            
            # Make a reservation
            res1 = system.make_reservation("R1", "John", "A", date, "10:00")
            assert res1 is not None
            assert res1.reservation_id == "R1"
            
            # Check court is unavailable for the same time slot
            try:
                system.make_reservation("R2", "Mary", "A", date, "10:00")
                assert False, "Should raise CourtUnavailableError for double booking"
            except CourtUnavailableError:
                pass  # Expected behavior
            
            # Other time slots should still be available
            res2 = system.make_reservation("R2", "Mary", "A", date, "11:00")
            assert res2 is not None
            
            # Non-existent court
            try:
                system.make_reservation("R3", "Bob", "Z", date, "12:00")
                assert False, "Should raise ReservationException for non-existent court"
            except ReservationException:
                pass  # Expected behavior
            
            # Test time slot availability
            # Try to get available time slots for non-existent court
            try:
                system.get_available_time_slots("Z", date)
                assert False, "Should raise ReservationException for non-existent court"
            except ReservationException:
                pass  # Expected behavior
            
            # Check available time slots for a court
            available_slots = system.get_available_time_slots("A", date)
            assert "10:00" not in available_slots  # Should be booked
            assert "11:00" not in available_slots  # Should be booked
            assert "12:00" in available_slots  # Should be available
            
            # Test payment processing with different amounts
            # Normal payment
            payment_result = res1.process_payment("cash")
            assert payment_result["status"] == "successful"
            assert res1.status == "confirmed"
            
            # Payment for an already confirmed reservation
            try:
                res1.process_payment("cash")
                assert False, "Should raise ReservationException for already confirmed reservation"
            except ReservationException:
                pass  # Expected behavior
            
            # Test payment with credit card above limit
            res_premium = system.make_reservation("R3", "Alice", "B", date, "15:00")
            # Set a high cost to trigger payment failure
            res_premium.total_cost = 60.0
            
            try:
                res_premium.process_payment("credit")
                assert False, "Should raise PaymentFailedError for credit card limit"
            except PaymentFailedError:
                pass  # Expected behavior
            
            # Should work with cash though
            payment_result = res_premium.process_payment("cash")
            assert payment_result["status"] == "successful"
            
            # Invalid payment method
            res_another = system.make_reservation("R4", "Bob", "B", date, "16:00")
            try:
                res_another.process_payment("bitcoin")
                assert False, "Should raise ValueError for invalid payment method"
            except ValueError:
                pass  # Expected behavior
            
            # Test reservation cancellation
            assert system.cancel_reservation("R1") is True
            assert system.reservations["R1"].status == "cancelled"
            
            # Try to cancel non-existent reservation
            try:
                system.cancel_reservation("R999")
                assert False, "Should raise ReservationException for non-existent reservation"
            except ReservationException:
                pass  # Expected behavior
            
            # Check that cancelled reservation time slot is available again
            available_slots = system.get_available_time_slots("A", date)
            assert "10:00" in available_slots  # Should be available again after cancellation
            
            TestUtils.yakshaAssert("test_system_boundaries", True, "boundary")
        except Exception as e:
            TestUtils.yakshaAssert("test_system_boundaries", False, "boundary")
            raise e