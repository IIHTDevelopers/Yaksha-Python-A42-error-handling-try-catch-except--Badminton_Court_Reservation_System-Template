"""
Badminton Court Reservation System
Version 1.0

Demonstrates try-except-else-finally error handling patterns.
"""

from datetime import datetime

# Custom exceptions
class ReservationException(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

class CourtUnavailableError(ReservationException):
    def __init__(self, court_id, time_slot):
        super().__init__(f"Court {court_id} is unavailable at {time_slot}", "C001")

class PaymentFailedError(ReservationException):
    def __init__(self, reservation_id, amount):
        super().__init__(f"Payment failed for reservation {reservation_id}, amount: ${amount}", "P001")

class Court:
    def __init__(self, court_id, hourly_rate):
        try:
            if not court_id or not isinstance(court_id, str):
                raise ValueError("Court ID must be a non-empty string")
            
            rate = float(hourly_rate)
            if rate <= 0:
                raise ValueError("Hourly rate must be positive")
        except ValueError as e:
            raise ReservationException(f"Invalid court data: {str(e)}")
        else:
            self.court_id = court_id
            self.hourly_rate = rate
            self.schedule = {}  # date -> list of time slots

    def is_available(self, date, time_slot):
        try:
            if date not in self.schedule:
                return True
            
            if time_slot in self.schedule[date]:
                raise CourtUnavailableError(self.court_id, time_slot)
        except CourtUnavailableError:
            raise
        else:
            return True

class Reservation:
    def __init__(self, reservation_id, player_name, court, date, time_slot):
        try:
            if not reservation_id or not player_name:
                raise ValueError("Reservation ID and player name are required")
            
            if not isinstance(court, Court):
                raise ValueError("Valid Court object is required")
                
            # Check court availability
            court.is_available(date, time_slot)
            
        except ValueError as e:
            raise ReservationException(f"Invalid reservation: {str(e)}")
        else:
            self.reservation_id = reservation_id
            self.player_name = player_name
            self.court = court
            self.date = date
            self.time_slot = time_slot
            self.status = "pending"
            self.total_cost = court.hourly_rate
            
            # Reserve the court
            if date not in court.schedule:
                court.schedule[date] = []
            court.schedule[date].append(time_slot)

    def process_payment(self, payment_method):
        payment_log = {
            "reservation_id": self.reservation_id,
            "amount": self.total_cost,
            "method": payment_method,
            "status": "pending"
        }
        
        try:
            if self.status != "pending":
                raise ReservationException("Cannot process payment for non-pending reservation")
            
            if payment_method not in ["credit", "cash", "online"]:
                raise ValueError("Invalid payment method")
                
            # Simulate failed payment condition
            if payment_method == "credit" and self.total_cost > 50:
                raise PaymentFailedError(self.reservation_id, self.total_cost)
                
        except (ValueError, ReservationException) as e:
            payment_log["status"] = "failed"
            payment_log["error"] = str(e)
            raise
        else:
            self.status = "confirmed"
            payment_log["status"] = "successful"
            return payment_log
        finally:
            print(f"Payment processing completed: {payment_log['status']}")

class ReservationSystem:
    def __init__(self):
        self.courts = {}
        self.reservations = {}
        self.transaction_log = []
        self.next_reservation_id = 1

    def add_court(self, court_id, hourly_rate):
        transaction = {
            "type": "add_court",
            "court_id": court_id,
            "status": "pending"
        }
        
        try:
            if court_id in self.courts:
                raise ReservationException(f"Court {court_id} already exists")
            
            court = Court(court_id, hourly_rate)
            
        except ReservationException as e:
            transaction["status"] = "failed"
            transaction["error"] = str(e)
            self.transaction_log.append(transaction)
            raise
        else:
            self.courts[court_id] = court
            transaction["status"] = "completed"
            self.transaction_log.append(transaction)
            return court
        finally:
            print(f"Court transaction: {transaction['status']}")

    def make_reservation(self, reservation_id, player_name, court_id, date, time_slot):
        transaction = {
            "type": "make_reservation",
            "reservation_id": reservation_id,
            "status": "pending"
        }
        
        try:
            if reservation_id in self.reservations:
                raise ReservationException(f"Reservation {reservation_id} already exists")
            
            if court_id not in self.courts:
                raise ReservationException(f"Court {court_id} does not exist")
            
            reservation = Reservation(reservation_id, player_name, 
                                     self.courts[court_id], date, time_slot)
            
        except ReservationException as e:
            transaction["status"] = "failed"
            transaction["error"] = str(e)
            self.transaction_log.append(transaction)
            raise
        else:
            self.reservations[reservation_id] = reservation
            transaction["status"] = "completed"
            self.transaction_log.append(transaction)
            return reservation
        finally:
            print(f"Reservation transaction: {transaction['status']}")

    def cancel_reservation(self, reservation_id):
        transaction = {
            "type": "cancel_reservation",
            "reservation_id": reservation_id,
            "status": "pending"
        }
        
        court_updated = False
        
        try:
            if reservation_id not in self.reservations:
                raise ReservationException(f"Reservation {reservation_id} does not exist")
            
            reservation = self.reservations[reservation_id]
            
            # Remove from court schedule
            court = reservation.court
            date = reservation.date
            time_slot = reservation.time_slot
            
            if date in court.schedule and time_slot in court.schedule[date]:
                court.schedule[date].remove(time_slot)
                court_updated = True
                
            reservation.status = "cancelled"
            
        except ReservationException as e:
            transaction["status"] = "failed"
            transaction["error"] = str(e)
            
            # Rollback court schedule if needed
            if court_updated:
                self._rollback_cancellation(reservation)
                
            self.transaction_log.append(transaction)
            raise
        else:
            transaction["status"] = "completed"
            self.transaction_log.append(transaction)
            return True
        finally:
            print(f"Cancellation transaction: {transaction['status']}")
    
    def _rollback_cancellation(self, reservation):
        try:
            date = reservation.date
            time_slot = reservation.time_slot
            court = reservation.court
            
            if date not in court.schedule:
                court.schedule[date] = []
            
            court.schedule[date].append(time_slot)
            reservation.status = "confirmed"
        except Exception as e:
            print(f"Rollback error: {e}")
        finally:
            print("Rollback operation completed")
    
    def get_available_time_slots(self, court_id, date):
        try:
            if court_id not in self.courts:
                raise ReservationException(f"Court {court_id} does not exist")
            
            court = self.courts[court_id]
            
            # Standard time slots
            all_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", 
                         "14:00", "15:00", "16:00", "17:00", "18:00"]
            
            # Remove booked slots
            booked_slots = court.schedule.get(date, [])
            available_slots = [slot for slot in all_slots if slot not in booked_slots]
            
            return available_slots
            
        except ReservationException as e:
            print(f"Error checking availability: {e}")
            raise
        else:
            return available_slots

