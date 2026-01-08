import logging
import uuid
import asyncio
import os
import io
import re
from datetime import datetime
from supabase import create_client, Client
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, InputFile
)
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

SUPABASE_URL = "https://ajzchkjwtpxlaprkmktc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFqemNoa2p3dHB4bGFwcmtta3RjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY4NTEzMCwiZXhwIjoyMDgzMjYxMTMwfQ.a8Ooc2x02OOKBfroshxCDe1nA_f5VSxoC-ZrdQj3b6c"

BOT_TOKEN = "8254879975:AAF-ikyNFF3kUeZWBT0pwbq-YnqWRxNIv20"
ADMIN_ID = 7637946765
CHANNEL_ID = -1003496634656
CHANNEL_LINK = "https://t.me/+91AhyuED8wthNzky"
CHANNEL_USERNAME = "@RavionScripts"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AdminStates(StatesGroup):
    waiting_post_content = State()
    confirm_post = State()
    waiting_broadcast_msg = State()
    waiting_edit_uuid = State()
    waiting_edit_content = State()
    waiting_delete_uuid = State()
    waiting_search_uuid = State()
    waiting_user_lookup = State()

class UserStates(StatesGroup):
    waiting_search_query = State()

async def sb_add_script(uid, title, content):
    def _req():
        supabase.table('scripts').insert({
            "uuid": uid,
            "title": title,
            "content": content
        }).execute()
    await asyncio.to_thread(_req)

async def sb_get_script(uid):
    def _req():
        res = supabase.table('scripts').select("title, content, views").eq("uuid", uid).execute()
        if res.data:
            supabase.rpc("increment_script_views", {"script_uuid": uid}).execute()
            return res.data[0]
        return None
    return await asyncio.to_thread(_req)

async def sb_update_script(uid, content):
    def _req():
        res = supabase.table('scripts').update({"content": content}).eq("uuid", uid).execute()
        return len(res.data) > 0
    return await asyncio.to_thread(_req)

async def sb_delete_script(uid):
    def _req():
        res = supabase.table('scripts').delete().eq("uuid", uid).execute()
        return len(res.data) > 0
    return await asyncio.to_thread(_req)

async def sb_search_scripts(query):
    def _req():
        res = supabase.table('scripts').select("uuid, title, views") \
            .ilike("title", f"%{query}%") \
            .order("views", desc=True).limit(10).execute()
        return res.data
    return await asyncio.to_thread(_req)

async def sb_get_top_scripts(limit=10):
    def _req():
        res = supabase.table('scripts').select("title, views, uuid") \
            .order("views", desc=True).limit(limit).execute()
        return res.data
    return await asyncio.to_thread(_req)

async def sb_upsert_user(user):
    def _req():
        f_name = user.first_name.replace("<", "&lt;").replace(">", "&gt;") if user.first_name else "User"
        u_name = user.username if user.username else "None"
        
        exist = supabase.table('users').select("user_id").eq("user_id", user.id).execute()
        
        if not exist.data:
            supabase.table('users').insert({
                "user_id": user.id,
                "first_name": f_name,
                "username": u_name,
                "status": "active"
            }).execute()
        else:
            supabase.table('users').update({
                "first_name": f_name,
                "username": u_name,
                "status": "active"
            }).eq("user_id", user.id).execute()
    await asyncio.to_thread(_req)

async def sb_inc_user_stats(user_id):
    def _req():
        supabase.rpc("increment_user_stats", {"target_user_id": user_id}).execute()
    await asyncio.to_thread(_req)

async def sb_get_stats():
    def _req():
        total = supabase.table('users').select("user_id", count="exact").execute().count
        active = supabase.table('users').select("user_id", count="exact").eq("status", "active").execute().count
        scripts_count = supabase.table('scripts').select("uuid", count="exact").execute().count
        
        res_dl = supabase.table('users').select("scripts_received").execute()
        downloads = sum(row['scripts_received'] for row in res_dl.data) if res_dl.data else 0
        
        return total, active, downloads, scripts_count
    return await asyncio.to_thread(_req)

async def sb_get_all_users_ids():
    def _req():
        res = supabase.table('users').select("user_id").execute()
        return [row['user_id'] for row in res.data]
    return await asyncio.to_thread(_req)

async def sb_get_user_info(target_id):
    def _req():
        res = supabase.table('users').select("*").eq("user_id", target_id).execute()
        return res.data[0] if res.data else None
    return await asyncio.to_thread(_req)

