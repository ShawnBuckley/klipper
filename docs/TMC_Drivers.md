This document provides information on using Trinamic stepper motor
drivers in SPI/UART mode on Klipper.

Klipper can also use Trinamic drivers in their "standalone mode".
However, when the drivers are in this mode, no special Klipper
configuration is needed and the advanced Klipper features discussed in
this document are not available.

In addition to this document, be sure to review the [TMC driver config
reference](Config_Reference.md#tmc-stepper-driver-configuration).

# Enabling "Stealthchop" mode

By default, Klipper places the TMC drivers in "spreadcycle" mode. If
the driver supports "stealthchop" then it can be enabled by adding
`stealthchop_threshold: 999999` to the TMC config section.

It is recommended to always use "spreadcycle" mode (by not specifying
`stealthchop_threshold`) or to always use "stealthchop" mode (by
setting `stealthchop_threshold` to 999999). Unfortunately, the drivers
often produce poor and confusing results if the mode changes while the
motor is at a non-zero velocity.

# Sensorless Homing

Sensorless homing allows to home an axis without the need for a
physical limit switch. Instead, the carriage on the axis is moved into
the mechanical limit making the stepper motor lose steps. The stepper
driver senses the lost steps and indicates this to the controlling MCU
(Klipper) by toggling a pin. This information can be used by Klipper
as end stop for the axis.

This guide covers the setup of sensorless homing for the X axis of
your (cartesian) printer. However, it works the same with all other
axes (that require an end stop). You should configure and tune it for
one axis at a time.

## Limitations

Be sure that your mechanical components are able to handle the load of
the carriage bumping into the limit of the axis repeatedly. Especially
leadscrews might generate a lot of force. Homing a Z axis by bumping
the nozzle into the printing surface might not be a good idea.

Further, sensorless homing might not be accurate enough for your
printer. While homing X and Y axes on a cartesian machine can work
well, homing the Z axis is generally not accurate enough and may
result in an inconsistent first layer height. Homing a delta printer
sensorless is not advisable due to missing accuracy.

Further, the stall detection of the stepper driver is dependent on the
mechanical load on the motor, the motor current and the motor
temperature (coil resistance).

Sensorless homing works best at medium motor speeds. For very slow
speeds (less than 10 RPM) the motor does not generate significant back
EMF and the TMC cannot reliably detect motor stalls. Further, at very
high speeds, the back EMF of the motor approaches the supply voltage
of the motor, so the TMC cannot detect stalls anymore. It is advised
to have a look in the datasheet of your specific TMCs. There you can
also find more details on limitations of this setup.

## Prerequisites

A few prerequisites are needed to use sensorless homing:

1. A StallGuard capable TMC stepper driver (any TMC driver except for
   tmc2208 series).
2. SPI / UART interface of the TMC driver wired to micro-controller
   (stand-alone mode does not work).
3. The appropriate "DIAG" or "SG_TST" pin of TMC driver connected to
   the micro-controller.
4. The steps in the [config checks](Config_checks.md) document must be
   run to confirm that the basic settings for the stepper motors,
   stepper driver, and homing direction are working correctly.

## Tuning

The procedure described here has six major steps:
1. Choose a homing speed.
2. Configure the `printer.cfg` file to enable sensorless homing.
3. Find the stallguard setting with highest sensitivity that
   successfully homes.
4. Find the stallguard setting with lowest sensitivity that
   successfully homes with a single touch.
5. Update the `printer.cfg` with the desired stallguard setting.
6. Create or update `printer.cfg` macros to home consistently.

### Choose homing speed

The homing speed is an important choice when performing sensorless
homing. It's desirable to use a slow homing speed so that the carriage
does not exert excessive force on the frame when making contact with
the end of the rail. However, the TMC drivers can't reliably detect a
stall at very slow speeds.

A good starting point for the homing speed is for the stepper motor to
make a full rotation every two seconds. For many axes this will be the
`rotation_distance` divided by two. For example:
```
[stepper_x]
rotation_distance: 40
homing_speed: 20
...
```

### Configure printer.cfg for sensorless homing

The `homing_retract_dist` setting must be set to zero in the
`stepper_x` config section to disable the second homing move. The
second homing attempt does not add value when using sensorless homing,
it will not work reliably, and it will confuse the tuning process.

Be sure that a `hold_current` setting is not specified in the TMC
driver section of the config. (If a hold_current is set then after
contact is made, the motor stops while the carriage is pressed against
the end of the rail, and reducing the current while in that position
may cause the carriage to move - that results in poor performance and
will confuse the tuning process.)

It is necessary to configure the sensorless homing pins and to
configure initial "stallguard" settings. A tmc2209 example
configuration for an X axis might look like:
```
[tmc2209 stepper_x]
diag_pin: ^PA1      # Set to MCU pin connected to TMC DIAG pin
driver_SGTHRS: 255  # 255 is most sensitive value, 0 is least sensitive
...

[stepper_x]
endstop_pin: tmc2209_stepper_x:virtual_endstop
homing_retract_dist: 0
...
```

An example tmc2130 or tmc5160 config might look like:
```
[tmc2130 stepper_x]
diag1_pin: ^!PA1 # Pin connected to TMC DIAG1 pin (or use diag0_pin / DIAG0 pin)
driver_SGT: -64  # -64 is most sensitive value, 63 is least sensitive
...

[stepper_x]
endstop_pin: tmc2130_stepper_x:virtual_endstop
homing_retract_dist: 0
...
```

An example tmc2660 config might look like:
```
[tmc2660 stepper_x]
driver_SGT: -64     # -64 is most sensitive value, 63 is least sensitive
...

[stepper_x]
endstop_pin: ^PA1   # Pin connected to TMC SG_TST pin
homing_retract_dist: 0
...
```

The examples above only show settings specific to sensorless
homing. See the [config
reference](Config_Reference.md#tmc-stepper-driver-configuration) for
all the available options.

### Find highest sensitivity that successfully homes

Place the carriage near the center of the rail. Use the SET_TMC_FIELD
command to set the highest sensitivity. For tmc2209:
```
SET_TMC_FIELD STEPPER=stepper_x FIELD=SGTHRS VALUE=255
```
For tmc2130, tmc5160, and tmc2660:
```
SET_TMC_FIELD STEPPER=stepper_x FIELD=SGT VALUE=-64
```

Then issue a `G28 X0` command and verify the axis does not move at
all. If the axis does move, then issue an `M112` to halt the printer -
something is not correct with the diag/sg_tst pin wiring or
configuration and it must be corrected before continuing.

Next, continually decrease the sensitivity of the `VALUE` setting and
run the `SET_TMC_FIELD` `G28 X0` commands again to find the highest
sensitivity that results in the carriage successfully moving all the
way to the endstop and halting. (For tmc2209 drivers this will be
decreasing SGTHRS, for other drivers it will be increasing SGT.) Be
sure to start each attempt with the carriage near the center of the
rail (if needed issue `M84` and then manually move the carriage to the
center). It should be possible to find the highest sensitivity that
homes reliably (settings with higher sensitivity results in small or
no movement). Note the found value as `maximum_sensitivity`. (If the
minimum possible sensitivity (SGTHRS=0 or SGT=63) is obtained without
any carriage movement then something is not correct with the
diag/sg_tst pin wiring or configuration and it must be corrected
before continuing.)

When searching for maximum_sensitivity, it may be convenient to jump
to different VALUE settings (so as to bisect the VALUE parameter). If
doing this then be prepared to issue an `M112` command to halt the
printer, as a setting with a very low sensitivity may cause the axis
to repeatedly "bang" into the end of the rail.

### Find lowest sensitivity that homes with one touch

When homing with the found `maximum_sensitivity` value, the axis
should move to the end of the rail and stop with a "single touch" -
that is, there should not be a "clicking" or "banging" sound. (If
there is a banging or clicking sound at maximum_sensitivity then the
homing_speed may be too low, the driver current may be too low, or
sensorless homing may not be a good choice for the axis.)

The next step is to again continually move the carriage to a position
near the center of the rail, decrease the sensitivity, and run the
`SET_TMC_FIELD` `G28 X0` commands - the goal is now to find the lowest
sensitivity that still results in the carriage successfully homing
with a "single touch". That is, it does not "bang" or "click" when
contacting the end of the rail. Note the found value as
`minimum_sensitivity`.

### Update printer.cfg with sensitivity value

After finding `maximum_sensitivity` and `minimum_sensitivity`, use a
calculator to obtain the recommend sensitivity as
`minimum_sensitivity + (maximum_sensitivity - minimum_sensitivity)/3`.
The recommended sensitivity should be in the range between the minimum
and maximum, but slightly closer to the minimum. Round the final value
to the nearest integer value.

For tmc2209 set this in the config as `driver_SGTHRS`, for other TMC
drivers set this in the config as `driver_SGT`.

If the range between `maximum_sensitivity` and `minimum_sensitivity`
is small (eg, less than 10) then it may result in unstable homing. A
faster homing speed may increase the range and make the operation more
stable.

Note that if any change is made to driver current, homing speed, or a
notable change is made to the printer hardware, then it will be
necessary to run the tuning process again.

### Using Macros when Homing

After sensorless homing completes the carriage will end up pressed
against the end of the rail and the stepper will exert a force on the
frame until the carriage is moved away. It is a good idea to create a
macro to home the axis and immediately move the carriage away from the
end of the rail.

It can also be useful to have that macro set the driver current before
homing and set a new current after the carriage has moved away. This
also allows a hold_current to be set during prints (a hold_current
is not recommended during sensorless homing).

An example macro might look like:
```
[gcode_macro SENSORLESS_HOME_X]
default_parameter_HOMECUR: 0.700
default_parameter_RUNCUR:  0.800
default_parameter_HOLDCUR: 0.500
gcode:
    # Set current for sensorless homing
    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOMECUR} HOLDCURRENT={HOMECUR}
    # Home
    G28 X0
    # Move away
    G90
    G1 X40 F1200
    # Set current during print
    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={RUNCUR} HOLDCURRENT={HOLDCUR}
```

The resulting macro can be called from a [homing_override config
section](Config_Reference.md#homing_override) or from a [START_PRINT
macro](Slicers.md#klipper-gcode_macro).

Note that if the driver current during homing is changed, then the
tuning process should be run again.

# Querying and diagnosing driver settings

The `[DUMP_TMC command](G-Codes.md#tmc-stepper-drivers) is a useful
tool when configuring and diagnosing the drivers. It will report all
fields configured by Klipper as well as all fields that can be queried
from the driver.

All of the reported fields are defined in the Trinamic datasheet for
each driver. These datasheets can be found on the [Trinamic
website](https://www.trinamic.com/). Obtain and review the Trinamic
datasheet for the driver to interpret the results of DUMP_TMC.

# Configuring driver_XXX settings

Klipper supports configuring many low-level driver fields using
`driver_XXX` settings. The [TMC driver config
reference](Config_Reference.md#tmc-stepper-driver-configuration) has
the full list of fields available for each type of driver.

In addition, almost all fields can be modified at run-time using the
[SET_TMC_FIELD command](G-Codes.md#tmc-stepper-drivers).

Each of these fields is defined in the Trinamic datasheet for each
driver. These datasheets can be found on the [Trinamic
website](https://www.trinamic.com/).

Note that the Trinamic datasheets sometime use wording that can
confuse a high-level setting (such as "hysteresis end") with a
low-level field value (eg, "HEND"). In Klipper, `driver_XXX` and
SET_TMC_FIELD always set the low-level field value that is actually
written to the driver. So, for example, if the Trinamic datasheet
states that a value of 3 must be written to the HEND field to obtain a
"hysteresis end" of 0, then set `driver_HEND=3` to obtain the
high-level value of 0.

# Common Questions

## Can I use stealthchop mode on an extruder with pressure advance?

Many people successfully use "stealthchop" mode with Klipper's
pressure advance. Klipper implements [smooth pressure
advance](Kinematics.md#pressure-advance) which does not introduce any
instantaneous velocity changes.

However, "stealthchop" mode may produce lower motor torque and/or
produce higher motor heat. It may or may not be an adequate mode for
your particular printer.

## I keep getting "Unable to read tmc uart 'stepper_x' register IFCNT" errors?

This occurs when Klipper is unable to communicate with a tmc2208 or
tmc2209 driver.

Make sure that the motor power is enabled, as the stepper motor driver
generally needs motor power before it can communicate with the
micro-controller.

Otherwise, this error is typically the result of incorrect UART pin
wiring or an incorrect Klipper configuration of the UART pin settings.

## I keep getting "Unable to write tmc spi 'stepper_x' register ..." errors?

This occurs when Klipper is unable to communicate with a tmc2130 or
tmc5160 driver.

Make sure that the motor power is enabled, as the stepper motor driver
generally needs motor power before it can communicate with the
micro-controller.

Otherwise, this error is typically the result of incorrect SPI wiring,
an incorrect Klipper configuration of the SPI settings, or an
incomplete configuration of devices on an SPI bus.

Note that if the driver is on a shared SPI bus with multiple devices
then be sure to fully configure every device on that shared SPI bus in
Klipper. If a device on a shared SPI bus is not configured, then it
may incorrectly respond to commands not intended for it and corrupt
the communication to the intended device. If there is a device on a
shared SPI bus that can not be configured in Klipper, then use a
[static_digital_output config
section](Config_Reference.md#static_digital_output) to set the CS pin
of the unused device high (so that it will not attempt to use the SPI
bus). The board's schematic is often a useful reference for finding
which devices are on an SPI bus and their associated pin settings.

## How do I tune spreadcycle/coolstep/etc. mode on my drivers?

The [Trinamic website](https://www.trinamic.com/) has guides on
configuring the drivers. These guides are often technical, low-level,
and may require specialized hardware. Regardless, they are the best
source of information.
