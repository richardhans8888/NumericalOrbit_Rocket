# rocket/fuel_system.py

class FuelSystem:
    def __init__(self, initial_fuel):
        self.fuel = initial_fuel
        self.initial_fuel = initial_fuel
        self.consumed = 0.0
        self.empty = (self.fuel <= 0.0)
        
    def consume(self, amount):
        if self.empty:
            return 0.0
            
        consumed = min(amount, self.fuel)
        self.fuel -= consumed
        self.consumed += consumed
        if self.fuel <= 0.0:
            self.fuel = 0.0
            self.empty = True
        return consumed

