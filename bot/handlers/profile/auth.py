from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile

from ...keyboards import profile_kb, main_menu_kb
from ...utils.helpers import safe_edit_text
from ...database.engine import session_scope
from ...services.cart_service import CartService
from ...database.repository import PurchaseRepo, UserRepo
from ...utils.states import AuthRegisterState, AuthLoginState


router = Router()


@router.callback_query(lambda c: c.data == "profile:open")
async def open_profile(cb: CallbackQuery, db_user):
    try:
        # Compute counts for cart and purchases
        async with session_scope() as session:
            cart_items, _ = await CartService(session).list_with_total(db_user.id)
            purchases_all = await PurchaseRepo(session).list_by_user(db_user.id)
        cart_count = sum(qty for _, _, qty, _ in cart_items)
        # Deduplicate purchases by product_id for badge consistency with history screen
        latest_by_product = {}
        for p in purchases_all:
            latest_by_product[p.product_id] = p
        purchases_count = len(latest_by_product)
        login_text = db_user.login or "-"
        text = f"<b>👤 Профиль</b>\n🧑‍💻 Логин: {login_text}"
        from ...config import PROFILE_PHOTO_FILE_ID
        try:
            if PROFILE_PHOTO_FILE_ID:
                await cb.message.answer_photo(photo=PROFILE_PHOTO_FILE_ID, caption=text, reply_markup=profile_kb(cart_count, purchases_count))
            else:
                await cb.message.answer(text, reply_markup=profile_kb(cart_count, purchases_count))
        except Exception:
            await cb.message.answer(text, reply_markup=profile_kb(cart_count, purchases_count))
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.answer()
    except Exception:
        # Fallback to simple text if anything goes wrong
        await safe_edit_text(cb.message, "<b>👤 Профиль</b>", reply_markup=profile_kb())
        await cb.answer()


@router.callback_query(lambda c: c.data == "profile:logout")
async def profile_logout(cb: CallbackQuery, db_user, db_session):
    # Clear login/password for current user
    db_user.login = None
    db_user.password_hash = None
    await db_session.flush()
    # Return to main menu with login/register button
    from ...keyboards import main_menu_kb
    from ...database.repository import ProductRepo
    from ...database.engine import session_scope as _sc
    async with _sc() as s:
        popular_count = len(await ProductRepo(s).list_popular(limit=50))
    await safe_edit_text(cb.message, "🏠 Главное меню", reply_markup=main_menu_kb(is_admin=False, popular_count=popular_count, is_logged_in=False))
    await cb.answer("Вы вышли из профиля")

@router.callback_query(lambda c: c.data == "auth:login")
async def auth_login(cb: CallbackQuery, state: FSMContext):
    # Start login flow immediately: ask for login first
    await state.set_state(AuthLoginState.waiting_for_login)
    text = (
        "<b>🔐 Вход</b>\n\n"
        "Введите логин и пароль для входа.\n\n"
        "Если у вас нет аккаунта — вы можете зарегистрироваться.\n\n"
        "🧑‍💻 Введите логин:"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="auth:register")], [InlineKeyboardButton(text="🏠 Меню", callback_data="home")]])
    try:
        await cb.message.delete()
    except Exception:
        pass
    sent = await cb.message.answer(text, reply_markup=kb)
    await state.update_data(prompt_msg_id=sent.message_id)
    await cb.answer()


@router.callback_query(lambda c: c.data == "auth:login:start")
async def auth_login_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AuthLoginState.waiting_for_login)
    await safe_edit_text(cb.message, "🧑‍💻 Введите логин:")
    await cb.answer()


@router.message(AuthLoginState.waiting_for_login)
async def auth_login_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text.strip())
    await state.set_state(AuthLoginState.waiting_for_password)
    # delete user message and previous prompt, then send new prompt
    try:
        await message.delete()
    except Exception:
        pass
    data = await state.get_data()
    prev_prompt_id = data.get("prompt_msg_id")
    if prev_prompt_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
        except Exception:
            pass
    sent = await message.answer("🔑 Введите пароль:")
    await state.update_data(prompt_msg_id=sent.message_id)


