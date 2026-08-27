"""287. Find the Duplicate Number
Given an array of integers nums containing n + 1 integers where each integer is in the range [1, n] inclusive.

There is only one repeated number in nums, return this repeated number.

You must solve the problem without modifying the array nums and using only constant extra space.

 

Example 1:

Input: nums = [1,3,4,2,2]
Output: 2
Example 2:

Input: nums = [3,1,3,4,2]
Output: 3
Example 3:

Input: nums = [3,3,3,3,3]
Output: 3
 

Constraints:

1 <= n <= 105
nums.length == n + 1
1 <= nums[i] <= n
All the integers in nums appear only once except for precisely one integer which appears two or more times."""

"""Итога разбора - протестированы известные подходы к решению задачи и их JIT-compiled версии.
Самое элегантное решение - алгоритм Флойда с медленным и быстрым указателями для поиска цикла
в связанном списке за O(n) по времени, на практике Memory Bound из-за случайного адреса
следующего элемента в памяти, поэтому оно проигрывает асимптотически менее эфективному
решению с подсчетом бит.
"""
from typing import List
def findDuplicate_sort(nums: List[int]) -> int:
    # попробуем тривиальные решения которые нарушают ограничения задачи
    # отсортируем nums и тогда дубликат обнаруживается при nums[i]==nums[i+1]
    # нарушаем условия задачи, изменяем nums
    nums.sort()
    for i in range(len(nums)-1):
        if nums[i]==nums[i+1]:
            return nums[i]

def findDuplicate_set(nums: List[int]) -> int:
    # другое тривиально решение с hashset
    # нарушаем условия задачи по памяти O(n)>O(1)
    hs = set()
    for num in nums:
        if num in hs:
            return num
        hs.add(num)

def findDuplicate_bs(nums: List[int]) -> int:
    # так как nums[i]<=n 
    # и так как можем увидеть монотонно возрастающую последовательность count(nums<=i)>i
    # [1,2,3,4,5]->[0,1,2,3,4]  but [1,3,4,2,2]->[False,True,True,True,True]
    # используем binsearch по ответу
    # тогда сложность по времени O(nlogn) - в каждой bs-logn итерации проходим по n элементам списка
    # по памяти O(1)
    n = len(nums)
    l, r = 1, n-1
    def answ(i):
        return sum(1 for num in nums if num<=i)>i
    while l<r:
        mid = l+(r-l)//2
        if answ(mid):
            r=mid
        else:
            l=mid+1
    return l

def findDuplicate_floyd(nums: List[int]) -> int:
    # это лучшее решение O(n)+O(1)
    # несмотря на O(N), при случайном распределении списка
    # алгоритм страдает от Pointer Chasing (CPU Cache Misses)
    # так как обращается к памяти хаотично (random memory access)
    # алгоритм
    # пользуясь условием 1 <= nums[i] <= n, понимаем что значения списка также являются индексами
    # мы моделируем движение по индексам:
    # стартуем с 0, затем идём в nums[0], потом в nums[nums[0]] и т.д.
    # Дубликат приводит к тому, что два разных индекса указывают на один и тот же 
    # следующий индекс — возникает цикл
    # точка входа в цикл на расстоянии P от головы, цикл длинной C
    # используем два указателя для поиска цикла, slow=nums[slow] and fast=nums[nums[fast]]
    # тогда двигаясь по списку до fast будет в два раза опережать slow
    # а когда оба указателя будут внутри цикла, fast пройдя цикл один раз начнет догонять slow
    # со скоростью одного шага за итерацию, пока они не встретятся на каком то расстоянии x до конца цикла
    # теперь мы знаем что цикл есть, если бы цикла не было fast дошел бы до конца списка
    # путь пройденный сначала списка fast=2*slow (1)
    # slow = P+C-x, fast=P+C+C-x (2) => подставим 2 в 1 => 2*(P+C-x)=P+C+C-x => P=x
    # значит расстояние сначала списка до точки входа в чикл равно расстоянию от точки встречи до точки входа
    # чтобы найти точку входа пройдем двумя медленными указателями - от начала списка
    # и от точки встречи, пока указатели не встретятся в точке входа
    
    slow, fast = nums[0],nums[0]
    while True:
        slow=nums[slow]        
        fast=nums[nums[fast]]
        if slow==fast:
            break

    slow2=nums[0]
    while slow!=slow2:
        slow=nums[slow]
        slow2=nums[slow2]

    return slow

