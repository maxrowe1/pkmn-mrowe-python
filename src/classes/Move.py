class Move:
    def __init__(self, **kwargs):

        self.id = kwargs["id"]
        self.name = kwargs["name"]
        self.type = get_arg("move_type",kwargs)
        self.category = kwargs["category"]
        self.power = get_arg("move_power",kwargs)
        self.accuracy = kwargs["accuracy"]
        self.base_pp = kwargs["base_pp"]
        self.stat = kwargs["stat"]
        self.target_self = kwargs["target_self"]
        self.stage_effect = kwargs["stage_effect"]
        self.can_crit = kwargs["can_crit"]

        # Combatant move data
        self.combatant_id = None
        self.number = None
        self.pp_current = None
        self.set_combatant_data(**kwargs)

    def set_combatant_data(self, **kwargs):
        if "combatant_id" in kwargs.keys():
            self.combatant_id = kwargs["combatant_id"]
            self.number = get_arg("move_number",kwargs)
            self.pp_current = kwargs["pp_current"]

get_arg = lambda x, kwargs: kwargs[x if x in kwargs.keys() else x.replace("move_", "")]