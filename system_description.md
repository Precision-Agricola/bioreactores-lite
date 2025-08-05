
# Bioreactor Controller Python Files Description

This file provides a description of the Python files in the bioreactor controller project.

## Device Files

### `device/boot.py`

Initializes the system, sets the operation mode based on switch positions, and synchronizes the RTC.

### `device/main.py`

Main entry point of the application. It starts the different tasks of the system.

### `device/system_state.py`

Manages the system's current operational mode (e.g., 'NORMAL', 'DEMO', 'EMERGENCY').

### `device/config/pins.py`

Defines the GPIO pin configuration for all hardware components.

### `device/config/runtime.py`

Contains runtime configuration parameters like pump intervals and compressor cycle times.

### `device/hw/button.py`

Manages the physical button for manual pump control.

### `device/hw/indicator.py`

Controls a visual indicator (LED) to show the system status (INFO, WARNING, ERROR).

### `device/hw/relay_controller.py`

Manages the relays for the compressors and the pump.

### `device/hw/relays.py`

Provides a class to control the relays.

### `device/sensors/flow_meter.py`

Reads and interprets data from a flow meter sensor.

### `device/tasks/control_task.py`

Implements the main control logic for the bioreactor, including automatic pump and compressor cycles.

### `device/tasks/display_task.py`

Manages the information displayed on the LCD screen.

### `device/ui/display.py`

Handles the LCD display, including initialization and writing text.

### `device/utils/drivers/ds3231.py`

Driver for the DS3231 real-time clock (RTC).

### `device/utils/drivers/lcd_api.py`

API for interfacing with HD44780-compatible character LCDs.

### `device/utils/drivers/machine_i2c_lcd.py`

I2C implementation for the LCD display.

### `device/utils/logger.py`

A simple logger to log events to a file.

## Test Files

### `tests/run_test.py`

A guided test suite for technicians to visually inspect and verify the hardware components.

### `tests/t01_logger.py`

Tests the logger functionality, including log rotation.

### `tests/t02_indicator.py`

Tests the visual indicator (LED).

### `tests/t03_relays.py`

Tests the relay controller and the individual relays.

### `tests/t04_button_phys.py`

Physical test for the manual pump button.

### `tests/t04_button_sim.py`

Simulated test for the manual pump button.

### `tests/t05_control_task.py`

Tests the main control task.

### `tests/t06_flow_meter.py`

Tests the flow meter sensor.

### `tests/t07_display_driver.py`

Tests the LCD display driver.

### `tests/t08_display_task.py`

Tests the display task.
