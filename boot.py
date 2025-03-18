import network
import ntptime
import time

from machine import Pin

# List of known Wi-Fi networks with passwords
KNOWN_NETWORKS = {
    "Hous-fi": "nothomeless",
    "WorkWiFi": "securepass",
    "SchoolWiFi": "schoolpass"
}

# Eastern Timezone Constants
STANDARD_OFFSET = -5  # EST (Eastern Standard Time)
DST_OFFSET = -4  # EDT (Eastern Daylight Time)

# Connect to a known Wi-Fi network
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print("Scanning for available networks...")
    networks = wlan.scan()
    available_ssids = [net[0].decode() for net in networks]
    print("Available SSIDs:", available_ssids)
    
    for ssid, password in KNOWN_NETWORKS.items():
        if ssid in available_ssids:
            print(f"Connecting to {ssid}...")
            wlan.connect(ssid, password)
            
            for _ in range(10):
                if wlan.isconnected():
                    print(f"Connected to {ssid}: {wlan.ifconfig()}")
                    return True
                time.sleep(1)
            print(f"Failed to connect to {ssid}")
    
    print("No known networks found.")
    return False

# Get Current Time from NTP
def get_ntp_time():
    try:
        ntptime.settime()  # Sync time with NTP
        return time.localtime()  # Returns (year, month, day, hour, min, sec, weekday, yearday)
    except Exception as e:
        print(f"Failed to get NTP time: {e}")
        return None

# Check if Daylight Saving Time (DST) is in effect
def is_dst(year, month, day, weekday):
    """Determines if DST applies based on the second Sunday in March to the first Sunday in November."""
    if month < 3 or month > 11:
        return False  # January, February, December -> Standard Time
    if month > 3 and month < 11:
        return True  # April to October -> Daylight Saving Time
    
    # Handling March and November
    if month == 3:  # DST starts on second Sunday in March
        return day >= (14 - weekday)
    if month == 11:  # DST ends on first Sunday in November
        return day < (8 - weekday)
    
    return False

# Convert UTC to local Eastern Time with DST adjustment
def get_local_time_est():
    utc_time = get_ntp_time()
    if utc_time is None:
        return None
    
    year, month, day, hour, minute, second, weekday, _ = utc_time
    offset = DST_OFFSET if is_dst(year, month, day, weekday) else STANDARD_OFFSET
    hour += offset
    
    # Handle day rollover
    if hour < 0:
        hour += 24
        day -= 1
    elif hour >= 24:
        hour -= 24
        day += 1
    
    return year, month, day, hour, minute, second

# Calculate days since a specific date
def days_since(year, month, day):
    """Calculate the number of days elapsed since a past date."""
    local_time = get_local_time_est()
    if local_time is None:
        return None
    
    year_now, month_now, day_now, _, _, _ = local_time
    t1 = time.mktime((year, month, day, 0, 0, 0, 0, 0))
    t2 = time.mktime((year_now, month_now, day_now, 0, 0, 0, 0, 0))
    
    return (t2 - t1) // (24 * 3600)  # Convert seconds to days

# 7-Segment Display
# Segment GPIOs (Common Cathode Configuration)
SEGMENTS = {
    "A": Pin(33, Pin.OUT), # Pin 11 to GPIO 33
    "B": Pin(34, Pin.OUT), # Pin 7 to GPIO 34
    "C": Pin(35, Pin.OUT), # Pin 4 to GPIO 35
    "D": Pin(36, Pin.OUT), # Pin 2 to GPIO 36
    "E": Pin(37, Pin.OUT), # Pin 1 to GPIO 37
    "F": Pin(38, Pin.OUT), # Pin 10 to GPIO 38
    "G": Pin(39, Pin.OUT), # Pin 5 to GPIO 39
    "DP": Pin(40, Pin.OUT), # Pin 3 to GPIO 40
}

# Digit Select GPIOs (Common Cathode)
DIGITS = [
    Pin(5, Pin.OUT),  # Pin 12 to 330R to GPIO 5
    Pin(4, Pin.OUT),  # Pin 9 to 330R to GPIO 4
    Pin(3, Pin.OUT),  # Pin 8 to 330R to GPIO 3
    Pin(2, Pin.OUT),  # Pin 6 to 330R to GPIO 2
]

