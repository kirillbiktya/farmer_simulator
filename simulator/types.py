from typing import List, Optional, Tuple, Type
from simulator import exceptions
from simulator.utils import action, Option ,check_action_availability
from time import sleep

# region Base classes


class GameObject:
    name: str
    can_sell: bool = False
    buy_price: float = 0.

    @property
    def sell_price(self):
        # Определить в наследниках способ определения ценности для продажи
        raise NotImplementedError
    
    def __str__(self):
        raise NotImplementedError


class ProductItem(GameObject):
    qty: float
    can_sell = True

    def __str__(self):
        return f"{self.name} - {self.qty}"


class Creature(GameObject):
    age: int
    minimum_required_age_for_producing: int
    maximum_allowed_age_for_producing: int
    max_age: int
    producing_per_day: int
    max_product_amount: float
    product: Type[ProductItem]
    inventory: ProductItem
    needs: Type[ProductItem]
    needs_level: float
    critical_needs_level: float
    filled_needs_level: float
    full_needs_level: float
    needs_decreasing_per_day: float

    @property
    def critical_unfilled_needs(self):
        return self.needs_level < self.critical_needs_level

    @property
    def needs_filled(self):
        return self.needs_level > self.filled_needs_level

    def fill_the_needs(self, product: ProductItem):
        if not isinstance(product, self.needs):
            raise exceptions.WrongClass()
        
        if self.needs_level + product.qty > self.full_needs_level:
            diff = product.qty - (self.full_needs_level - self.needs_level)
            self.needs_level = self.full_needs_level
            product.qty = diff
        else:
            self.needs_level += product.qty
            product.qty = 0

    def harvest_products(self):
        qty = self.inventory.qty
        self.inventory.qty = 0.
        return self.product(qty=qty)

    def produce(self):
        if self.needs_filled and self.inventory.qty < self.max_product_amount:
            if self.minimum_required_age_for_producing < self.age and \
                self.maximum_allowed_age_for_producing > self.age:
                self.inventory.qty += self.producing_per_day

    def grow_up(self):
        if self.critical_unfilled_needs:
            raise exceptions.DeathFromUnfilledNeeds()
        
        if self.max_age - 1 == self.age:
            raise exceptions.DeathDueBigAge()
        
        self.age += 1

    def tick(self):
        self.grow_up()
        self.produce()
        self.needs_level -= self.needs_decreasing_per_day


class Animal(Creature):
    critical_needs_level = 20.
    filled_needs_level = 60.
    full_needs_level = 100.
    can_sell = True

    def __str__(self):
        return f"{self.name}: возраст {self.age}, сытость {self.needs_level}/{self.full_needs_level}"

    @property
    def sell_price(self):
        if self.age < self.minimum_required_age_for_producing:
            return self.buy_price * 0.7
        elif self.age > self.maximum_allowed_age_for_producing:
            return self.buy_price * 0.5
        else:
            return self.buy_price * 1.2


class Plant(Creature):
    critical_needs_level = 60.
    filled_needs_level = 70.
    full_needs_level = 100.

    def __str__(self):
        return f"{self.name}: возраст {self.age}, влажность {self.needs_level}/{self.full_needs_level}"


class Building(GameObject):
    lvl: int
    max_lvl: int
    _base_upgrade_price: float
    _upgrade_price_coeff: float
    slots: int
    _slots_growth_with_lvl: int
    can_contain_types: Tuple[Type]
    inventory: List[Creature]

    @property
    def upgrade_price(self):
        return self._base_upgrade_price * self.lvl * self._upgrade_price_coeff

    @property
    def slots_available(self):
        return self.slots - len(self.inventory)
    
    def __str__(self):
        ret = f"{self.name} - {self.lvl} lvl (Слотов доступно {self.slots_available} из {self.slots})\n"
        ret += f"{'\n'.join(str(x) for x in self.inventory)}"
        return ret

    def upgrade(self):
        if self.lvl == self.max_lvl:
            raise exceptions.MaximumLevelReached()
        
        self.lvl += 1
        self.slots += self._slots_growth_with_lvl

    def place_creature(self, creature: Creature):
        if not isinstance(creature, self.can_contain_types):
            raise exceptions.WrongClass()
        
        if len(self.inventory) == self.slots:
            raise exceptions.NoMoreSpaceAvailable()
        
        self.inventory.append(creature)


