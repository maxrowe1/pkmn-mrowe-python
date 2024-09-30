class Move:
    def __init__(self,move_dict):
        self.id = move_dict["id"]
        self.name = move_dict["name"]
        self.type = move_dict["move_type"]
        self.category = move_dict["category"]
        self.power = move_dict["move_power"]
        self.accuracy = move_dict["accuracy"]
        self.base_pp = move_dict["base_pp"]
        self.stat = move_dict["stat"]
        self.target_self = move_dict["target_self"]
        self.stage_effect = move_dict["stage_effect"]
        self.can_crit = move_dict["can_crit"]