def get_main_kb(user_id):
    if user_id == ADMIN_ID:
        kb = [
            [KeyboardButton(text="📝 Создать пост"), KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="✏️ Редактировать"), KeyboardButton(text="🗑 Удалить скрипт")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👤 Поиск Юзера")],
            [KeyboardButton(text="📦 Бэкап Базы"), KeyboardButton(text="🔍 Найти UUID")]
        ]
    else:
        kb = [
            [KeyboardButton(text="🔎 Поиск скрипта"), KeyboardButton(text="📂 Мой профиль")],
            [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="🎮 Канал скриптов")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True, one_time_keyboard=True)

async def check_subscription(bot: Bot, user_id: int) -> bool:
    if user_id == ADMIN_ID: return True
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return True

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    await sb_upsert_user(message.from_user)
    args = command.args

    if args:
        if not await check_subscription(bot, message.from_user.id):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Подписаться", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Проверить", url=f"https://t.me/{bot.get_me().username}?start={args}")]
            ])
            await message.answer("🔒 <b>Доступ ограничен!</b>\nПодпишись на канал для доступа.", reply_markup=kb)
            return

        script_data = await sb_get_script(args)
        if not script_data:
            await message.answer("❌ <b>Ошибка 404:</b> Скрипт не найден.")
            return

        title = script_data['title']
        content = script_data['content']
        views = script_data['views']
        
        header = f"✅ <b>Скрипт найден!</b>\n🎮 Игра: <b>{title}</b>\n👀 Загрузок: {views + 1}"
        clean_code = f"-- {title}\n-- Source: {CHANNEL_USERNAME}\n\n{content}"
        
        await message.answer(header)
        
        if len(clean_code) > 3000:
            safe_name = re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_")
            file_data = io.BytesIO(clean_code.encode('utf-8'))
            await message.answer_document(BufferedInputFile(file_data.getvalue(), filename=f"{safe_name}.lua"), caption="📂 Скрипт файлом")
        else:
            try:
                await message.answer(f"<code>{clean_code}</code>")
            except:
                await message.answer(clean_code)
        
        await sb_inc_user_stats(message.from_user.id)
        return

    role = "👑 GOD MODE" if message.from_user.id == ADMIN_ID else "👤 Пользователь"
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\nСтатус: {role}\n🤖 База: <b>Supabase Cloud</b>",
        reply_markup=get_main_kb(message.from_user.id)
    )

@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_main_kb(message.from_user.id))

@router.message(F.text == "📂 Мой профиль")
async def profile(message: Message):
    res = await sb_get_user_info(message.from_user.id)
    if not res: return
    date_joined = datetime.fromisoformat(res['joined_at']).strftime('%Y-%m-%d')
    await message.answer(
        f"👤 <b>Личный кабинет</b>\n🆔: <code>{message.from_user.id}</code>\n"
        f"🔰 Статус: {res['status'].upper()}\n📅 Регистрация: {date_joined}\n"
        f"📥 Скриптов: <b>{res['scripts_received']}</b>"
    )

@router.message(F.text == "🆘 Поддержка")
async def support(message: Message):
    await message.answer(f"👨‍💻 Владелец: @RavionScripts", disable_web_page_preview=True)

@router.message(F.text == "🎮 Канал скриптов")
async def channel_link(message: Message):
    await message.answer(f"🔗 Скрипты тут:\n{CHANNEL_LINK}")

@router.message(F.user_id == ADMIN_ID, F.text == "📝 Создать пост")
async def admin_create_post(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_post_content)
    await message.answer(
        "<b>📝 Создание поста</b>\nФормат:\n1. Название\n2. Описание\n3. Теги (#...)\n4. Код скрипта",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminStates.waiting_post_content)
