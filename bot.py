import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = '8171409133:AAGUJPwOOR-BMmodxHxrDwaV9A74ehvDQSY'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ЛОКАЛИЗАЦИЯ ---
TEXTS = {
    'ru': {
        'welcome': "Калькулятор выбросов CO₂\nЯ помогу рассчитать углеродный след вашего автомобиля.",
        'select_fuel': "Выберите тип двигателя:",
        'benzin': "Бензин",
        'diesel': "Дизель",
        'hybrid': "Гибрид",
        'electric': "Электромобиль",
        'select_method': "Как рассчитать выбросы?",
        'method_consumption': "Ввести расход топлива",
        'method_class': "Выбрать класс авто",
        'enter_consumption': "Введите средний расход топлива (л/100км):\nПример: 8.5 или 12",
        'select_class': "Выберите класс автомобиля:",
        'enter_mileage': "Введите пробег (км):",
        'electric_region': "🌍 Выбор региона для электромобиля",
        'electric_region_desc': "Интенсивность выбросов CO₂ зависит от энергомикса региона.\nВыберите, где вы чаще всего заряжаете автомобиль:",
        'result_header': "📊 РЕЗУЛЬТАТЫ РАСЧЕТА",
        'eco_tips': "💡 РЕКОМЕНДАЦИИ:",
        'new_calc': "🔄 Новый расчет: /start",
        'error_number': "❌ Введите число",
        'error_positive': "❌ Число должно быть больше 0",
        'cancel': "❌ Расчет отменен",
        'help_text': "Помощь по боту:\n/start - начать расчет\n/cancel - отменить расчет\n/help - эта справка",
        'fuel_selected': "Выбрано:",
        'class_selected': "Класс:",
        'region_selected': "Выбрано:",
        'co2_factor': "Коэффициент:",
        'mileage': "Пробег:",
        'emissions': "Выбросы CO₂:",
        'consumption': "Расход:",
        'electric_consumption': "Потребление:",
        'compensation': "Для компенсации потребуется",
        'trees_per_year': "деревьев в год",
        'tree_info': "(1 дерево поглощает ~20 кг CO₂ в год)",
        'region': "Регион:",
        'eco_equivalent': "🌍 ЭКО-ЭКВИВАЛЕНТ:",
        'separator': "─" * 30,
        'description': "📝",
        'select_region': "Выберите регион:",
        'co2_per_kwh': "г CO₂/кВт·ч",
    },
    'en': {
        'welcome': "CO₂ Emissions Calculator\nI'll help calculate your car's carbon footprint.",
        'select_fuel': "Select engine type:",
        'benzin': "Gasoline",
        'diesel': "Diesel",
        'hybrid': "Hybrid",
        'electric': "Electric",
        'select_method': "How to calculate emissions?",
        'method_consumption': "Enter fuel consumption",
        'method_class': "Select car class",
        'enter_consumption': "Enter average fuel consumption (L/100km):\nExample: 8.5 or 12",
        'select_class': "Select car class:",
        'enter_mileage': "Enter mileage (km):",
        'electric_region': "🌍 Region selection for electric car",
        'electric_region_desc': "CO₂ emission intensity depends on the region's energy mix.\nSelect where you most often charge your car:",
        'result_header': "📊 CALCULATION RESULTS",
        'eco_tips': "RECOMMENDATIONS:",
        'new_calc': "🔄 New calculation: /start",
        'error_number': "❌ Enter a number",
        'error_positive': "❌ Number must be greater than 0",
        'cancel': "❌ Calculation cancelled",
        'help_text': "Bot help:\n/start - start calculation\n/cancel - cancel calculation\n/help - this help",
        'fuel_selected': "Selected:",
        'class_selected': "Class:",
        'region_selected': "Selected:",
        'co2_factor': "Factor:",
        'mileage': "Mileage:",
        'emissions': "CO₂ emissions:",
        'consumption': "Consumption:",
        'electric_consumption': "Consumption:",
        'compensation': "To compensate, you need",
        'trees_per_year': "trees per year",
        'tree_info': "(1 tree absorbs ~20 kg CO₂ per year)",
        'region': "Region:",
        'eco_equivalent': "🌍 ECO EQUIVALENT:",
        'separator': "-" * 30,
        'description': "📝",
        'select_region': "Select region:",
        'co2_per_kwh': "g CO₂/kWh",
    }
}

