from config_dict    import DetectorConfig
from threading      import Thread

class CommandCenter:
    config : DetectorConfig = None
    thread : Thread         = None
    enabled: bool           = False
    exit   : bool           = False

    def start(self):
        self.enabled = True
        self.thread = Thread(target=self.run_commands)
        self.thread.start()

    def stop(self):
        if self.thread is None:
            print("Attempted to kill a command center thread that doesn't exist.")
            return False
        self.enabled = False
        self.thread.join()
        return True
    
    def restart(self):
        self.stop()
        self.start()

    def alive(self):
        return self.thread is not None and self.thread.is_alive()

    def request_exit(self):
        self.exit = True
        return True
    
    def check_exit(self):
        return self.exit

    CMD_FUNC = "func"
    CMD_ARGS = "arg_cnt"

    CMD_ACCESS_CONTROL = "control"

    CMD_CONTROL_EXIT = "exit"
    CMD_CONTROL_RESTART = "restart"

    CMD_CONTROL_ALL = {
        CMD_CONTROL_EXIT : {
            CMD_FUNC    : lambda self : self.request_exit(),
            CMD_ARGS    : 0  
        },
    }

    CMD_ACCESS_CFG = "config"
    
    CMD_CFG_SET = "set"
    CMD_CFG_GET = "get"
    CMD_CFG_RESET = "reset"
    CMD_CFG_VIEW = "view"
    CMD_CFG_RESET_ALL = "reset-all"
    CMD_CFG_EXPORT = "export"

    CMD_CFG_ALL = { CMD_CFG_SET         :   {
                                                CMD_FUNC    :   lambda self, a1, a2 : self.config.update_entry(a1,a2),
                                                CMD_ARGS    :   2
                                            },
                    CMD_CFG_GET         :   {
                                                CMD_FUNC    :   lambda self, a1 : self.config.get_entry(a1),
                                                CMD_ARGS    :   1
                                            },
                    CMD_CFG_RESET       :   {
                                                CMD_FUNC    :   lambda self, a1 : self.config.reset_entry(a1),
                                                CMD_ARGS    :   1
                                            },
                    CMD_CFG_VIEW        :   {
                                                CMD_FUNC    :   lambda self : self.config.view_configuration(),
                                                CMD_ARGS    :   0
                                            },
                    CMD_CFG_RESET_ALL   :   {
                                                CMD_FUNC    :   lambda self : self.config.to_defaults(),
                                                CMD_ARGS    :   0
                                            },
                    CMD_CFG_EXPORT      :   {
                                                CMD_FUNC    :   lambda self : self.config.export_configuration(),
                                                CMD_ARGS    :   0
                                            },
                   }
    CMD_DICT    =   {
        CMD_ACCESS_CFG      : CMD_CFG_ALL,
        CMD_ACCESS_CONTROL  : CMD_CONTROL_ALL
    }

    def __init__(self, config : DetectorConfig):
        self.config = config

    def parse_command(self, command : str):
        command_split = command.split()
        len_command = len(command_split)
        if len_command == 0:
            return
        search_dict = self.CMD_DICT
        last_idx_searched = 0
        for idx in range(len_command):
            if command_split[idx] not in search_dict:
                break
            search_dict = search_dict[command_split[idx]]
            last_idx_searched = idx
        remaining_split = command_split[last_idx_searched+1:]
        if self.CMD_FUNC not in search_dict or self.CMD_ARGS not in search_dict:
            print(f"Invalid command, suffix {remaining_split} is unknown.")
            return
        remaining_arg_length = len(remaining_split)
        required_arg_length = search_dict[self.CMD_ARGS]
        if required_arg_length > remaining_arg_length:
            print(f"Not enough arguments. Expected {required_arg_length} but got {remaining_arg_length}")
            return
        if required_arg_length < remaining_arg_length:
            print(f"Too many arguments. Expected {required_arg_length} but got {remaining_arg_length}")
            return
        print(self.run_command(search_dict[self.CMD_FUNC], required_arg_length, remaining_split))
    
    def run_command(self, command, arg_cnt : int, arg_lst : list):
        if arg_cnt < 0:
            return "Command with no arguments cannot be run!"
        if arg_cnt != len(arg_lst):
            return "Arg count and arg list lengths do not match!"
        if arg_cnt == 0:
            return f"Command result: {command(self)}"
        elif arg_cnt == 1:
            return f"Command result: {command(self, arg_lst[0])}"
        elif arg_cnt == 2:
            return f"Command result: {command(self, arg_lst[0], arg_lst[1])}"
        elif arg_cnt == 3:
            return f"Command result: {command(self, arg_lst[0], arg_lst[1], arg_lst[2])}"
        elif arg_cnt == 4:
            return f"Command result: {command(self, arg_lst[0], arg_lst[1], 
                                              arg_lst[2], arg_lst[3])}"
        elif arg_cnt == 5:
            return f"Command result: {command(self, arg_lst[0], arg_lst[1], 
                                              arg_lst[2], arg_lst[3], arg_lst[4])}"
        else:
            return "Got a command with an unsupported number of args."
        
    def run_commands(self):
        while self.enabled and not self.exit:
            self.parse_command(input("Enter a command: "))