async def process_post_content(message: Message, state: FSMContext, bot: Bot):
    text = message.caption or message.text
    if not text:
        await message.answer("❌ Нужен текст!")
        return

    lines = text.split('\n')
    if len(lines) < 3:
        await message.answer("❌ Слишком короткий текст.")
        return

    game_name = lines[0].strip()
    tags_idx = -1
    tags = ""
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            tags = line.strip()
            tags_idx = i
            break
    
    if tags_idx == -1:
        desc = lines[1].strip()
        script = "\n".join(lines[2:]).strip()
        tags = "#Script"
    else:
        desc = "\n".join(lines[1:tags_idx]).strip()
        script = "\n".join(lines[tags_idx+1:]).strip()

    if not script:
        await message.answer("❌ Код не найден.")
        return

    uid = str(uuid.uuid4())[:8]
    key_status = "🔓 <b>Ключ:</b> Не требуется" if "#nokey" in tags.lower() else "🔐 <b>Ключ:</b> Требуется"
    tags_clean = tags.replace("#nokey", "").strip()

    post_data = {
        'game': game_name, 'desc': desc, 'tags': tags_clean, 
        'key_status': key_status, 'script': script, 'uuid': uid,
        'photo': message.photo[-1].file_id if message.photo else None,
        'video': message.video.file_id if message.video else None
    }
    await state.update_data(post=post_data)

    preview = (
        f"━━━━━━━━━━━━━━━━━━━\n🎮 <b>{game_name.upper()}</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 {desc}\n\n{key_status}\n{tags_clean}\n\n"
        f"👇 <b>Нажми кнопку ниже, чтобы получить скрипт</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n📢 {CHANNEL_USERNAME}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Получить (Тест)", url=f"https://t.me/{(await bot.get_me()).username}?start={uid}")],
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="pub_yes"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="pub_no")]
    ])

    await message.answer("👁 <b>Предпросмотр:</b>")
    if post_data['photo']:
        await message.answer_photo(post_data['photo'], caption=preview, reply_markup=kb)
    elif post_data['video']:
        await message.answer_video(post_data['video'], caption=preview, reply_markup=kb)
    else:
        await message.answer(preview, reply_markup=kb)
    
    await state.set_state(AdminStates.confirm_post)

@router.callback_query(AdminStates.confirm_post, F.data.in_({"pub_yes", "pub_no"}))
async def confirm_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == "pub_no":
        await callback.message.delete()
        await callback.message.answer("❌ Отменено.", reply_markup=get_main_kb(ADMIN_ID))
        await state.clear()
        return

    data = await state.get_data()
    post = data['post']
    await sb_add_script(post['uuid'], post['game'], post['script'])

    text = (
        f"━━━━━━━━━━━━━━━━━━━\n🎮 <b>{post['game'].upper()}</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 {post['desc']}\n\n{post['key_status']}\n{post['tags']}\n\n"
        f"👇 <b>Нажми кнопку ниже, чтобы получить скрипт</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n📢 {CHANNEL_USERNAME}"
    )
    
    url = f"https://t.me/{(await bot.get_me()).username}?start={post['uuid']}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📜 Получить скрипт", url=url)]])

    try:
        if post['photo']:
            await bot.send_photo(CHANNEL_ID, post['photo'], caption=text, reply_markup=kb)
        elif post['video']:
            await bot.send_video(CHANNEL_ID, post['video'], caption=text, reply_markup=kb)
        else:
            await bot.send_message(CHANNEL_ID, text, reply_markup=kb)
        
        await callback.message.delete()
        await callback.message.answer(f"✅ Опубликовано! UUID: <code>{post['uuid']}</code>", reply_markup=get_main_kb(ADMIN_ID))
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка отправки: {e}")
    
    await state.clear()

@router.message(F.user_id == ADMIN_ID, F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_broadcast_msg)
    await message.answer("📢 Пришли сообщение для рассылки.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_broadcast_msg)
async def confirm_broadcast(message: Message, state: FSMContext):
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ЗАПУСТИТЬ", callback_data="broadcast_go")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])
    await message.answer("⚠️ Отправить всем пользователям?", reply_markup=kb)

@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("❌ Отменено.", reply_markup=get_main_kb(ADMIN_ID))
    await state.clear()

@router.callback_query(F.data == "broadcast_go")
async def run_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_id = data['msg_id']
    from_chat = data['chat_id']
    users = await sb_get_all_users_ids()
    
    status_msg = await callback.message.edit_text("🚀 Рассылка началась...")
    success, blocked = 0, 0
    
    for i, uid in enumerate(users):
        try:
            await bot.copy_message(uid, from_chat, msg_id)
            success += 1
        except TelegramForbiddenError:
            blocked += 1
        except Exception:
            pass
        
        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"🚀 Рассылка: {i}/{len(users)}\n✅ {success} | 🚫 {blocked}")
            except: pass
        await asyncio.sleep(0.04)

    await status_msg.delete()
    await callback.message.answer(f"🏁 <b>Завершено!</b>\n✅ Доставлено: {success}\n🚫 Заблокировано: {blocked}", reply_markup=get_main_kb(ADMIN_ID))
    await state.clear()

@router.message(F.user_id == ADMIN_ID, F.text == "📊 Статистика")
async def admin_stats(message: Message):
    total, active, dls, scripts = await sb_get_stats()
    top = await sb_get_top_scripts()
    top_text = "\n".join([f"{i+1}. <b>{t['title']}</b> - {t['views']} 👀 (<code>{t['uuid']}</code>)" for i, t in enumerate(top)])
    
    text = (
        "📈 <b>DASHBOARD</b>\n"
        f"👥 Пользователи: <b>{total}</b> (Active: {active})\n"
        f"💾 Скачиваний: <b>{dls}</b>\n"
        f"📂 Скриптов: <b>{scripts}</b>\n\n"
        f"🏆 <b>Топ-10:</b>\n{top_text}"
    )
    await message.answer(text)