# 7-Segment digit mapping (0-9, Common Cathode)
DIGIT_MAP = {
    "0": [1, 1, 1, 1, 1, 1, 0, 0],
    "1": [0, 1, 1, 0, 0, 0, 0, 0],
    "2": [1, 1, 0, 1, 1, 0, 1, 0],
    "3": [1, 1, 1, 1, 0, 0, 1, 0],
    "4": [0, 1, 1, 0, 0, 1, 1, 0],
    "5": [1, 0, 1, 1, 0, 1, 1, 0],
    "6": [1, 0, 1, 1, 1, 1, 1, 0],
    "7": [1, 1, 1, 0, 0, 0, 0, 0],
    "8": [1, 1, 1, 1, 1, 1, 1, 0],
    "9": [1, 1, 1, 1, 0, 1, 1, 0],
    "-": [0, 0, 0, 0, 0, 0, 1, 0],  # Dash
    " ": [0, 0, 0, 0, 0, 0, 0, 0],  # Blank
}




def debug_digit(digit, position):
    """Lights up a single digit at a given position for debugging (Common Anode)."""
    if position < 0 or position > 3:
        print("Invalid position! Must be between 0 and 3.")
        return

    # Turn OFF all digits first (pull LOW to disable)
    for d in DIGITS:
        d.value(0)  # LOW = Disable digit

    # Get the correct segment pattern
    pattern = DIGIT_MAP.get(str(digit), DIGIT_MAP[" "])  # Default to blank if invalid

    # Ensure correct segment-to-pin mapping (explicit key lookup)
    SEGMENT_ORDER = ["A", "B", "C", "D", "E", "F", "G", "DP"]  # Defined order
    for seg_name, state in zip(SEGMENT_ORDER, pattern):
        SEGMENTS[seg_name].value(0 if state else 1)  # LOW = ON, HIGH = OFF for Common Anode

    # Enable only the selected digit (HIGH = Enable for common anode)
    DIGITS[position].value(1)

    print(f"Displaying {digit} at position {position}")

def display_number(number, cycles=50):
    """Displays a 4-digit number on the 7-segment display using multiplexing (Common Anode)."""

    # Convert number to a string and ensure it's within 4 characters
    str_num = str(int(number))

    # Manually pad with leading spaces if less than 4 digits
    if len(str_num) < 4:
        str_num = "0" * (4 - len(str_num)) + str_num  # Leading space padding

    SEGMENT_ORDER = ["A", "B", "C", "D", "E", "F", "G", "DP"]

    for _ in range(cycles):  # Run multiple cycles for persistence
        for i in (3, 2, 1, 0):  # Always loop through 4 digit positions
            
            # Get the digit to display (ensures leading spaces are handled)
            digit = str_num[i]
            #print(digit)

            # Turn OFF all digits first (prevent ghosting)
            for d in DIGITS:
                d.value(0)

            # Get segment pattern for the current digit
            pattern = DIGIT_MAP.get(digit, DIGIT_MAP[" "])  # Use blank if invalid

            # Apply segment states (LOW = ON, HIGH = OFF for Common Anode)
            for seg_name, state in zip(SEGMENT_ORDER, pattern):
                SEGMENTS[seg_name].value(0 if state else 1)

            # Enable the selected digit (HIGH = ON for Common Anode)
            DIGITS[i].value(1)

            # Short delay for multiplexing effect
            time.sleep(0.005)

            # Turn OFF the digit before moving to the next one
            DIGITS[i].value(0)



# Main Execution
def main():
    connect_wifi()
    since_days = 0  # Initialize with a default value
    last_update_time = 0
    
    while True:
        current_time = time.time()
        
        # Update the elapsed days only once per minute
        if current_time - last_update_time >= 60:
            last_update_time = current_time
            local_time = get_local_time_est()
            
            if local_time:
                since_days = days_since(2024, 3, 19)  # Change to your desired date
                if since_days is not None:
                    print(f"Days since 2024-03-19: {since_days}")
                else:
                    print("Error calculating elapsed days")
            else:
                print("Error retrieving time")
        
        # Continuously display the elapsed days without interruptions
        display_number(since_days)

if __name__ == "__main__":
    main()