def findDuplicate_sign(nums: List[int]) -> int:
    # как и в Флойде используем значения nums как индексы 
    # используя nums как связанный список
    # двигаемся по списку и меняем знак 
    # дубликат образует цикл и мы увидим отрицательное значение, значит мы уже здесь были
    # вторым циклом возвращаем nums в исходное состояние 
    # решение спорное так как иммутабельность nums временно нарушается
    # поэтому это thread-unsafe решение
    # также как Флойд алгоритм страдает от Pointer Chasing (CPU Cache Misses)
    # и вызывает аллокацию N PyObject
    pos=0
    while True:
        if nums[pos]<0:
            duplicate=pos
            break
        nums[pos]=-nums[pos]
        pos = -nums[pos]
    pos2=0
    while nums[pos2]<0:
        nums[pos2]=-nums[pos2]
        pos2=nums[pos2]
    return duplicate

def findDuplicate_bit(nums: List[int]) -> int:
    # считаем биты в списке и пользуемся разницей числа бит в списке без дубликатов
    # дубликат восстанавливаеваем побитово из разницы числа бит
    # 0->0, 1+->1
    # time O(Nlog M): M=N, space O(1)
    n = len(nums) - 1
    duplicate = 0
    max_bit = n.bit_length()
    
    for bit in range(max_bit):
        mask = 1 << bit
        count_nums = 0

        # в списке без дубликатов
        # аналитический подсчет count_base за O(1)
        # можно считать проще - итеративно, добавив условие в цикл ниже
        period = 1 << (bit + 1)       # 2^(bit+1)
        half_period = 1 << bit        # 2^bit
        
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)
        
        # считаем биты в списке nums - итеративный подсчет
        for num in nums:
            if num & mask:
                count_nums += 1
            # можно предложить вариант без ветвления count_nums += (num >> bit) & 1
            # но в CPython if будет быстрее так как скипается дорогое сложение 
            # дорогой в создании PyObject структур - (num >> bit), (& 1), (count_nums +=)
            # в C/С++ вариант без ветвления был бы быстрее - нет сброса конвейера CPU 
                
        # сравниваем
        if count_nums > count_base:
            duplicate |= mask
            
    return duplicate

def findDuplicate_bit_optimal(nums: List[int]) -> int:
    n = len(nums) - 1
    max_bit = n.bit_length()
    
    # Массив из max_bit (ceil(log2(n))=24 для n=10**7) элементов для хранения счетчиков единиц. 
    # max_bit int'ов - это истинное O(1) space.
    count_nums = [0] * max_bit 
    
    for num in nums:
        temp = num
        # Применяем инкрементный сдвиг
        for bit in range(max_bit):
            count_nums[bit] += temp & 1
            temp >>= 1  # In-place сдвиг на 1 без дорогих вычислений!
            if temp == 0:
                break # Ранняя остановка, если биты закончились
                
    # Теперь у нас есть все count_nums. 
    # Считаем эталонные count_base и собираем дубликат
    duplicate = 0
    for bit in range(max_bit):
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)
        
        if count_nums[bit] > count_base:
            duplicate |= (1 << bit)
            
    return duplicate