class Farm(GameObject):
    building_slots: int
    buildings: List[Building]
    storage: List[ProductItem]

    @property
    def space_available(self):
        return self.building_slots - len(self.buildings)
    
    def __init__(self, building_slots: int, buildings: List[Building], creatures: List[Creature], products: List[ProductItem]):
        super().__init__()
        self.building_slots = building_slots
        self.buildings = buildings
        for creature in creatures:
            for building in self.buildings:
                if building.slots_available > 0 and type(creature) in building.can_contain_types:
                    building.place_creature(creatures.pop(creatures.index(creature)))

        self.storage = products

    def __str__(self):
        ret = ["\nСклад фермы:", '\n'.join(str(x) for x in self.storage), "\nПостройки:", '\n'.join(str(x) for x in self.buildings)]
        return '\n'.join(ret)

    def place_building(self, building_type: Type[Building]):
        if self.space_available == 0:
            raise exceptions.NoMoreSpaceAvailable()
        
        self.buildings.append(building_type())

    def place_in_storage(self, product: ProductItem):
        p = list(filter(lambda x: type(x) is type(product), self.storage))
        if len(p) == 0:
            self.storage.append(product)
        else:
            p[0].qty += product.qty

    def get_from_storage(self, product_type: Type[ProductItem], qty: Optional[float] = None):
        if len(list(filter(lambda x: type(x) is product_type, self.storage))) == 0:
            raise exceptions.NoSuchProduct()
        if qty is not None:
            if list(filter(lambda x: type(x) is product_type, self.storage))[0].qty < qty:
                raise exceptions.InsufficientProductQty()
        
            p = list(filter(lambda x: type(x) is product_type, self.storage))[0]
            if p.qty == qty:
                self.storage.remove(p)
            else:
                p.qty -= qty

            return product_type(qty=qty)
        else:
            p = list(filter(lambda x: type(x) is product_type, self.storage))[0]
            self.storage.remove(p)
            return p

    def tick(self):
        for building in self.buildings:
            for creature in building.inventory[:]:
                try:
                    creature.tick()
                except exceptions.DeathDueBigAge:
                    if isinstance(creature, Animal):
                        print(f"{creature.name} умерла от старости.")
                    else:
                        print(f"{creature.name} засохла от старости.")
                    building.inventory.remove(creature)
                except exceptions.DeathFromUnfilledNeeds:
                    if isinstance(creature, Animal):
                        print(f"{creature.name} умерла от голода.")
                    else:
                        print(f"{creature.name} засохла без полива.")
                    building.inventory.remove(creature)


class Player:
    balance: float
    total_actions: int
    spent_actions: int = 0
    farm: Farm

    @property
    def available_actions(self):
        return self.total_actions - self.spent_actions

    def __init__(self, balance: float, total_actions: int, farm: Farm):
        self.balance = balance
        self.total_actions = total_actions
        self.farm = farm

    def _fill_the_creature_needs(self, target: Type[Creature], using: ProductItem):
        broke = False
        for building in self.farm.buildings:
            if broke:
                break
            for creature in building.inventory:
                if not issubclass(type(creature), target):
                    continue
                        
                creature.fill_the_needs(using)
                        
                if using.qty == 0:
                    broke = True
                    break
    
    @action
    def feed_animals(self):
        food: AnimalFood = self.farm.get_from_storage(AnimalFood)
        self._fill_the_creature_needs(Animal, food)
        if food.qty > 0:
            self.farm.place_in_storage(food)

    @action
    def pour_plants(self):
        water: Water = self.farm.get_from_storage(Water)
        self._fill_the_creature_needs(Plant, water)
        if water.qty > 0:
            self.farm.place_in_storage(water)

    @action
    def get_animal_products(self):
        for building in self.farm.buildings:
            for creature in building.inventory:
                if isinstance(creature, Animal):
                    self.farm.place_in_storage(creature.harvest_products())

    @action
    def harvest_plants(self):
        for building in self.farm.buildings:
            for creature in building.inventory:
                if isinstance(creature, Plant):
                    self.farm.place_in_storage(creature.harvest_products())

    @action
    def buy_product_item(self, product_type: Type[ProductItem], qty: float):
        if self.balance < product_type.buy_price * qty:
            raise exceptions.InsufficientFunds()
        self.balance -= product_type.buy_price * qty
        self.farm.place_in_storage(product_type(qty=qty))

    @action
    def sell_product_item(self, product_type: Type[ProductItem], qty: float):
        self.balance += product_type.buy_price * qty
        self.farm.get_from_storage(product_type, qty)

    @action
    def buy_creature(self, creature_type: Type[Creature], qty: int):
        if self.balance < creature_type.buy_price * qty:
            raise exceptions.InsufficientFunds()
        
        if qty > sum([x.slots_available for x in self.farm.buildings if creature_type in x.can_contain_types]):
            raise exceptions.NoMoreSpaceAvailable()
        
        c = 0
        for building in self.farm.buildings:
            if creature_type in building.can_contain_types:
                while building.slots_available > 0 and qty > c:
                    building.place_creature(creature_type())
                    c += 1
        self.balance -= creature_type.buy_price * qty

    @action
    def sell_creature(self, building: Building, creature: Creature):
        if creature.can_sell:
            self.balance += creature.sell_price
            building.inventory.remove(creature)
        else:
            raise exceptions.WrongAction()
    
    @action
    def buy_building(self, building_type: Type[Building]):
        if self.balance < building_type.buy_price:
            raise exceptions.InsufficientFunds() 
        self.farm.place_building(building_type)
        self.balance -= building_type.buy_price

    @action
    def upgrade_building(self, building: Building):
        if self.balance < building.upgrade_price:
            raise exceptions.InsufficientFunds()
        building.upgrade()
        self.balance -= building.upgrade_price


