class Game:
    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.player_combatant_id = kwargs["p_combatant_id"]
        self.enemy_combatant_id = kwargs["e_combatant_id"]