def findDuplicate_bit_numpy(nums: List[int]) -> int:
    # векторизуем подсчет бит через numpy и избавимся от внутреннего цикла
    # преимущество только при n>10^6
    # по памяти O(n) поэтому это плохое решение, 
    # но работает быстрее так нет PyObject и меньше циклов
    # считаем биты в списке и пользуемся разницей числа бит в списке без дубликатов
    # дубликат восстанавливаеваем побитово из разницы числа бит
    # 0->0, 1+->1
    import numpy as np
    n = len(nums) - 1
    duplicate = 0
    max_bit = n.bit_length()
    arr = np.array(nums, dtype=np.uint32)
    
    for bit in range(max_bit):
        mask = 1 << bit
        count_nums = 0

        # в списке без дубликатов
        # аналитический подсчет count_base за O(1)
        # можно считать проще - итеративно, добавив условие в цикл ниже
        period = 1 << (bit + 1)       # 2^(bit+1)
        half_period = 1 << bit        # 2^bit
        
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)
        
        # считаем биты в списке nums - векоризованный подсчет
        # так как numpy выполняет C++ код
        # нет штрафа CPython - числа лежат компактно в непрерывном блоке памяти
        # это дает кэш-локальность и позволяет CPU cache prefetcher
        # уходим от ветвления count_nums += (num >> bit) & 1
        # и векторизуем count_nums = np.sum((arr >> bit) & 1)
        # получаем бенефиты SIMD, битовый сдвиг
        count_nums = np.sum((arr >> bit) & 1)
                
        # сравниваем
        if count_nums > count_base:
            duplicate |= mask
            
    return duplicate
import numpy as np

def findDuplicate_bit_numpy_full(nums: list[int]) -> int:
    arr = np.array(nums, dtype=np.int32)
    n = len(arr) - 1
    max_bit = n.bit_length()
    
    # Создаем вектор индексов битов: [0, 1, 2, ..., max_bit-1]
    bits = np.arange(max_bit, dtype=np.int32)
    
    # 1. Аналитический подсчет count_base для ВСЕХ битов сразу (Векторная операция)
    period = 1 << (bits + 1)
    half_period = 1 << bits
    full_cycles = (n + 1) // period
    remainder = (n + 1) % period
    count_base = (full_cycles * half_period) + np.maximum(0, remainder - half_period)
    
    # 2. Векторизация по обоим измерениям (Broadcasting)
    # arr[:, None] превращает массив в столбец (N, 1)
    # bits остается строкой (1, max_bit)
    # Операция >> неявно разворачивает их в 2D-матрицу размером (N, max_bit)
    
    bit_matrix = (arr[:, None] >> bits) & 1
    
    # Складываем по оси 0 (по столбцам), получая вектор длиной max_bit
    count_nums = np.sum(bit_matrix, axis=0)
    
    # 3. Сравниваем два вектора (результат - массив булевых значений)
    diff = count_nums > count_base
    
    # 4. Восстанавливаем число из битов (Умножаем True/False на степени двойки)
    duplicate = np.sum(diff * (1 << bits))
    
    return int(duplicate)

import numpy as np
from numba import njit

# Декоратор @njit (No-Python JIT) отключает виртуальную машину CPython 
# и компилирует функцию в нативный машинный код
@njit
def findDuplicate_bit_numba(arr: np.ndarray) -> int:
    n = len(arr) - 1
    duplicate = 0
    
    # Вычисляем max_bit вручную, как в C
    temp = n
    max_bit = 0
    while temp > 0:
        max_bit += 1
        temp >>= 1
        
    for bit in range(max_bit):
        mask = 1 << bit
        
        # 1. Аналитический подсчет эталона O(1)
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)
        
        # 2. Низкоуровневый JIT-цикл
        count_nums = 0
        for i in range(len(arr)):
            # Branchless сложение. 
            # Здесь не создаются массивы или PyObject. 
            # arr[i] читается напрямую из памяти C-массива в регистр процессора.
            count_nums += (arr[i] >> bit) & 1
            
        # 3. Сравниваем
        if count_nums > count_base:
            duplicate |= mask
            
    return duplicate

