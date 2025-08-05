# Bioreactor Controller Lite

This project implements a controller for a bioreactor system using a microcontroller running MicroPython. It manages compressors, a pump, and provides status updates via an LCD screen. The system is designed to be robust, with different operational modes and a logging system.

## Features

- Automatic control of two alternating compressors.
- Scheduled and manual control of a nutrient pump.
- LCD display for real-time status monitoring (runtime, pump status, compressor hours).
- Multiple operational modes: `NORMAL`, `DEMO`, `EMERGENCY`, and `PROGRAM`.
- Event logging to a file with log rotation.
- Visual status indicator (LED).
- Real-Time Clock (RTC) synchronization for accurate timekeeping.
- Watchdog timer for system stability.

## Hardware Requirements

- A MicroPython-compatible microcontroller (e.g., ESP32).
- I2C LCD Display (PCF8574 driver, address 0x27).
- DS3231 RTC Module (address 0x68).
- Relays for compressors and pump.
- A physical button for manual control.
- A flow meter (YF-B1 or similar).
- Switches to select the operational mode.
- An indicator LED.

## Software Requirements

- MicroPython firmware for the target microcontroller.

## Setup

1.  Flash the MicroPython firmware onto the microcontroller.
2.  Connect the hardware components according to the definitions in `device/config/pins.py`.
3.  Upload the **contents** of the `device/` folder to the root directory of the ESP32's filesystem. **Important:** Do not copy the `device` folder itself, but rather the files and folders inside it (e.g., `boot.py`, `main.py`, the `config` folder, etc.).

## Operation

The system's operational mode is determined at boot time by the state of two switches connected to `MODE_SW1_PIN` and `MODE_SW2_PIN`.

-   **PROGRAM** (both switches OFF): System boots into the REPL for debugging and development. No tasks are started.
-   **WORKING** (SW1 ON, SW2 OFF): Normal operation mode. All tasks are started.
-   **DEMO** (SW1 OFF, SW2 ON): Demo mode. Time is accelerated (`DEMO_TIME_FACTOR`).
-   **EMERGENCY** (both switches ON): Only the compressor alternation task runs.

The physical button can be used to manually toggle the pump on and off.

## Project Structure

### Device Code (`device/`)

This folder contains all the code that should be uploaded to the ESP32.

-   **`boot.py`**: Initializes the system, sets the operation mode, and synchronizes the RTC.
-   **`main.py`**: Main entry point of the application; starts system tasks.
-   **`system_state.py`**: Manages the system's operational mode.
-   **`config/`**: Contains configuration files for pins and runtime parameters.
-   **`hw/`**: Modules for controlling hardware components (button, indicator, relays).
-   **`sensors/`**: Modules for reading sensor data.
-   **`tasks/`**: High-level tasks for control and display logic.
-   **`ui/`**: User interface code, primarily for the LCD.
-   **`utils/`**: Utility modules like the logger and hardware drivers.

### Testing (`tests/`)

This folder contains scripts for testing the system's functionality.

-   **`run_test.py`**: A guided test suite for technicians.
-   **`t01_...` to `t08_...`**: Individual tests for each module.

## Testing

The project includes a suite of tests in the `tests/` directory to verify functionality.

**Important Note on Testing:** The tests are not fully automated. They are designed as a guided checklist for a technician. The person running the tests will need to follow the on-screen instructions and **physically observe the system's behavior** (e.g., check if an LED turns on, if a relay clicks, if the pump activates) to confirm that the hardware is responding correctly.

-   **`tests/run_test.py`**: This is the main test suite for technicians. Run this script from the REPL for a guided, visual inspection of the hardware.
-   **`tests/t01_...` to `t08_...`**: These are individual component tests that can also be run from the REPL for more granular debugging.

## License

This project is licensed under the terms of the LICENSE file.
