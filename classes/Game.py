class Game:
    def __init__(self, group_dict: dict):
        self.id = group_dict["id"]
        self.player_combatant_id = group_dict["p_combatant_id"]
        self.enemy_combatant_id = group_dict["e_combatant_id"]
