import sqlite3
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)

TOKEN = "8726596316:AAGi3d_tmCcsGEujgRM3mn-mJu2KN3heTKY"

# --- ИНИЦИАЛИЗА БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("rpg_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 50,
            potions INTEGER DEFAULT 2,
            weapon_power INTEGER DEFAULT 10,
            armor_defense INTEGER DEFAULT 0,
            weapon_name TEXT DEFAULT 'Ржавый меч',
            armor_name TEXT DEFAULT 'Обычная одежда'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_player(user_id, name):
    conn = sqlite3.connect("rpg_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("""
            INSERT INTO players (user_id, name) VALUES (?, ?)
        """, (user_id, name))
        conn.commit()
        cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
    conn.close()
    
    return {
        "user_id": row[0], "name": row[1], "hp": row[2], "max_hp": row[3],
        "level": row[4], "exp": row[5], "gold": row[6], "potions": row[7],
        "weapon_power": row[8], "armor_defense": row[9],
        "weapon_name": row[10], "armor_name": row[11]
    }

def update_player(p):
    conn = sqlite3.connect("rpg_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE players SET 
            hp = ?, max_hp = ?, level = ?, exp = ?, gold = ?, 
            potions = ?, weapon_power = ?, armor_defense = ?, 
            weapon_name = ?, armor_name = ?
        WHERE user_id = ?
    """, (
        p["hp"], p["max_hp"], p["level"], p["exp"], p["gold"],
        p["potions"], p["weapon_power"], p["armor_defense"],
        p["weapon_name"], p["armor_name"], p["user_id"]
    ))
    conn.commit()
    conn.close()

# --- МЕНЮ ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("⚔️ На охоту", callback_data="hunt")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile"), InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton("🏪 Магазин", callback_data="shop"), InlineKeyboardButton("🧪 Выпить зелье (+40 HP)", callback_data="heal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def shop_menu():
    keyboard = [
        [InlineKeyboardButton("🧪 Зелье (20💰)", callback_data="buy_potion")],
        [InlineKeyboardButton("⚔️ Стальной меч (+15 атк) — 100💰", callback_data="buy_weapon")],
        [InlineKeyboardButton("🛡️ Кожаная броня (+5 защ) — 80💰", callback_data="buy_armor")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- ОБРАБОТЧИКИ КОМАНД ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_player(user.id, user.first_name)
    await update.message.reply_text(
        f"🛡️ Добро пожаловать в RPG Мир, {user.first_name}!\n"
        "Исследуйте подземелья, покупайте экипировку и прокачивайте героя!",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    p = get_player(user.id, user.first_name)
    data = query.data

    if data == "menu":
        await query.edit_message_text("Выберите действие:", reply_markup=main_menu())

    elif data == "profile":
        exp_needed = p["level"] * 50
        text = (
            f"👤 **Герой:** {p['name']}\n"
            f"⭐ **Уровень:** {p['level']} (Опыт: {p['exp']}/{exp_needed})\n"
            f"❤️ **HP:** {p['hp']}/{p['max_hp']}\n"
            f"⚔️ **Атака:** {p['weapon_power']}\n"
            f"🛡️ **Защита:** {p['armor_defense']}\n"
            f"💰 **Золото:** {p['gold']}\n\n"
            f"🗡️ **Оружие:** {p['weapon_name']}\n"
            f"🛡️ **Броня:** {p['armor_name']}"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "inventory":
        text = f"🎒 **Ваш инвентарь:**\n\n🧪 Зелья здоровья: {p['potions']} шт."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "heal":
        if p["potions"] <= 0:
            text = "❌ У вас нет зелий!"
        elif p["hp"] >= p["max_hp"]:
            text = "❤️ У вас уже максимум HP!"
        else:
            p["potions"] -= 1
            p["hp"] = min(p["max_hp"], p["hp"] + 40)
            update_player(p)
            text = f"🧪 Вы восстановили здоровье! Текущее HP: {p['hp']}/{p['max_hp']}"
        await query.edit_message_text(text, reply_markup=main_menu())

    elif data == "shop":
        await query.edit_message_text("🏪 **Магазин снаряжения и зелий:**", parse_mode="Markdown", reply_markup=shop_menu())

    elif data == "buy_potion":
        if p["gold"] >= 20:
            p["gold"] -= 20
            p["potions"] += 1
            update_player(p)
            text = "✅ Вы купили 1 зелье здоровья!"
        else:
            text = "❌ Недостаточно золота!"
        await query.edit_message_text(text, reply_markup=shop_menu())

    elif data == "buy_weapon":
        if p["gold"] >= 100:
            p["gold"] -= 100
            p["weapon_power"] = 25
            p["weapon_name"] = "Стальной меч"
            update_player(p)
            text = "⚔️ Вы купили Стальной меч! Атака повышена до 25."
        else:
            text = "❌ Недостаточно золота!"
        await query.edit_message_text(text, reply_markup=shop_menu())

    elif data == "buy_armor":
        if p["gold"] >= 80:
            p["gold"] -= 80
            p["armor_defense"] = 5
            p["armor_name"] = "Кожаная броня"
            update_player(p)
            text = "🛡️ Вы купили Кожаную броню! Защита повышена до 5."
        else:
            text = "❌ Недостаточно золота!"
        await query.edit_message_text(text, reply_markup=shop_menu())

    elif data == "hunt":
        if p["hp"] <= 0:
            await query.edit_message_text("☠️ Вы погибли! Восстановите HP зельем перед боем.", reply_markup=main_menu())
            return

        monsters = [
            {"name": "Гоблин", "hp": 35, "attack": 10, "gold": 20, "exp": 25},
            {"name": "Дикий Волк", "hp": 50, "attack": 14, "gold": 30, "exp": 40},
            {"name": "Пещерный Огр", "hp": 90, "attack": 22, "gold": 75, "exp": 80}
        ]
        
        monster = random.choice(monsters)
        
        # Расчет урона
        player_dmg = random.randint(p["weapon_power"] - 2, p["weapon_power"] + 4)
        monster_dmg = max(1, random.randint(monster["attack"] - 3, monster["attack"] + 2) - p["armor_defense"])
        
        p["hp"] = max(0, p["hp"] - monster_dmg)
        
        if player_dmg >= monster["hp"]:
            p["gold"] += monster["gold"]
            p["exp"] += monster["exp"]
            
            # Проверка уровня
            exp_needed = p["level"] * 50
            lvl_text = ""
            if p["exp"] >= exp_needed:
                p["level"] += 1
                p["max_hp"] += 25
                p["hp"] = p["max_hp"]
                p["weapon_power"] += 3
                lvl_text = f"\n\n🎉 **Уровень повышен!** Теперь вы {p['level']} уровня!"

            update_player(p)
            text = (
                f"⚔️ Вы встретили **{monster['name']}**!\n"
                f"💥 Вы нанесли {player_dmg} урона и одолели врага!\n"
                f"🛡️ Враг нанес вам {monster_dmg} урона.\n\n"
                f"🎁 Вы получили: {monster['gold']} 💰 и {monster['exp']} EXP.{lvl_text}"
            )
        else:
            update_player(p)
            text = (
                f"⚔️ Вы встретили **{monster['name']}**!\n"
                f"💥 Вы нанесли {player_dmg} урона, но монстр сбежал!\n"
                f"🩸 Вы получили {monster_dmg} урона (Текущее HP: {p['hp']}/{p['max_hp']})."
            )

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

# --- ЗАПУСК ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Бот успешно запущен!")
    app.run_polling()
          
