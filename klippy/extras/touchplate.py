
import homing

class Touchplate:
    def __init__(self, config):
        self.printer = config.get_printer()

        self.x_offset = config.getfloat('x_offset')
        self.y_offset = config.getfloat('y_offset')
        self.z_offset = config.getfloat('z_offset')

        self.x_position = config.getfloat('x_position')
        self.y_position = config.getfloat('y_position')
        self.z_position = config.getfloat('z_position')
        self.speed = config.getfloat('speed', 50.0, above=0.)
        # self.has_absolute_home = config.getboolean('has_absolute_home', True)

        self.gcode = self.printer.lookup_object('gcode')

        # self.prev_G28 = self.gcode.register_command("G28", None)
        self.gcode.register_command("PROBE_TOUCHPLATE", self.cmd_PROBE_TOUCHPLATE)

    def cmd_PROBE_TOUCHPLATE(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        # z_endstop = None

        # ignore axis provided and always do all

        ##################################################
        # Z

        # move to touchplate

        toolhead.manual_move([
            None,
            None,
            self.z_position + self.z_offset
        ], self.speed)
        toolhead.manual_move([
            self.x_position,
            self.y_position,
            self.z_position + self.z_offset
        ], self.speed)

        # probe Z
        # hmove = homing.HomingMove(self.printer, [z_endstop])
        # touchplateTriggeredZ = hmove.homing_move([
        #     self.x_position,
        #     self.y_position,
        #     self.z_position
        # ], self.speed)[2]

        toolhead.manual_move([
            self.x_position,
            self.y_position,
            self.z_position + self.z_offset
        ], self.speed)

        ###############################################
        # Y

        # move from Z to Y position
        toolhead.manual_move([
            self.x_position,
            self.y_position + self.y_offset,
            self.z_position + self.z_offset
        ], self.speed)
        toolhead.manual_move([
            self.x_position,
            self.y_position + self.y_offset,
            self.z_position
        ], self.speed)

        # probe Y
        # hmove = homing.HomingMove(self.printer, [z_endstop])
        # touchplateTriggeredY = hmove.homing_move([
        #     self.x_position,
        #     self.y_position,
        #     self.z_position
        # ], self.speed)[2]

        toolhead.manual_move([
            self.x_position,
            self.y_position + self.y_offset,
            self.z_position
        ], self.speed)

        ###############################################
        # X

        # move from Y to X
        toolhead.manual_move([
            self.x_position + self.x_offset,
            self.y_position + self.y_offset,
            self.z_position
        ], self.speed)
        toolhead.manual_move([
            self.x_position + self.x_offset,
            self.y_position,
            self.z_position
        ], self.speed)

        # probe X
        # hmove = homing.HomingMove(self.printer, [z_endstop])
        # touchplateTriggeredX = hmove.homing_move([
        #     self.x_position,
        #     self.y_position,
        #     self.z_position
        # ], self.speed)[2]

        toolhead.manual_move([
            self.x_position + self.x_offset,
            self.y_position,
            self.z_position
        ], self.speed)

        ###############################################
        # done

        # move from X to Z
        toolhead.manual_move([
            self.x_position + self.x_offset,
            self.y_position,
            self.z_position + self.z_position
        ], self.speed)
        toolhead.manual_move([
            self.x_position,
            self.y_position,
            self.z_position + self.z_position
        ], self.speed)

        # set the new home
        # newHome = [
        #     touchplateTriggeredX, -
        #     touchplateTriggeredY,
        #     touchplateTriggeredZ]
        # toolhead.set_position(newHome)

        # set the new limit to prevent out of range moves

def load_config(config):
    return Touchplate(config)