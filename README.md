# SpectrumGrapher
Построитель спектрограм на базе показаний устройств Arinst

## Установка
1. Клонируем репозиторий
```
git clone https://github.com/Ydrec/SpectrumGrapher.git
```
3. Устанавливаем необходимые библиотеки Python
```
cd SpectrumGrapher
pip install -r requirements.txt
```

## Запуск приложения
```
python main.py --start [начальная частота сканирвоания] --stop [конечная частота сканирования] --step [шаг сканирования]
или
python main.py --file [путь к файлу лога для чтения]
```

## Управление
`q` - Выход