def generate_report(system):
    report = None
    
    try:
        if not system.reservations:
            raise ReservationException("No reservations to report")
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_courts": len(system.courts),
            "total_reservations": len(system.reservations),
            "confirmed_reservations": 0,
            "total_revenue": 0.0
        }
        
        for reservation in system.reservations.values():
            if reservation.status == "confirmed":
                report["confirmed_reservations"] += 1
                report["total_revenue"] += reservation.total_cost
    
    except ReservationException as e:
        print(f"Report generation failed: {e}")
        raise
    else:
        print("Report generated successfully")
        return report
    finally:
        print("Report generation process completed")

def main():
    system = ReservationSystem()
    
    # Add some initial courts
    try:
        system.add_court("A", 20.0)
        system.add_court("B", 25.0)
        system.add_court("C", 30.0)  # Premium court
    except ReservationException as e:
        print(f"Error initializing courts: {e}")
    
    while True:
        print("\n===== BADMINTON COURT RESERVATION SYSTEM =====")
        print("1. View Available Courts")
        print("2. Make a Reservation")
        print("3. Cancel a Reservation")
        print("4. View My Reservations")
        print("5. Generate Report")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ")
            
            if choice == "1":
                # View available courts
                print("\n----- AVAILABLE COURTS -----")
                if not system.courts:
                    print("No courts available in the system.")
                    continue
                
                print("Available court IDs:")
                for court_id, court in system.courts.items():
                    print(f"Court {court.court_id}: ${court.hourly_rate:.2f} per hour")
                    
            elif choice == "2":
                # Make a reservation
                print("\n----- MAKE A RESERVATION -----")
                
                # Get player name
                player_name = input("Enter your name: ")
                if not player_name:
                    print("Name cannot be empty")
                    continue
                
                # View and select a court
                print("\nAvailable courts:")
                valid_court_ids = []
                for court_id, court in system.courts.items():
                    print(f"Court {court.court_id}: ${court.hourly_rate:.2f} per hour")
                    valid_court_ids.append(court.court_id)
                
                print(f"\nValid court IDs: {', '.join(valid_court_ids)}")
                court_id = input("Enter court ID from the list above: ")
                
                if court_id not in system.courts:
                    print(f"Court {court_id} does not exist. Please choose from: {', '.join(valid_court_ids)}")
                    continue
                
                # Enter date
                date = input("Enter date (YYYY-MM-DD): ")
                
                try:
                    # Get available time slots
                    available_slots = system.get_available_time_slots(court_id, date)
                    
                    if not available_slots:
                        print(f"No available time slots for court {court_id} on {date}")
                        continue
                    
                    # Display available time slots
                    print("\nAvailable time slots:")
                    for i, slot in enumerate(available_slots, 1):
                        print(f"{i}. {slot}")
                    
                    # Select time slot
                    slot_choice = int(input(f"Select time slot number (1-{len(available_slots)}): "))
                    if slot_choice < 1 or slot_choice > len(available_slots):
                        print(f"Invalid selection. Please enter a number between 1 and {len(available_slots)}")
                        continue
                    
                    time_slot = available_slots[slot_choice - 1]
                    
                    # Generate reservation ID
                    reservation_id = f"R{system.next_reservation_id}"
                    system.next_reservation_id += 1
                    
                    # Make reservation
                    reservation = system.make_reservation(reservation_id, player_name, court_id, date, time_slot)
                    
                    # Process payment
                    print("\n----- PAYMENT -----")
                    print(f"Total amount: ${reservation.total_cost:.2f}")
                    print("Valid payment methods: credit, cash, online")
                    
                    payment_method = input("Enter payment method (credit/cash/online): ").lower()
                    reservation.process_payment(payment_method)
                    
                    print(f"\nReservation confirmed! Your reservation ID is {reservation_id}")
                    print(f"Court {court_id} reserved for {date} at {time_slot}")
                    
                except (ValueError, ReservationException) as e:
                    print(f"Reservation failed: {e}")
                    
            elif choice == "3":
                # Cancel a reservation
                print("\n----- CANCEL A RESERVATION -----")
                
                # Show existing reservations
                if system.reservations:
                    print("Existing reservations:")
                    for res_id, res in system.reservations.items():
                        print(f"ID: {res_id}, Player: {res.player_name}, Court: {res.court.court_id}, Date: {res.date}, Time: {res.time_slot}")
                else:
                    print("No reservations exist in the system.")
                    continue
                
                try:
                    reservation_id = input("Enter reservation ID from the list above: ")
                    system.cancel_reservation(reservation_id)
                    print(f"Reservation {reservation_id} cancelled successfully")
                except ReservationException as e:
                    print(f"Cancellation failed: {e}")
                    
            elif choice == "4":
                # View reservations
                print("\n----- MY RESERVATIONS -----")
                
                player_name = input("Enter your name: ")
                
                found = False
                for res_id, reservation in system.reservations.items():
                    if reservation.player_name.lower() == player_name.lower():
                        found = True
                        print(f"ID: {res_id}, Court: {reservation.court.court_id}, " + 
                              f"Date: {reservation.date}, Time: {reservation.time_slot}, " +
                              f"Status: {reservation.status}")
                
                if not found:
                    print("No reservations found for this name.")
                    
            elif choice == "5":
                # Generate report
                print("\n----- SYSTEM REPORT -----")
                
                try:
                    report = generate_report(system)
                    print(f"Date: {report['date']}")
                    print(f"Total courts: {report['total_courts']}")
                    print(f"Total reservations: {report['total_reservations']}")
                    print(f"Confirmed reservations: {report['confirmed_reservations']}")
                    print(f"Total revenue: ${report['total_revenue']:.2f}")
                except ReservationException as e:
                    print(f"Report generation failed: {e}")
                    
            elif choice == "6":
                print("\nThank you for using the system!")
                print(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()