# Симулятор фермера
## Lore

### Ресурсы
В игре необходимо покупать воду и еду для животных. Они используются для полива растений и кормления животных, соответственно.

> Все остальные ресурсы можно только продавать. Семена нельзя сажать, что бы выросло растение. Из яйца нельзя получить цыпленка.

| Название         | Стоимость    |
|------------------|--------------|
| Вода             | 1 денег/шт   |
| Еда для животных | 5 денег/шт   |
| Семена пшеницы   | 5 денег/шт   |
| Семена кукурузы  | 6 денег/шт   |
| Клубни картофеля | 7 денег/шт   |
| Яйцо             | 25 денег/шт  |
| Шерсть           | 100 денег/шт |
| Молоко           | 60 денег/шт  |

### Существа
#### Животные
1. Курица. Стоимость: 30 денег.
    - Производит 2 яйца в день, ест 5 еды для животных в день.
    - Живет 50 дней, несет яйца с 5-го по 45-й дни.
2. Овца. Стоимость: 50 денег.
    - Производит 1 ед. шерсти в день, ест 15 еды для животных в день.
    - Живет 80 дней, производит шерсть с 10-го по 75-й дни.
3. Корова. Стоимость: 150 денег.
    - Производит 3 ед. молока в день, есть 25 еды для животных в день.
    - Живет 100 дней, производит молоко с 15-го по 95-й дни.

#### Растения
1. Пшеница. Стоимость: 6 денег.
    - Производит 4 семени пшеницы в день, потребляет 5 ед. воды в день.
    - Живет 26 дней, производит семена пшеницы с 15-го по 25-й день.
2. Кукуруза. Стоимость: 8,5 денег.
    - Производит 6 семян кукурузы в день, потребляет 7 ед. воды в день.
    - Живет 26 дней, производит семена кукурузы с 15-го по 25-й день.
3. Картофель. Стоимость: 11 денег.
    - Производит 8 клубней картофеля в день, потребляет 9 ед. воды в день.
    - Живет 26 дней, производит клубни картофеля с 15-го по 25-й день.

> Можно продать животное. Растение - нет.

### Постройки
1. Поле. Стоимость: 1000 денег.
    - Имеет 16 мест для посева.
    - Имеет 5 уровней улучшения. Каждый уровень дает +4 места для посева.
    - Может размещать Пшеницу, Кукурузу, Картошку.
2. Амбар. Стоимость: 600 денег.
    - Имеет 8 мест для животных.
    - Имеет 5 уровней улучшения. Каждый уровень дает +4 места для животного.
    - Может размещать Курицу, Овцу, Корову.

> Каждое существо занимает 1 слот в постройке.

## Запуск
`python -m simulator`