def t(key, lang='ru'):
    """Получение локализованного текста"""
    return TEXTS.get(lang, TEXTS['ru']).get(key, key)

# --- РЕГИОНЫ ДЛЯ ЭЛЕКТРОМОБИЛЕЙ ---
ENERGY_REGIONS = {
    'scandinavia': {
        'name_ru': "🇳🇴 Скандинавия",
        'name_en': "🇳🇴 Scandinavia",
        'co2_factor': 0.03,
        'description_ru': "Гидроэнергетика",
        'description_en': "Hydroelectric power",
        'flag': "🇳🇴"
    },
    'eu_north': {
        'name_ru': "🇩🇪 Северная Европа",
        'name_en': "🇩🇪 Northern Europe",
        'co2_factor': 0.40,
        'description_ru': "Смесь ВИЭ и угля",
        'description_en': "Mix of renewables and coal",
        'flag': "🇩🇪"
    },
    'eu_west': {
        'name_ru': "🇫🇷 Западная Европа",
        'name_en': "🇫🇷 Western Europe",
        'co2_factor': 0.15,
        'description_ru': "Атомная энергетика и ВИЭ",
        'description_en': "Nuclear and renewables",
        'flag': "🇫🇷"
    },
    'eu_south': {
        'name_ru': "🇪🇸 Южная Европа",
        'name_en': "🇪🇸 Southern Europe",
        'co2_factor': 0.25,
        'description_ru': "Газовая генерация и солнце",
        'description_en': "Gas and solar",
        'flag': "🇪🇸"
    },
    'asia_china': {
        'name_ru': "🇨🇳 Китай",
        'name_en': "🇨🇳 China",
        'co2_factor': 0.58,
        'description_ru': "Угольные электростанции",
        'description_en': "Coal power plants",
        'flag': "🇨🇳"
    },
    'asia_japan': {
        'name_ru': "🇯🇵 Япония, Южная Корея",
        'name_en': "🇯🇵 Japan, South Korea",
        'co2_factor': 0.45,
        'description_ru': "Газ и импортная энергия",
        'description_en': "Gas and imported energy",
        'flag': "🇯🇵"
    },
    'asia_south': {
        'name_ru': "🇮🇳 Южная Азия",
        'name_en': "🇮🇳 South Asia",
        'co2_factor': 0.65,
        'description_ru': "Уголь и развивающаяся энергосистема",
        'description_en': "Coal and developing grid",
        'flag': "🇮🇳"
    },
    'usa_canada': {
        'name_ru': "🇺🇸 США и Канада",
        'name_en': "🇺🇸 USA and Canada",
        'co2_factor': 0.42,
        'description_ru': "Смешанная генерация (газ, уголь, ВИЭ)",
        'description_en': "Mixed generation (gas, coal, renewables)",
        'flag': "🇺🇸"
    },
    'latin_america': {
        'name_ru': "🇧🇷 Латинская Америка",
        'name_en': "🇧🇷 Latin America",
        'co2_factor': 0.20,
        'description_ru': "Гидроэнергетика и газ",
        'description_en': "Hydro and gas",
        'flag': "🇧🇷"
    },
    'cis_russia': {
        'name_ru': "🇷🇺 Россия и СНГ",
        'name_en': "🇷🇺 Russia and CIS",
        'co2_factor': 0.35,
        'description_ru': "Газовая, атомная и гидроэнергетика",
        'description_en': "Gas, nuclear and hydro",
        'flag': "🇷🇺"
    },
    'eastern_europe': {
        'name_ru': "🇺🇦 Восточная Европа",
        'name_en': "🇺🇦 Eastern Europe",
        'co2_factor': 0.38,
        'description_ru': "Уголь и атомная энергетика",
        'description_en': "Coal and nuclear",
        'flag': "🇺🇦"
    },
    'middle_east': {
        'name_ru': "🇸🇦 Ближний Восток",
        'name_en': "🇸🇦 Middle East",
        'co2_factor': 0.55,
        'description_ru': "Газовая и нефтяная генерация",
        'description_en': "Gas and oil generation",
        'flag': "🇸🇦"
    },
    'africa': {
        'name_ru': "🌍 Африка",
        'name_en': "🌍 Africa",
        'co2_factor': 0.50,
        'description_ru': "Уголь и дизельные генераторы",
        'description_en': "Coal and diesel generators",
        'flag': "🌍"
    },
    'oceania': {
        'name_ru': "🇦🇺 Австралия и Океания",
        'name_en': "🇦🇺 Australia and Oceania",
        'co2_factor': 0.60,
        'description_ru': "Уголь и природный газ",
        'description_en': "Coal and natural gas",
        'flag': "🇦🇺"
    },
    'unknown': {
        'name_ru': "❓ Не знаю / Среднее значение",
        'name_en': "❓ Don't know / Average value",
        'co2_factor': 0.35,
        'description_ru': "Среднемировой энергомикс",
        'description_en': "Global average energy mix",
        'flag': "❓"
    },
    'green_tariff': {
        'name_ru': "🌿 Зеленый тариф / 100% ВИЭ",
        'name_en': "🌿 Green tariff / 100% renewables",
        'co2_factor': 0.01,
        'description_ru': "Гарантированно возобновляемая энергия",
        'description_en': "Guaranteed renewable energy",
        'flag': "🌿"
    }
}

