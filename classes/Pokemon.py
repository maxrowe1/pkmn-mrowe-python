class Pokemon:
    def __init__(self, pokemon_dict):
        if isinstance(pokemon_dict, Pokemon):
            self.__dict__ = pokemon_dict.__dict__.copy()
        else:
            self.id = pokemon_dict["id"]
            self.name = pokemon_dict["name"]
            self.type1 = pokemon_dict["type1"]
            self.type2 = pokemon_dict["type2"]