@njit(parallel=True)
def findDuplicate_bit_numba_prange(nums):
    n = len(nums) - 1
    
    # 1. Находим количество бит (log M)
    max_num = n
    max_bit = 0
    while max_num > 0:
        max_bit += 1
        max_num >>= 1
        
    duplicate = 0
    
    # 2. prange распределит итерации этого цикла между логическими ядрами.
    # На 27 битах и 12 потоках, каждый поток проверит по 2-3 бита.
    for bit in prange(max_bit):
        mask = 1 << bit
        base_count = 0
        nums_count = 0
        
        # 3. Вложенный цикл: каждый поток независимо читает массив.
        # Аппаратные Prefetcher'ы ядер начнут соревноваться за пропускную способность.
        for i in range(len(nums)):
            if (nums[i] & mask) != 0:
                nums_count += 1
            if i > 0 and (i & mask) != 0:
                base_count += 1
                
        # 4. Редукция (Reduction)
        if nums_count > base_count:
            # Важный хак: вместо побитового ИЛИ (|=) мы используем сложение (+=).
            # Поскольку степени двойки никогда не пересекаются (у них разные биты),
            # += дает тот же результат. Numba умеет автоматически делать 
            # безопасную многопоточную редукцию для оператора +=.
            duplicate += mask
            
    return duplicate

@njit
def findDuplicate_bit_optimal_numba(arr: np.ndarray) -> int:
    n = len(arr) - 1
    
    # 1. Вычисляем max_bit вручную (так как int.bit_length() может не поддерживаться в старых версиях Numba)
    temp_n = n
    max_bit = 0
    while temp_n > 0:
        max_bit += 1
        temp_n >>= 1
        
    # Создаем массив счетчиков. 
    # В Numba это аллоцирует крошечный С-массив на 17-24 элемента, 
    # который гарантированно останется в самом быстром кэше L1.
    count_nums = np.zeros(max_bit, dtype=np.int32)
    
    # 2. ЕДИНСТВЕННЫЙ ПРОХОД ПО ПАМЯТИ (Идеальная кэш-локальность)
    for i in range(len(arr)):
        temp = arr[i]
        
        for bit in range(max_bit):
            count_nums[bit] += temp & 1
            temp >>= 1
            
    # 3. Аналитический подсчет эталона и восстановление дубликата
    duplicate = 0
    for bit in range(max_bit):
        period = 1 << (bit + 1)
        half_period = 1 << bit
        full_cycles = (n + 1) // period
        remainder = (n + 1) % period
        
        # Numba поддерживает встроенную функцию max
        count_base = (full_cycles * half_period) + max(0, remainder - half_period)
        
        if count_nums[bit] > count_base:
            duplicate |= (1 << bit)
            
    return duplicate

import numpy as np
from numba import njit, prange

@njit
def findDuplicate_floyd_numba(arr: np.ndarray) -> int:
    slow = arr[0]
    fast = arr[0]
    
    # Ищем пересечение (цикл)
    while True:
        slow = arr[slow]
        fast = arr[arr[fast]]
        if slow == fast:
            break
            
    # Ищем точку входа в цикл
    slow2 = arr[0]
    while slow != slow2:
        slow = arr[slow]
        slow2 = arr[slow2]
        
    return slow

tests = [([1,3,4,2,2], 2),
         ([1,2,3,4,3], 3),
         ([3,3,3,3,3], 3),
         (list(range(1, 10**7))+[10**7-1], 10**7-1)]

import time
import math
import time
import random
import numpy as np
import mmap
from hugepage import allocate_hugepage_array


