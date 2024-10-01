class Move:
    def __init__(self,move_dict: dict):
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

        # Combatant move data
        self.combatant_id = None
        self.number = None
        self.pp_current = None
        self.set_combatant_data(move_dict)

    def set_combatant_data(self, move_dict):
        if "combatant_id" in move_dict.keys():
            self.combatant_id = move_dict["combatant_id"]
            self.number = move_dict["move_number"]
            self.pp_current = move_dict["pp_current"]