REGION_GROUPS = {
    'ru': {
        '🌍 Европа': ['scandinavia', 'eu_north', 'eu_west', 'eu_south', 'eastern_europe'],
        '🌏 Азия': ['asia_china', 'asia_japan', 'asia_south'],
        '🌎 Америка': ['usa_canada', 'latin_america'],
        '🌐 Другие регионы': ['cis_russia', 'middle_east', 'africa', 'oceania'],
        '📊 Специальные опции': ['unknown', 'green_tariff']
    },
    'en': {
        '🌍 Europe': ['scandinavia', 'eu_north', 'eu_west', 'eu_south', 'eastern_europe'],
        '🌏 Asia': ['asia_china', 'asia_japan', 'asia_south'],
        '🌎 America': ['usa_canada', 'latin_america'],
        '🌐 Other regions': ['cis_russia', 'middle_east', 'africa', 'oceania'],
        '📊 Special options': ['unknown', 'green_tariff']
    }
}

# --- КОЭФФИЦИЕНТЫ ---
CO2_FACTORS = {
    "benzin": {
        "ru": {
            "Малый (A/B класс)": 0.14,
            "Средний (C/D класс)": 0.18,
            "Кроссовер/SUV": 0.22,
            "Внедорожник": 0.28,
            "Премиум": 0.35
        },
        "en": {
            "Small (A/B class)": 0.14,
            "Medium (C/D class)": 0.18,
            "Crossover/SUV": 0.22,
            "Off-road": 0.28,
            "Premium": 0.35
        }
    },
    "diesel": {
        "ru": {
            "Малый (A/B класс)": 0.13,
            "Средний (C/D класс)": 0.17,
            "Кроссовер/SUV": 0.21,
            "Внедорожник": 0.26
        },
        "en": {
            "Small (A/B class)": 0.13,
            "Medium (C/D class)": 0.17,
            "Crossover/SUV": 0.21,
            "Off-road": 0.26
        }
    },
    "hybrid": {
        "ru": {
            "Малый/Средний": 0.09,
            "Кроссовер/SUV": 0.13
        },
        "en": {
            "Small/Medium": 0.09,
            "Crossover/SUV": 0.13
        }
    }
}

def get_co2_factors(fuel_type, lang='ru'):
    """Получение локализованных классов авто"""
    return CO2_FACTORS.get(fuel_type, {}).get(lang, {})

FUEL_TO_CO2 = {
    "benzin": 2.31,
    "diesel": 2.68,
    "hybrid": 2.31
}

ELECTRIC_CONSUMPTION = 18  # кВт·ч/100км