if __name__ == '__main__':

    # Собираем все функции
    functions = [
        findDuplicate_bit,
        findDuplicate_bs,
        findDuplicate_bit_optimal,
        findDuplicate_sort,
        findDuplicate_floyd,
        findDuplicate_sign,
        findDuplicate_set,
        findDuplicate_floyd_numba,
        findDuplicate_bit_numpy_full,
        findDuplicate_bit_numpy,
        findDuplicate_bit_optimal_numba,
        findDuplicate_bit_numba,
        findDuplicate_bit_numba_prange
    ]
    # 1. Основные тесты на корректность
    tests = [
        ([1, 3, 4, 2, 2], 2),
        ([1, 2, 3, 4, 3], 3),
        ([3, 3, 3, 3, 3], 3)
    ]

    print("--- ЗАПУСК ТЕСТОВ НА КОРРЕКТНОСТЬ ---")
    for func in functions:
        func_name = func.__name__
        try:
            for test_arr, expected in tests:
                result = func(test_arr.copy())
                assert result == expected, f"Expected {expected}, got {result}"
            print(f"✅ {func_name:<32} | Все тесты пройдены")
        except Exception as e:
            print(f"❌ {func_name:<32} | ОШИБКА: {e}")

    # 3. БЕНЧМАРК НА РАЗНЫХ N
    # N=10 выступает в роли неявного прогрева (warmup)
    Ns = [10, 10**5, 10**6, 10**7,10**8]
    results = {func.__name__: [] for func in functions}

    # Флаг для включения/выключения HugePages
    USE_HUGEPAGES = True 
    
    print("\n--- ЗАПУСК МАСШТАБИРУЕМОГО БЕНЧМАРКА ---")
    for N in Ns:
        print(f"⏳ Генерация и перемешивание массива N = {N}...")
        test_arr = list(range(1, N + 1)) + [N]
        random.shuffle(test_arr)
        expected_dup = N

        for func in functions:
            func_name = func.__name__
            raw_buffer = None # Инициализируем ссылку на mmap буфер
            
            # --- ПОДГОТОВКА ДАННЫХ ---
            if "numba" in func_name or "numpy" in func_name:
                if USE_HUGEPAGES:
                    try:
                        # Запрашиваем физические 2MB-страницы
                        data, raw_buffer = allocate_hugepage_array(len(test_arr), dtype=np.int32)
                        # Копируем данные в выделенную память (не входит в замер времени)
                        data[:] = test_arr 
                    except RuntimeError as e:
                        print(f"\n[!] ОШИБКА: {e}")
                        print("[!] Сбрасываем флаг USE_HUGEPAGES в False и продолжаем...")
                        USE_HUGEPAGES = False
                        data = np.array(test_arr, dtype=np.int32)
                else:
                    data = np.array(test_arr, dtype=np.int32)
            else:
                data = test_arr.copy()

            # input(f'Press enter to start benchmark of {func_name}')

            # --- ЗАМЕР ВРЕМЕНИ ---
            start_time = time.perf_counter()
            try:
                res = func(data)
                elapsed = (time.perf_counter() - start_time) * 1000
                if res != expected_dup:
                    elapsed = -1.0 
            except Exception as e:
                elapsed = -1.0
            finally:
                # --- ГАРАНТИРОВАННАЯ ОЧИСТКА АППАРАТНОЙ ПАМЯТИ ---
                if raw_buffer is not None:
                    raw_buffer.close()
                
            results[func_name].append((N, elapsed))

    # 4. РЕНДЕР СВОДНОЙ ТАБЛИЦЫ С ПОДСВЕТКОЙ
    print("\n" + "="*102)
    
    # Формируем динамический заголовок
    headers = f"{'Алгоритм':<32} |"
    for N in Ns:
        eng_N = f"10^{int(math.log10(N))}"
        headers += f" N={eng_N:<12} |"
    print(headers)
    print("-" * 102)
    
    # Шаг 1: Находим лучшее (минимальное) время для каждой колонки N
    best_times = {}
    for N in Ns:
        valid_times = []
        for func in functions:
            # Ищем время текущей функции для текущего N
            t = next((val for n, val in results[func.__name__] if n == N), -1)
            if t >= 0:
                valid_times.append(t)
        
        # Если есть успешные замеры, сохраняем минимум
        best_times[N] = min(valid_times) if valid_times else -1

    # Шаг 2: Сортируем функции по времени на самом большом N (для наглядности)
    max_N = max(Ns)
    def get_sort_key(func):
        t = next((val for n, val in results[func.__name__] if n == max_N), -1)
        return t if t >= 0 else float('inf')
        
    sorted_functions = sorted(functions, key=get_sort_key)

    # Шаг 3: Выводим строки таблицы
    for func in sorted_functions:
        func_name = func.__name__
        row_str = f"{func_name:<32} |"
        
        for N in Ns:
            time_val = next((t for n, t in results[func_name] if n == N), -1)
            
            if time_val < 0:
                row_str += f" {'ERROR':>14} |"
            else:
                # \033[1;32m = жирный зеленый, \033[0m = сброс
                is_best = (time_val == best_times[N])
                formatted_time = f"{time_val:>11.2f} ms"
                
                if is_best:
                    row_str += f" \033[1;32m{formatted_time}\033[0m |"
                else:
                    row_str += f" {formatted_time} |"
                    
        print(row_str)
    print("="*102)