class Game:
    player: Player
    farm: Farm

    def __init__(self, start_balance: float, player_total_cations: int):
        self.farm = Farm(10, [Barn(), Field()], [Hen(), Wheat(), Wheat()], [AnimalFood(20), Water(25)])
        self.player = Player(balance=start_balance, total_actions=player_total_cations, farm=self.farm)

    def _print_status(self):
        print(f"Действий доступно: {self.player.available_actions}\nБаланс: {self.player.balance} денег\n{str(self.farm)}\n")

    def _ask_player(self, question: str, options: List[Option]):
        print(question)
        for option in options:
            print(option)
        answer = input('Выбор: ')
        if answer == '':
            return None
        
        selected_option = list(filter(lambda x: x.key == answer, options))
        if len(selected_option) == 0:
            return self._ask_player(question, options)
        else:
            return selected_option[0]
        
    @check_action_availability
    def _feed_animals(self):
        try:
            self.player.feed_animals()
            print("Вы покормили животных.")
        except exceptions.NoSuchProduct:
            print("Нет еды для животных на складе!")

    @check_action_availability
    def _pour_plants(self):
        try:
            self.player.pour_plants()
            print("Вы полили растения.")
        except exceptions.NoSuchProduct:
            print("Нет воды на складе!")

    @check_action_availability
    def _get_animal_products(self):
        self.player.get_animal_products()
        print("Вы собрали продукты животных.")

    @check_action_availability
    def _harvest_plants(self):
        self.player.harvest_plants()
        print("Вы собрали продукты растений.")

    @check_action_availability
    def _buy_creature(self):
        answer = self._ask_player("Растение или животное? [Enter, что бы вернуться]", [
            Option('1', 'Животное'),
            Option('2', 'Растение')
        ])
        if answer is None:
            return

        match answer.key:
            case '1':
                answer2 = self._ask_player("Какое животное вы бы хотели купить? [Enter, что бы вернуться]", [
                    Option('1', f"{Hen.name} - {Hen.buy_price} денег", handler_args=[Hen]),
                    Option('2', f"{Sheep.name} - {Sheep.buy_price} денег", handler_args=[Sheep]),
                    Option('3', f"{Cow.name} - {Cow.buy_price} денег", handler_args=[Cow])
                ])
            case '2':
                answer2 = self._ask_player("Какое животное вы бы хотели купить? [Enter, что бы вернуться]", [
                    Option('1', f"{Wheat.name} - {Wheat.buy_price} денег", handler_args=[Wheat]),
                    Option('2', f"{Corn.name} - {Corn.buy_price} денег", handler_args=[Corn]),
                    Option('3', f"{Potato.name} - {Potato.buy_price} денег", handler_args=[Potato])
                ])
            case _:
                return
        
        if answer2 is None:
            return
        
        try:
            self.player.buy_creature(answer2.handler_args[0], 1)
            print(f"Вы купили {answer2.handler_args[0].name}.")
        except exceptions.InsufficientFunds:
            print("Не хватает денег!")
        except exceptions.NoMoreSpaceAvailable:
            print("Нет места для животного!")

    def _sell_creature(self):
        options = []
        for building in self.farm.buildings:
            options.extend([{'b': building, 'c': x} for x in building.inventory if x.can_sell])
        
        answer = self._ask_player("Выберите животное, которое хотели бы продать. [Enter, что бы вернуться]", [
            Option(str(i+1), f"{x['c'].name} - {x['c'].sell_price} денег", handler_args=[x['b'], x['c']]) for i, x in enumerate(options)
        ])
        if answer is None:
            return
        
        self.player.sell_creature(answer.handler_args[0], answer.handler_args[1])
        print(f"Вы продали {answer.handler_args[1].name} за {answer.handler_args[1].sell_price}.")

    def _buy_products(self):
        answer = self._ask_player("Какой продукт вы бы хотели купить? [Enter, что бы вернуться]", [
            Option('1', f"{AnimalFood.name} - {AnimalFood.buy_price}/шт", handler_args=[AnimalFood]),
            Option('2', f"{Water.name} - {Water.buy_price}/шт", handler_args=[Water])
        ])
        if answer is None:
            return
        qty = float(input("Сколько? "))
        if qty < 0:
            print("А иди-ка ты лесом, друг...")
            exit()
        
        try:
            self.player.buy_product_item(answer.handler_args[0], qty)
            print(f"Вы купили {qty} {answer.handler_args[0].name}")
        except exceptions.InsufficientFunds:
            print("Недостаточно денег!")

    def _sell_products(self):
        answer = self._ask_player("Выберите продукт, который хотели бы продать. [Enter, что бы вернуться]", [
            Option(str(i+1), f"{x.name} - {x.qty} шт, {x.buy_price}/шт", handler_args=[x]) for i, x in enumerate(self.farm.storage)
        ])
        if answer is None:
            return
        qty = float(input("Сколько? "))
        if qty < 0:
            print("А иди-ка ты лесом, друг...")
            exit()

        try:
            self.player.sell_product_item(type(answer.handler_args[0]), qty)
            print(f"Вы продали {answer.handler_args[0].name} за {answer.handler_args[0].buy_price * qty}.")
        except exceptions.InsufficientProductQty:
            print("Вы пытаетесь продать больше, чем имеете!")

    def _upgrade_building(self):
        answer = self._ask_player("Какое здание будем улучшать? [Enter, что бы вернуться]", [
            Option(str(i+1), f"{str(x)} - {x.upgrade_price}", handler_args=[x]) for i, x in enumerate(self.farm.buildings)
        ])
        if answer is None:
            return
        
        try:
            self.player.upgrade_building(answer.handler_args[0])
            print(f"Вы улучшили {answer.handler_args[0].name}.")
        except exceptions.InsufficientFunds:
            print("Не хватает денег!")
        except exceptions.MaximumLevelReached:
            print("И так уже максимальный уровень!")

    def _buy_building(self):
        answer = self._ask_player("Какое здание будем покупать? [Enter, что бы вернуться]", [
            Option('1', f"{Barn.name} - {Barn.buy_price} денег", handler_args=[Barn]),
            Option('2', f"{Field.name} - {Field.buy_price} денег", handler_args=[Field]),
        ])
        if answer is None:
            return
        
        try:
            self.player.buy_building(answer.handler_args[0])
            print(f"Вы купили {answer.handler_args[0].name}.")
        except exceptions.InsufficientFunds:
            print("Не хватает денег!")
        except exceptions.NoMoreSpaceAvailable:
            print("Все уже застроено. Ставить некуда.")
    
    def _main_question(self):
        print('\n\n\n')
        self._print_status()
        answer = self._ask_player("Что бы вы хотели сделать? [Enter, что бы лечь спать] [ctrl-c для выхода]", [
            Option('1', 'Покормить животных', self._feed_animals),
            Option('2', 'Полить растения', self._pour_plants),
            Option('3', 'Собрать продукты животных', self._get_animal_products),
            Option('4', 'Собрать продукты растений', self._harvest_plants),
            Option('5', 'Купить животное/растение', self._buy_creature),
            Option('6', 'Продать животное', self._sell_creature),
            Option('7', 'Купить продукты', self._buy_products),
            Option('8', 'Продать продукты', self._sell_products),
            Option('9', 'Улучшить здание', self._upgrade_building),
            Option('0', 'Купить здание', self._buy_building)
        ])
        if answer is None:
            self.farm.tick()
            self.player.spent_actions = 0
            sleep(5)
            print("Вы поспали.")
        else:
            answer.handler()

    def main_cycle(self):
        print("Добро пожаловать в симулятор фермера!")
        try:
            while True:
                self._main_question()
        except KeyboardInterrupt:
            print("До свидания.")
            return