# --- СОВЕТЫ ---
ECO_TIPS = {
    'benzin': {
        'ru': [
            "✅ Поддерживайте правильное давление в шинах",
            "✅ Удалите ненужный груз из багажника",
            "✅ Заправляйтесь в прохладное время суток",
            "✅ Регулярно меняйте воздушный фильтр",
        ],
        'en': [
            "✅ Maintain proper tire pressure",
            "✅ Remove unnecessary weight from the trunk",
            "✅ Refuel during cooler times of the day",
            "✅ Change the air filter regularly",
        ]
    },
    'diesel': {
        'ru': [
            "✅ Используйте рекомендованные режимы движения",
            "✅ Проводите регулярную регенерацию DPF",
            "✅ Выбирайте качественное топливо",
            "✅ Избегайте коротких поездок в холодное время",
        ],
        'en': [
            "✅ Use recommended driving modes",
            "✅ Perform regular DPF regeneration",
            "✅ Choose high-quality fuel",
            "✅ Avoid short trips in cold weather",
        ]
    },
    'hybrid': {
        'ru': [
            "✅ Используйте электрический режим в городе",
            "✅ Пользуйтесь рекуперативным торможением",
            "✅ Избегайте резких ускорений",
            "✅ Планируйте маршрут с учетом рельефа",
        ],
        'en': [
            "✅ Use electric mode in the city",
            "✅ Use regenerative braking",
            "✅ Avoid sudden acceleration",
            "✅ Plan your route considering terrain",
        ]
    },
    'electric': {
        'ru': [
            "✅ Заряжайтесь в ночное время",
            "✅ Используйте быструю зарядку при необходимости",
            "✅ Предварительно прогревайте салон на питании",
            "✅ Поддерживайте заряд в диапазоне 20-80%",
        ],
        'en': [
            "✅ Charge during nighttime",
            "✅ Use fast charging when necessary",
            "✅ Pre-heat the cabin while plugged in",
            "✅ Maintain charge between 20-80%",
        ]
    }
}

GENERAL_TIPS = {
    'ru': [
        "📅 Планируйте маршруты заранее",
        "🔄 Объединяйте несколько задач в одну поездку",
        "🚲 Рассмотрите альтернативы для коротких дистанций",
        "🔧 Следите за техническим состоянием автомобиля",
    ],
    'en': [
        "📅 Plan routes in advance",
        "🔄 Combine multiple errands into one trip",
        "🚲 Consider alternatives for short distances",
        "🔧 Monitor the technical condition of the car",
    ]
}

# --- СОСТОЯНИЯ ---
SELECT_LANGUAGE, SELECT_FUEL, SELECT_METHOD, INPUT_CONSUMPTION, SELECT_CLASS, SELECT_ELECTRIC_REGION, INPUT_MILEAGE = range(7)

