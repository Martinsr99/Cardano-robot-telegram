"""
Test script for the price alerts functionality.

This script tests the creation, checking, and triggering of price alerts.
"""

import sys
import time
from price_alerts_refactored import (
    AlertCondition, PriceAlert, PriceAlertManager,
    EQUAL, GREATER, LESS, AND, OR,
    get_alert_manager, initialize_alerts
)

def test_create_alert():
    """Test creating a simple price alert"""
    # Create a condition
    condition = AlertCondition("BTC", GREATER, 70000)
    
    # Create an alert
    alert = PriceAlert([condition], "test_user")
    
    # Print alert details
    print(f"Created alert: {alert}")
    print(f"Alert ID: {alert.alert_id}")
    print(f"Condition: {condition}")
    
    return alert

def test_check_alert(alert, price):
    """Test checking if an alert condition is met"""
    # Create a prices dictionary
    prices = {"BTC": price}
    
    # Check if the alert condition is met
    result = alert.check(prices)
    
    # Print result
    print(f"Alert condition met: {result}")
    print(f"Current price: ${price}")
    
    return result

def test_complex_alert():
    """Test creating and checking a complex alert with AND/OR logic"""
    # Create conditions
    condition1 = AlertCondition("BTC", GREATER, 70000)
    condition2 = AlertCondition("ETH", LESS, 3000)
    
    # Create an alert with AND logic
    alert_and = PriceAlert([condition1, condition2], "test_user", AND)
    
    # Create an alert with OR logic
    alert_or = PriceAlert([condition1, condition2], "test_user", OR)
    
    # Print alert details
    print(f"Created AND alert: {alert_and}")
    print(f"Created OR alert: {alert_or}")
    
    # Test with different price combinations
    prices1 = {"BTC": 75000, "ETH": 2500}  # Both conditions met
    prices2 = {"BTC": 75000, "ETH": 3500}  # Only BTC condition met
    prices3 = {"BTC": 65000, "ETH": 2500}  # Only ETH condition met
    prices4 = {"BTC": 65000, "ETH": 3500}  # No conditions met
    
    # Check AND alert
    print("\nTesting AND alert:")
    print(f"Prices 1 (BTC: ${prices1['BTC']}, ETH: ${prices1['ETH']}): {alert_and.check(prices1)}")
    print(f"Prices 2 (BTC: ${prices2['BTC']}, ETH: ${prices2['ETH']}): {alert_and.check(prices2)}")
    print(f"Prices 3 (BTC: ${prices3['BTC']}, ETH: ${prices3['ETH']}): {alert_and.check(prices3)}")
    print(f"Prices 4 (BTC: ${prices4['BTC']}, ETH: ${prices4['ETH']}): {alert_and.check(prices4)}")
    
    # Check OR alert
    print("\nTesting OR alert:")
    print(f"Prices 1 (BTC: ${prices1['BTC']}, ETH: ${prices1['ETH']}): {alert_or.check(prices1)}")
    print(f"Prices 2 (BTC: ${prices2['BTC']}, ETH: ${prices2['ETH']}): {alert_or.check(prices2)}")
    print(f"Prices 3 (BTC: ${prices3['BTC']}, ETH: ${prices3['ETH']}): {alert_or.check(prices3)}")
    print(f"Prices 4 (BTC: ${prices4['BTC']}, ETH: ${prices4['ETH']}): {alert_or.check(prices4)}")
    
    return alert_and, alert_or

def test_alert_manager():
    """Test the PriceAlertManager"""
    # Get the alert manager
    manager = get_alert_manager()
    
    # Create a condition and alert
    condition = AlertCondition("BTC", GREATER, 70000)
    alert = PriceAlert([condition], "test_user")
    
    # Add the alert to the manager
    alert_id = manager.add_alert(alert)
    
    # Print alert details
    print(f"Added alert to manager: {alert}")
    print(f"Alert ID: {alert_id}")
    
    # Get alerts for user
    alerts = manager.get_alerts_for_user("test_user")
    print(f"Alerts for user: {len(alerts)}")
    
    # Remove the alert
    removed = manager.remove_alert(alert_id)
    print(f"Alert removed: {removed}")
    
    # Get alerts for user again
    alerts = manager.get_alerts_for_user("test_user")
    print(f"Alerts for user after removal: {len(alerts)}")
    
    return manager

def test_command_parsing():
    """Test parsing alert commands"""
    from price_alerts_refactored import parse_alert_command
    
    # Test simple commands
    commands = [
        "BTC 70000",
        "ETH > 3000",
        "ADA < 0.5",
        "INVALID",
        "BTC -1000",
    ]
    
    for cmd in commands:
        success, message, alert = parse_alert_command(cmd, "test_user")
        print(f"Command: {cmd}")
        print(f"Success: {success}")
        print(f"Message: {message}")
        print(f"Alert: {alert}")
        print()
    
    # Test complex commands
    complex_commands = [
        "BTC > 70000 and ETH < 3000",
        "ADA > 0.5 or SOL < 100",
        "BTC > 70000 and INVALID",
    ]
    
    for cmd in complex_commands:
        success, message, alert = parse_alert_command(cmd, "test_user")
        print(f"Complex command: {cmd}")
        print(f"Success: {success}")
        print(f"Message: {message}")
        print(f"Alert: {alert}")
        print()

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        if test_name == "create":
            test_create_alert()
        elif test_name == "check":
            alert = test_create_alert()
            price = float(sys.argv[2]) if len(sys.argv) > 2 else 65000
            test_check_alert(alert, price)
        elif test_name == "complex":
            test_complex_alert()
        elif test_name == "manager":
            test_alert_manager()
        elif test_name == "parse":
            test_command_parsing()
        else:
            print(f"Unknown test: {test_name}")
    else:
        # Run all tests
        print("=== Testing Alert Creation ===")
        alert = test_create_alert()
        print("\n=== Testing Alert Checking ===")
        test_check_alert(alert, 65000)
        test_check_alert(alert, 75000)
        print("\n=== Testing Complex Alerts ===")
        test_complex_alert()
        print("\n=== Testing Alert Manager ===")
        test_alert_manager()
        print("\n=== Testing Command Parsing ===")
        test_command_parsing()

if __name__ == "__main__":
    main()
