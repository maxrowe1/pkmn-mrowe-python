class BaseStats:
    def __init__(self, base_stats_dict):
        self.hp_min = base_stats_dict["hp_min"]
        self.hp_max = base_stats_dict["hp_max"]
        self.attack_min = base_stats_dict["attack_min"]
        self.attack_max = base_stats_dict["attack_max"]
        self.defense_min = base_stats_dict["defense_min"]
        self.defense_max = base_stats_dict["defense_max"]
        self.sp_attack_min = base_stats_dict["sp_attack_min"]
        self.sp_attack_max = base_stats_dict["sp_attack_max"]
        self.sp_defense_min = base_stats_dict["sp_defense_min"]
        self.sp_defense_max = base_stats_dict["sp_defense_max"]
        self.speed_min = base_stats_dict["speed_min"]
        self.speed_max = base_stats_dict["speed_max"]