# --- ОСНОВНЫЕ ФУНКЦИИ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    # Добавлены флаги к выбору языка
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    
    await update.message.reply_text(
        "Выберите язык / Select language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка языка"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.replace('lang_', '')
    context.user_data['lang'] = lang
    
    keyboard = [
        [InlineKeyboardButton(t('benzin', lang), callback_data="fuel_benzin")],
        [InlineKeyboardButton(t('diesel', lang), callback_data="fuel_diesel")],
        [InlineKeyboardButton(t('hybrid', lang), callback_data="fuel_hybrid")],
        [InlineKeyboardButton(t('electric', lang), callback_data="fuel_electric")]
    ]
    
    await query.edit_message_text(
        f"{t('welcome', lang)}\n\n{t('select_fuel', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_FUEL

async def select_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа топлива"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'ru')
    fuel_type = query.data.replace('fuel_', '')
    context.user_data['fuel'] = fuel_type
    
    if fuel_type == "electric":
        return await ask_electric_region(query, lang, context)
    
    keyboard = [
        [InlineKeyboardButton(t('method_consumption', lang), callback_data="method_consumption")],
        [InlineKeyboardButton(t('method_class', lang), callback_data="method_class")]
    ]
    
    fuel_name = t(fuel_type, lang)
    await query.edit_message_text(
        f"{t('fuel_selected', lang)} {fuel_name}\n\n{t('select_method', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_METHOD

async def ask_electric_region(query, lang, context):
    """Выбор региона для электромобиля - С ЭМОДЗИ ФЛАГОВ!"""
    keyboard = []
    
    for group_name, region_keys in REGION_GROUPS[lang].items():
        # Добавляем заголовок группы с эмодзи
        keyboard.append([InlineKeyboardButton(f"──── {group_name} ────", callback_data="group_header")])
        
        for region_key in region_keys:
            region = ENERGY_REGIONS[region_key]
            region_name = region[f'name_{lang}']  # Уже содержит флаг
            region_desc = region[f'description_{lang}']
            
            # Кнопка с флагом и описанием
            button_text = f"{region_name} - {region_desc}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"eregion_{region_key}")])
    
    await query.edit_message_text(
        f"{t('electric_region', lang)}\n\n{t('electric_region_desc', lang)}\n\n{t('select_region', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_ELECTRIC_REGION

async def select_electric_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора региона"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'ru')
    region_key = query.data.replace('eregion_', '')
    
    if region_key == "group_header":
        return SELECT_ELECTRIC_REGION
    
    region = ENERGY_REGIONS.get(region_key, ENERGY_REGIONS['unknown'])
    context.user_data['electric_region'] = region_key
    context.user_data['electric_factor'] = region['co2_factor']
    
    region_name = region[f'name_{lang}']
    region_desc = region[f'description_{lang}']
    
    await query.edit_message_text(
        f"{t('region_selected', lang)} {region_name}\n"
        f"{t('description', lang)} {region_desc}\n"
        f"{t('co2_factor', lang)} {region['co2_factor']*100:.0f} {t('co2_per_kwh', lang)}\n\n"
        f"{t('enter_mileage', lang)}"
    )
    return INPUT_MILEAGE

async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор метода расчета"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'ru')
    method = query.data.replace('method_', '')
    context.user_data['method'] = method
    
    if method == "consumption":
        await query.edit_message_text(t('enter_consumption', lang))
        return INPUT_CONSUMPTION
    else:
        fuel_type = context.user_data['fuel']
        classes_dict = get_co2_factors(fuel_type, lang)
        
        keyboard = []
        for car_class in classes_dict.keys():
            keyboard.append([InlineKeyboardButton(car_class, callback_data=f"class_{car_class}")])
        
        fuel_name = t(fuel_type, lang)
        await query.edit_message_text(
            f"{t('select_class', lang)} ({fuel_name}):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_CLASS

async def input_consumption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод расхода топлива"""
    lang = context.user_data.get('lang', 'ru')
    
    try:
        text = update.message.text.strip()
        if not text:
            await update.message.reply_text(t('error_number', lang))
            return INPUT_CONSUMPTION
            
        consumption = float(text.replace(',', '.'))
        if consumption <= 0:
            await update.message.reply_text(t('error_positive', lang))
            return INPUT_CONSUMPTION
        
        context.user_data['consumption'] = consumption
        await update.message.reply_text(t('enter_mileage', lang))
        return INPUT_MILEAGE
        
    except ValueError:
        await update.message.reply_text(t('error_number', lang))
        return INPUT_CONSUMPTION

async def select_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор класса автомобиля"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'ru')
    car_class = query.data.replace('class_', '')
    context.user_data['car_class'] = car_class
    
    fuel_name = t(context.user_data.get('fuel'), lang)
    
    await query.edit_message_text(
        f"{t('fuel_selected', lang)} {fuel_name}\n"
        f"{t('class_selected', lang)} {car_class}\n\n"
        f"{t('enter_mileage', lang)}"
    )
    return INPUT_MILEAGE

async def input_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод пробега и расчет"""
    lang = context.user_data.get('lang', 'ru')
    
    try:
        text = update.message.text.strip()
        if not text:
            await update.message.reply_text(t('error_number', lang))
            return INPUT_MILEAGE
            
        mileage = float(text.replace(',', '.'))
        if mileage <= 0:
            await update.message.reply_text(t('error_positive', lang))
            return INPUT_MILEAGE
        
        fuel = context.user_data.get('fuel')
        if not fuel:
            await update.message.reply_text("Ошибка данных. Начните заново: /start")
            context.user_data.clear()
            return ConversationHandler.END
        
        co2 = 0.0
        details_lines = []
        
        if fuel == "electric":
            region_key = context.user_data.get('electric_region', 'unknown')
            region = ENERGY_REGIONS.get(region_key, ENERGY_REGIONS['unknown'])
            factor = region['co2_factor']
            region_name = region[f'name_{lang}']
            region_desc = region[f'description_{lang}']
            
            co2 = (mileage / 100) * ELECTRIC_CONSUMPTION * factor
            details_lines.append(f"{t('region', lang)} {region_name}")
            details_lines.append(f"{t('description', lang)} {region_desc}")
            details_lines.append(f"{t('co2_factor', lang)} {factor*100:.0f} {t('co2_per_kwh', lang)}")
            details_lines.append(f"{t('electric_consumption', lang)} {ELECTRIC_CONSUMPTION} кВт·ч/100км")
            
        else:
            method = context.user_data.get('method')
            
            if method == "consumption":
                consumption = context.user_data.get('consumption', 8.0)
                co2_per_liter = FUEL_TO_CO2.get(fuel, 2.31)
                co2 = (consumption / 100) * mileage * co2_per_liter
                details_lines.append(f"{t('consumption', lang)} {consumption} л/100км")
                details_lines.append(f"{t('co2_factor', lang)} {co2_per_liter} кг/л")
                
            else:
                car_class = context.user_data.get('car_class')
                factor = get_co2_factors(fuel, lang).get(car_class, 0.15)
                co2 = mileage * factor
                details_lines.append(f"{t('class_selected', lang)} {car_class}")
                details_lines.append(f"{t('co2_factor', lang)} {factor} кг/км")
        
        await show_results(update, context, fuel, details_lines, mileage, co2, lang)
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(t('error_number', lang))
        return INPUT_MILEAGE
    except Exception as e:
        logger.error(f"Ошибка расчета: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка расчета. Попробуйте /start")
        context.user_data.clear()
        return ConversationHandler.END

async def show_results(update, context, fuel_type, details_lines, mileage, co2_kg, lang='ru'):
    """Показывает результаты расчета"""
    
    trees_needed = co2_kg / 20
    
    fuel_key = fuel_type if fuel_type in ECO_TIPS else 'benzin'
    specific_tips = ECO_TIPS.get(fuel_key, {}).get(lang, [])
    general_tips = GENERAL_TIPS.get(lang, [])
    
    all_tips = specific_tips[:2] + general_tips[:2]
    
    # Формируем результат со всеми эмодзи
    result = f"""{t('result_header', lang)}
{t('separator', lang)}

{'⚡ ' + t('electric', lang) if fuel_type == 'electric' else t(fuel_type, lang)}
{"\n".join(details_lines)}
{t('mileage', lang)} {mileage:.0f} км

{t('emissions', lang)} {co2_kg:.1f} кг

{t('eco_equivalent', lang)}
{t('compensation', lang)} {trees_needed:.1f} {t('trees_per_year', lang)}
{t('tree_info', lang)}

{t('separator', lang)}
{t('eco_tips', lang)}"""
    
    for tip in all_tips:
        result += f"\n{tip}"
    
    result += f"\n\n{t('separator', lang)}\n{t('new_calc', lang)}"
    
    await update.message.reply_text(result)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена расчета"""
    lang = context.user_data.get('lang', 'ru')
    await update.message.reply_text(t('cancel', lang))
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(t('help_text', 'ru'))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке update {update}: {context.error}")
    
    try:
        await update.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте снова: /start"
        )
    except:
        pass

# --- ЗАПУСК БОТА ---
def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_error_handler(error_handler)
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LANGUAGE: [CallbackQueryHandler(set_language, pattern='^lang_')],
            SELECT_FUEL: [CallbackQueryHandler(select_fuel, pattern='^fuel_')],
            SELECT_METHOD: [CallbackQueryHandler(select_method, pattern='^method_')],
            INPUT_CONSUMPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_consumption)],
            SELECT_CLASS: [CallbackQueryHandler(select_class, pattern='^class_')],
            SELECT_ELECTRIC_REGION: [CallbackQueryHandler(select_electric_region, pattern='^eregion_')],
            INPUT_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_mileage)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('help', help_command),
            CommandHandler('start', start),
        ],
        allow_reentry=True
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help_command))
    
    print("🚀 Бот запускается...")
    print("📱 Перейдите в Telegram и найдите своего бота")
    print("⏹️ Для остановки нажмите Ctrl+C")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()