@router.message(F.user_id == ADMIN_ID, F.text == "✏️ Редактировать")
async def edit_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_edit_uuid)
    await message.answer("✏️ Введи UUID скрипта для замены.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_edit_uuid)
async def edit_uuid(message: Message, state: FSMContext):
    uid = message.text.strip()
    script = await sb_get_script(uid)
    if not script:
        await message.answer("❌ UUID не найден.")
        return
    await state.update_data(uuid=uid)
    await state.set_state(AdminStates.waiting_edit_content)
    await message.answer(f"✅ Найден: <b>{script['title']}</b>\nПришли новый код.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_edit_content)
async def edit_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    if await sb_update_script(data['uuid'], message.text):
        await message.answer("✅ Скрипт обновлен!", reply_markup=get_main_kb(ADMIN_ID))
    else:
        await message.answer("❌ Ошибка БД.")
    await state.clear()

@router.message(F.user_id == ADMIN_ID, F.text == "🗑 Удалить скрипт")
async def delete_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_delete_uuid)
    await message.answer("🗑 Введи UUID для удаления.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_delete_uuid)
async def delete_finish(message: Message, state: FSMContext):
    if await sb_delete_script(message.text.strip()):
        await message.answer("✅ Скрипт удален.", reply_markup=get_main_kb(ADMIN_ID))
    else:
        await message.answer("❌ Ошибка или не найдено.")
    await state.clear()

@router.message(F.user_id == ADMIN_ID, F.text == "📦 Бэкап Базы")
async def backup_db(message: Message):
    await message.answer("💾 Используй Supabase Dashboard для бэкапа (Export CSV).")

@router.message(F.user_id == ADMIN_ID, F.text == "👤 Поиск Юзера")
async def lookup_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_user_lookup)
    await message.answer("👤 Пришли ID пользователя.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_user_lookup)
async def lookup_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Только цифры.")
        return
    info = await sb_get_user_info(int(message.text))
    if info:
        joined = datetime.fromisoformat(info['joined_at']).strftime('%Y-%m-%d %H:%M')
        await message.answer(
            f"🕵️‍♂️ <b>Инфо:</b>\nName: {info['first_name']}\nUser: @{info['username']}\nStatus: {info['status']}\nScripts: {info['scripts_received']}\nJoined: {joined}",
            reply_markup=get_main_kb(ADMIN_ID)
        )
    else:
        await message.answer("❌ Не найден.", reply_markup=get_main_kb(ADMIN_ID))
    await state.clear()

@router.message(F.user_id == ADMIN_ID, F.text == "🔍 Найти UUID")
async def admin_search_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_search_uuid)
    await message.answer("🔍 Введи название игры.", reply_markup=get_cancel_kb())

@router.message(AdminStates.waiting_search_uuid)
async def admin_search_finish(message: Message, state: FSMContext):
    res = await sb_search_scripts(message.text)
    if res:
        text = "🔍 <b>Результаты:</b>\n" + "\n".join([f"🎮 <b>{r['title']}</b>\n🆔 <code>{r['uuid']}</code>\n👀 {r['views']}" for r in res])
        await message.answer(text, reply_markup=get_main_kb(ADMIN_ID))
    else:
        await message.answer("❌ Пусто.", reply_markup=get_main_kb(ADMIN_ID))
    await state.clear()

@router.message(F.text == "🔎 Поиск скрипта")
async def user_search_start(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_search_query)
    await message.answer("🔎 Введи название игры:", reply_markup=get_cancel_kb())

@router.message(UserStates.waiting_search_query)
async def user_search_finish(message: Message, state: FSMContext, bot: Bot):
    res = await sb_search_scripts(message.text)
    if res:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📥 {r['title']}", url=f"https://t.me/{(await bot.get_me()).username}?start={r['uuid']}")]
            for r in res
        ])
        await message.answer(f"🔎 Найдено {len(res)} скриптов:", reply_markup=kb)
        await message.answer("⬆️ Выбери скрипт выше.", reply_markup=get_main_kb(message.from_user.id))
    else:
        await message.answer("😔 Ничего не найдено.", reply_markup=get_main_kb(message.from_user.id))
    await state.clear()

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Ravion Bot v5.0 Ultimate (Supabase Edition) Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