# endregion

# region Game Object Classes

#region Products

class AnimalFood(ProductItem):
    name = "Еда для животных"
    buy_price = 5.
    
    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class Water(ProductItem):
    name = "Вода"
    buy_price = 1.
    
    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class WheatSeed(ProductItem):
    name = "Семена пшеницы"
    buy_price = 5.

    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class CornSeed(ProductItem):
    name = "Семена кукурузы"
    buy_price = 6.

    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class Tuber(ProductItem):
    name = "Картофельный клубень"
    buy_price = 7.

    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class Egg(ProductItem):
    name = "Яйцо"
    buy_price = 25.
    
    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class Wool(ProductItem):
    name = "Шерсть"
    buy_price = 100.
    
    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty


class Milk(ProductItem):
    name = "Молоко"
    buy_price = 60.
    
    def __init__(self, qty: float):
        super().__init__()
        self.qty = qty

# endregion

# region Plants

class Wheat(Plant):
    name = "Пшеница"
    buy_price = 6.
    minimum_required_age_for_producing = 15
    maximum_allowed_age_for_producing = 25
    max_age = 26
    producing_per_day = 4
    max_product_amount = 12
    product = WheatSeed
    needs = Water
    needs_decreasing_per_day = 5

    def __init__(self) -> None:
        super().__init__()
        self.age = 0
        self.needs_level = 90
        self.inventory = WheatSeed(0)