"""RESULTS
########################single core NUMBA_NUM_THREADS=2 -c 0-1 is 2 virtual and 1 physical core###################
bench NUMBA_NUM_THREADS=2 setarch x86_64 -R taskset -c 0-1 python3 ../287.py
======================================================================================================
Алгоритм                         | N=10^1         | N=10^5         | N=10^6         | N=10^7         | N=10^8         |
------------------------------------------------------------------------------------------------------
findDuplicate_bit_numba_prange   |      405.58 ms |        0.24 ms |        2.68 ms |       34.86 ms |      397.07 ms |
findDuplicate_bit_numba          |      102.93 ms |        0.13 ms |        1.58 ms |       36.70 ms |      399.84 ms |
findDuplicate_bit_optimal_numba  |      121.49 ms |        0.43 ms |        4.99 ms |       47.87 ms |      586.14 ms |
findDuplicate_bit_numpy          |        0.09 ms |        1.06 ms |        8.64 ms |      296.05 ms |     3205.19 ms |
findDuplicate_bit_numpy_full     |        0.07 ms |        5.23 ms |       54.35 ms |      593.59 ms |     7137.50 ms |
findDuplicate_floyd_numba        |       54.82 ms |        0.54 ms |       14.41 ms |     1842.85 ms |    16159.39 ms |
findDuplicate_set                |        0.00 ms |        3.83 ms |      187.54 ms |     2052.86 ms |    18390.81 ms |
findDuplicate_sign               |        0.00 ms |        6.76 ms |      209.55 ms |     4045.77 ms |    46038.12 ms |
findDuplicate_sort               |        0.00 ms |       15.05 ms |      241.75 ms |     3432.98 ms |    48021.09 ms |
findDuplicate_floyd              |        0.00 ms |        5.59 ms |      234.26 ms |     8132.65 ms |    63194.64 ms |
findDuplicate_bit_optimal        |        0.01 ms |      160.83 ms |     2010.87 ms |    23329.37 ms |   273459.56 ms |
findDuplicate_bs                 |        0.01 ms |       51.41 ms |     2029.83 ms |    29515.85 ms |   387643.12 ms |
findDuplicate_bit                |        0.01 ms |       69.18 ms |     2337.61 ms |    32525.89 ms |   451671.40 ms |
======================================================================================================

##################################################### 2 physical cores############################################
 NUMBA_NUM_THREADS=2 setarch x86_64 -R taskset -c 0,2 python3 ../287.py
======================================================================================================
Алгоритм                         | N=10^1         | N=10^5         | N=10^6         | N=10^7         | N=10^8         |
------------------------------------------------------------------------------------------------------
findDuplicate_bit_numba_prange   |      409.59 ms |        0.18 ms |        1.79 ms |       22.19 ms |      283.18 ms |
findDuplicate_bit_numba          |      102.12 ms |        0.14 ms |        1.52 ms |       35.84 ms |      461.19 ms |
findDuplicate_bit_optimal_numba  |      121.82 ms |        0.39 ms |        4.97 ms |       47.98 ms |      582.07 ms |
findDuplicate_bit_numpy          |        0.09 ms |        1.08 ms |        8.42 ms |      307.69 ms |     3284.49 ms |
findDuplicate_bit_numpy_full     |        0.06 ms |        7.63 ms |       71.13 ms |      702.85 ms |     6832.24 ms |
findDuplicate_floyd_numba        |       54.69 ms |        0.52 ms |       16.76 ms |      487.78 ms |     9641.80 ms |
findDuplicate_sign               |        0.00 ms |        8.17 ms |      287.10 ms |     1723.87 ms |    30155.70 ms |
findDuplicate_set                |        0.00 ms |        4.65 ms |      200.65 ms |     1783.58 ms |    35379.20 ms |
findDuplicate_floyd              |        0.00 ms |        5.48 ms |      286.83 ms |     2075.08 ms |    37542.17 ms |
findDuplicate_sort               |        0.00 ms |       15.17 ms |      242.08 ms |     3440.07 ms |    48034.46 ms |
findDuplicate_bit_optimal        |        0.01 ms |      164.31 ms |     2076.29 ms |    23097.77 ms |   278587.46 ms |
findDuplicate_bs                 |        0.01 ms |       51.62 ms |     2072.07 ms |    29742.82 ms |   392198.56 ms |
findDuplicate_bit                |        0.01 ms |       71.84 ms |     2472.80 ms |    32825.97 ms |   432564.35 ms |
======================================================================================================

##################################################### 4 physical cores############################################
 bench NUMBA_NUM_THREADS=4 setarch x86_64 -R taskset -c 0,2,4,6 python3 ../287.py
 ======================================================================================================
Алгоритм                         | N=10^1         | N=10^5         | N=10^6         | N=10^7         | N=10^8         |
------------------------------------------------------------------------------------------------------
findDuplicate_bit_numba_prange   |      417.01 ms |        0.12 ms |        1.22 ms |       13.76 ms |      145.76 ms |
findDuplicate_bit_numba          |      104.69 ms |        0.12 ms |        1.53 ms |       38.75 ms |      396.50 ms |
findDuplicate_bit_optimal_numba  |      122.70 ms |        0.40 ms |        5.01 ms |       48.48 ms |      614.96 ms |
findDuplicate_bit_numpy          |        0.11 ms |        1.10 ms |        9.60 ms |      306.01 ms |     3037.21 ms |
findDuplicate_bit_numpy_full     |        0.07 ms |        5.84 ms |       68.00 ms |      622.79 ms |     7769.43 ms |
findDuplicate_floyd_numba        |       57.75 ms |        0.25 ms |       17.04 ms |     1458.94 ms |    11238.88 ms |
findDuplicate_set                |        0.00 ms |        8.62 ms |      102.34 ms |     1001.56 ms |    20071.61 ms |
findDuplicate_sign               |        0.00 ms |        5.13 ms |      267.55 ms |     3707.38 ms |    32768.44 ms |
findDuplicate_floyd              |        0.00 ms |        2.51 ms |      279.94 ms |     6351.21 ms |    44408.30 ms |
findDuplicate_sort               |        0.00 ms |       15.53 ms |      244.38 ms |     3486.28 ms |    48466.09 ms |
findDuplicate_bit_optimal        |        0.01 ms |      154.16 ms |     1898.27 ms |    21469.95 ms |   262193.63 ms |
findDuplicate_bs                 |        0.01 ms |       51.93 ms |     2137.68 ms |    29834.45 ms |   425675.07 ms |
findDuplicate_bit                |        0.01 ms |       69.42 ms |     2431.49 ms |    33036.73 ms |   455739.76 ms |
======================================================================================================

##################################################### 5 physical cores############################################
`➜ bench NUMBA_NUM_THREADS=5 setarch x86_64 -R taskset -c 0,2,4,6,8 python3 ../287.py`

| **Algorithm**                    | **N=10^1** | **N=10^5** | **N=10^6** | **N=10^7** | **N=10^8** |
| -------------------------------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| `findDuplicate_bit_numba_prange` | 419.89 ms  | 3.16 ms    | 0.89 ms    | 10.54 ms   | 116.62 ms  |

 """