@router.message(AuthLoginState.waiting_for_password)
async def auth_login_finish(message: Message, state: FSMContext, db_user, db_session):
    try:
        data = await state.get_data()
        login = data.get("login", "").strip()
        password = message.text.strip()
        # Проверка данных: должны совпадать с записанными у пользователя
        if not db_user.login or not db_user.password_hash or db_user.login != login or db_user.password_hash != password:
            await state.clear()
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            text = (
                "❌ Неверный логин или пароль. Попробуйте снова.\n\n"
                "<b>🔐 Вход</b>\n\n"
                "Если у вас нет аккаунта — вы можете зарегистрироваться."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Войти", callback_data="auth:login:start")], [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="auth:register")], [InlineKeyboardButton(text="🏠 Меню", callback_data="home")]])
            # delete user message and any previous prompt
            try:
                await message.delete()
            except Exception:
                pass
            prev_prompt_id = data.get("prompt_msg_id")
            if prev_prompt_id:
                try:
                    await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
                except Exception:
                    pass
            await message.answer(text, reply_markup=kb)
            return
        await state.clear()
        # Успешный вход — показываем профиль с фото
    except Exception:
        await state.clear()
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Меню", callback_data="home")]]))
    try:
        # delete user message and any previous prompt
        try:
            await message.delete()
        except Exception:
            pass
        prev_prompt_id = data.get("prompt_msg_id")
        if prev_prompt_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
            except Exception:
                pass
        photo = InputFile("profile_photo.png")
        await message.answer_photo(photo=photo, caption=f"<b>👤 Профиль</b>\n🧑‍💻 Логин: {db_user.login}\n🔑 Пароль: {db_user.password_hash}", reply_markup=profile_kb(0, 0))
    except Exception:
        await message.answer(f"<b>👤 Профиль</b>\n🧑‍💻 Логин: {db_user.login}\n🔑 Пароль: {db_user.password_hash}", reply_markup=profile_kb(0, 0))


@router.callback_query(lambda c: c.data == "auth:register")
async def auth_register_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AuthRegisterState.waiting_for_login)
    await safe_edit_text(cb.message, "🧑‍💻 Придумайте логин:")
    await cb.answer()


@router.message(AuthRegisterState.waiting_for_login)
async def auth_register_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text.strip()[:50])
    await state.set_state(AuthRegisterState.waiting_for_email)
    try:
        await message.delete()
    except Exception:
        pass
    # delete previous prompt if any
    data = await state.get_data()
    prev_prompt_id = data.get("prompt_msg_id")
    if prev_prompt_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
        except Exception:
            pass
    sent = await message.answer(
        "📧 Введите ваш email:\n\n"
        "⚠️ <b>Важно:</b> Указывайте корректный email, иначе могут возникать проблемы с оплатой!\n"
        "Email нужен для отправки чеков и уведомлений о платежах."
    )
    await state.update_data(prompt_msg_id=sent.message_id)


@router.message(AuthRegisterState.waiting_for_email)
async def auth_register_email(message: Message, state: FSMContext):
    from ...utils.helpers import validate_email
    
    email = message.text.strip().lower()
    
    if not validate_email(email):
        try:
            await message.delete()
        except Exception:
            pass
        # delete previous prompt if any
        data = await state.get_data()
        prev_prompt_id = data.get("prompt_msg_id")
        if prev_prompt_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
            except Exception:
                pass
        sent = await message.answer(
            "❌ Неверный формат email!\n\n"
            "📧 Введите корректный email (например: user@example.com):\n\n"
            "⚠️ <b>Важно:</b> Указывайте корректный email, иначе могут возникать проблемы с оплатой!"
        )
        await state.update_data(prompt_msg_id=sent.message_id)
        return
    
    await state.update_data(email=email)
    await state.set_state(AuthRegisterState.waiting_for_password)
    try:
        await message.delete()
    except Exception:
        pass
    # delete previous prompt if any
    data = await state.get_data()
    prev_prompt_id = data.get("prompt_msg_id")
    if prev_prompt_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
        except Exception:
            pass
    sent = await message.answer("🔑 Придумайте пароль:")
    await state.update_data(prompt_msg_id=sent.message_id)


@router.message(AuthRegisterState.waiting_for_password)
async def auth_register_finish(message: Message, state: FSMContext, db_user, db_session):
    data = await state.get_data()
    login = data.get("login")
    email = data.get("email")
    password = message.text.strip()
    # Save to current db_user
    db_user.login = login
    db_user.email = email
    db_user.password_hash = password  # Note: hash in prod
    await db_session.flush()
    await state.clear()
    # Show profile with photo
    try:
        try:
            await message.delete()
        except Exception:
            pass
        prev_prompt_id = data.get("prompt_msg_id")
        if prev_prompt_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
            except Exception:
                pass
        photo = InputFile("profile_photo.png")
        await message.answer_photo(photo=photo, caption=f"<b>👤 Профиль</b>\n🧑‍💻 Логин: {login}\n📧 Email: {email}\n🔑 Пароль: {password}", reply_markup=profile_kb(0, 0))
    except Exception:
        await message.answer(f"<b>👤 Профиль</b>\n🧑‍💻 Логин: {login}\n📧 Email: {email}\n🔑 Пароль: {password}", reply_markup=profile_kb(0, 0))