class Corn(Plant):
    name = "Кукуруза"
    buy_price = 8.5
    minimum_required_age_for_producing = 15
    maximum_allowed_age_for_producing = 25
    max_age = 26
    producing_per_day = 6
    max_product_amount = 18
    product = CornSeed
    needs = Water
    needs_decreasing_per_day = 7

    def __init__(self) -> None:
        super().__init__()
        self.age = 0
        self.needs_level = 90
        self.inventory = CornSeed(0)


class Potato(Plant):
    name = "Картошка"
    buy_price = 11
    minimum_required_age_for_producing = 15
    maximum_allowed_age_for_producing = 25
    max_age = 26
    producing_per_day = 8
    max_product_amount = 24
    product = Tuber
    needs = Water
    needs_decreasing_per_day = 9

    def __init__(self) -> None:
        super().__init__()
        self.age = 0
        self.needs_level = 90
        self.inventory = Tuber(0)

# endregion

# region Animals

class Hen(Animal):
    name = "Курица"
    buy_price = 30
    minimum_required_age_for_producing = 5
    maximum_allowed_age_for_producing = 45
    max_age = 50
    producing_per_day = 2
    max_product_amount = 6
    product = Egg
    needs = AnimalFood
    needs_decreasing_per_day = 5

    def __init__(self) -> None:
        super().__init__()
        self.age = 3
        self.needs_level = 90
        self.inventory = Egg(0)


class Sheep(Animal):
    name = "Овца"
    buy_price = 50
    minimum_required_age_for_producing = 10
    maximum_allowed_age_for_producing = 75
    max_age = 80
    producing_per_day = 1
    max_product_amount = 3
    product = Wool
    needs = AnimalFood
    needs_decreasing_per_day = 15

    def __init__(self) -> None:
        super().__init__()
        self.age = 3
        self.needs_level = 90
        self.inventory = Wool(0)


class Cow(Animal):
    name = "Корова"
    buy_price = 150
    minimum_required_age_for_producing = 15
    maximum_allowed_age_for_producing = 95
    max_age = 100
    producing_per_day = 3
    max_product_amount = 3
    product = Milk
    needs = AnimalFood
    needs_decreasing_per_day = 25

    def __init__(self) -> None:
        super().__init__()
        self.age = 3
        self.needs_level = 90
        self.inventory = Milk(0)

# endregion

# region Buildings

class Field(Building):
    name = "Поле"
    buy_price = 1000
    max_lvl = 5
    _base_upgrade_price = 150
    _upgrade_price_coeff = 1.5
    slots = 16
    _slots_growth_with_lvl = 4
    can_contain_types = (Wheat, Corn, Potato)

    def __init__(self) -> None:
        super().__init__()
        self.lvl = 1
        self.inventory = []


class Barn(Building):
    name = "Амбар"
    buy_price = 600
    max_lvl = 5
    _base_upgrade_price = 250
    _upgrade_price_coeff = 2
    slots = 8
    _slots_growth_with_lvl = 4
    can_contain_types = (Hen, Sheep, Cow)

    def __init__(self) -> None:
        super().__init__()
        self.lvl = 1
        self.inventory = []

# endregion

# endregion