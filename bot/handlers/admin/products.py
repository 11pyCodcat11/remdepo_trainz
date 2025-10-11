from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from ...config import BOT_ADMINS
from ...keyboards import (
    admin_main_kb,
    admin_products_kb,
    admin_product_actions_kb,
    admin_products_list_kb,
    admin_categories_pick_kb,
)
from ...utils.states import AdminProductState, AdminProductEditState
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from decimal import Decimal
from ...database.engine import session_scope
from ...database.models import Product, Category
from ...database.repository import ProductRepo
from sqlalchemy import select


router = Router()


def _is_admin(uid: int) -> bool:
    return uid in BOT_ADMINS


@router.callback_query(lambda c: c.data == "admin:products")
async def admin_products(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    await cb.message.edit_text("Админ: Товары\nВ спике товаров вы можеет отредактирвоать или удалить любой товар!", reply_markup=admin_products_kb())
    await cb.answer()


@router.callback_query(lambda c: c.data == "admin:prod:add")
async def prod_add_start(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    await state.set_state(AdminProductState.waiting_for_name)
    await cb.message.edit_text("Введите название товара:")
    await cb.answer()


@router.message(AdminProductState.waiting_for_name)
async def prod_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    # Показать выбор категории
    async with session_scope() as session:
        from sqlalchemy import select
        res = await session.execute(select(Category).order_by(Category.name))
        cats = res.scalars().all()
    if not cats:
        await message.answer("Сначала создайте категорию")
        return await state.clear()
    await state.set_state(AdminProductState.waiting_for_category)
    await message.answer("Выберите категорию:", reply_markup=admin_categories_pick_kb([(c.id, c.name) for c in cats]))


@router.callback_query(lambda c: c.data.startswith("admin:cat:pick:"))
async def prod_pick_category(cb: CallbackQuery, state: FSMContext):
    cid = int(cb.data.split(":")[-1])
    await state.update_data(category_id=cid)
    await state.set_state(AdminProductState.waiting_for_price)
    await cb.message.edit_text("Введите цену (например 2500.00, 0 — бесплатно):")
    await cb.answer()


@router.message(AdminProductState.waiting_for_price)
async def prod_add_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.replace(",", ".").strip())
    except Exception:
        return await message.answer("Неверная цена. Повторите ввод, например 199.99")
    await state.update_data(price=price)
    await state.set_state(AdminProductState.waiting_for_desc)
    await message.answer("Введите короткое описание (для карточки):")


@router.message(AdminProductState.waiting_for_desc)
async def prod_add_desc(message: Message, state: FSMContext):
    await state.update_data(short_description=message.text.strip())
    await message.answer("Введите полное описание (для раздела 'О товаре'):")
    await state.set_state(AdminProductState.waiting_for_full_desc)


@router.message(AdminProductState.waiting_for_full_desc)
async def prod_add_full_desc(message: Message, state: FSMContext):
    await state.update_data(full_description=message.text.strip())
    await state.set_state(AdminProductState.waiting_for_image)
    await message.answer("Пришлите ГЛАВНОЕ фото (обложку) товара или '-' чтобы пропустить:")


@router.message(AdminProductState.waiting_for_image)
async def prod_add_image(message: Message, state: FSMContext):
    data = await state.get_data()
    image_id = None
    if message.photo:
        image_id = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        await message.answer("Отправьте именно фото (обложку) или '-' чтобы пропустить")
        return

    async with session_scope() as session:
        product = Product(
            name=data["name"],
            price=data["price"],
            short_description=data.get("short_description"),
            full_description=data.get("full_description"),
            category_id=data.get("category_id"),
            main_image_file_id=image_id,
            is_active=True,
        )
        session.add(product)
        await session.flush()
        await state.update_data(product_id=product.id, extra_count=0)
    # Ask download URL before extra images
    await state.set_state(AdminProductState.waiting_for_download_url)
    await message.answer("Пришлите ссылку для скачивания товара (URL):")


@router.message(AdminProductState.waiting_for_download_url)
async def prod_add_download_url(message: Message, state: FSMContext):
    url = message.text.strip()
    data = await state.get_data()
    pid = data.get("product_id")
    if not pid:
        return await message.answer("Ошибка состояния. Начните заново: /start")
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.download_url = url
            await session.flush()
    # Move to extra images step
    await state.set_state(AdminProductState.waiting_for_extra_images)
    from ...keyboards import finish_extra_kb
    prompt = await message.answer("Пришлите доп. фото (до 4 шт) по одному", reply_markup=finish_extra_kb())
    await state.update_data(prompt_msg_id=prompt.message_id)


@router.callback_query(lambda c: c.data == "admin:prod:list")
async def prod_list(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    async with session_scope() as session:
        res = await session.execute(select(Product).order_by(Product.created_at.desc()))
        products = res.scalars().all()
    if not products:
        await cb.message.edit_text("Список товаров пуст", reply_markup=admin_products_kb())
        return await cb.answer()
    numbered = [(p.id, p.name) for p in products]
    listing = [f"{i}. {name}" for i, (_, name) in enumerate(numbered, start=1)]
    try:
        await cb.message.edit_text("\n".join(["Список товаров:", *listing]), reply_markup=admin_products_list_kb(numbered))
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("\n".join(["Список товаров:", *listing]), reply_markup=admin_products_list_kb(numbered))
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("admin:prod:open:"))
async def prod_open(cb: CallbackQuery):
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
    if not p:
        return await cb.answer("Товар не найден", show_alert=True)
    text = f"<b>{p.name}</b>\nЦена: {p.price} ₽\n\n{p.short_description or p.full_description or ''}"
    if p.main_image_file_id:
        from aiogram.types import InputMediaPhoto
        try:
            await cb.message.edit_media(
                media=InputMediaPhoto(media=p.main_image_file_id, caption=text),
                reply_markup=admin_product_actions_kb(p.id, True),
            )
        except Exception:
            await cb.message.edit_text(text, reply_markup=admin_product_actions_kb(p.id, True))
    else:
        await cb.message.edit_text(text, reply_markup=admin_product_actions_kb(p.id, False))
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("admin:prod:edit:name:"))
async def prod_edit_name(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[-1])
    await state.update_data(pid=pid)
    await state.set_state(AdminProductEditState.editing_name)
    try:
        await cb.message.edit_text("Новое название:")
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("Новое название:")
    await cb.answer()


@router.message(AdminProductEditState.editing_name)
async def prod_edit_name_set(message: Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("pid")
    if not pid:
        await state.clear()
        return await message.answer("Ошибка состояния. /start")
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.name = message.text.strip()
            await session.flush()
    await state.clear()
    return await message.answer("Название обновлено. /start")


@router.callback_query(lambda c: c.data.startswith("admin:prod:edit:price:"))
async def prod_edit_price(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[-1])
    await state.update_data(pid=pid)
    await state.set_state(AdminProductEditState.editing_price)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Бесплатно", callback_data="admin:prod:set_free")]
    ])
    
    try:
        await cb.message.edit_text("Новая цена (или нажмите 'Бесплатно'):", reply_markup=kb)
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("Новая цена (или нажмите 'Бесплатно'):", reply_markup=kb)
    await cb.answer()


@router.callback_query(lambda c: c.data == "admin:prod:set_free", AdminProductEditState.editing_price)
async def prod_set_free_edit(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pid = data.get("pid")
    if not pid:
        await state.clear()
        await cb.answer()
        return
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.price = Decimal("0.00")
            await session.flush()
    await state.clear()
    try:
        await cb.message.edit_text("Цена установлена как бесплатная. /start")
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("Цена установлена как бесплатная. /start")
    await cb.answer()


@router.message(AdminProductEditState.editing_price)
async def prod_edit_price_set(message: Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("pid")
    try:
        price = Decimal(message.text.replace(",", ".").strip())
    except Exception:
        return await message.answer("Неверная цена. Повторите ввод, например 199.99")
    if not pid:
        await state.clear()
        return await message.answer("Ошибка состояния. /start")
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.price = price
            await session.flush()
    await state.clear()
    return await message.answer("Цена обновлена. /start")


@router.callback_query(lambda c: c.data.startswith("admin:prod:edit:desc:"))
async def prod_edit_desc(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[-1])
    await state.update_data(pid=pid)
    await state.set_state(AdminProductEditState.editing_desc)
    try:
        await cb.message.edit_text("Новое описание:")
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("Новое описание:")
    await cb.answer()


@router.message(AdminProductEditState.editing_desc)
async def prod_edit_desc_set(message: Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("pid")
    if not pid:
        await state.clear()
        return await message.answer("Ошибка состояния. /start")
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.short_description = message.text.strip()
            await session.flush()
    await state.clear()
    return await message.answer("Короткое описание обновлено. /start")


@router.callback_query(lambda c: c.data.startswith("admin:prod:edit:photo:"))
async def prod_edit_photo(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[-1])
    await state.update_data(pid=pid)
    await state.set_state(AdminProductEditState.editing_image)
    try:
        await cb.message.edit_text("Пришлите фото:")
    except Exception:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("Пришлите фото:")
    await cb.answer()


@router.message(AdminProductEditState.editing_image)
async def prod_edit_photo_set(message: Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("pid")
    image_id = None
    if message.photo:
        image_id = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        return await message.answer("Отправьте фото или '-' чтобы пропустить")
    if not pid:
        await state.clear()
        return await message.answer("Ошибка состояния. /start")
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            p.main_image_file_id = image_id
            await session.flush()
    await state.clear()
    return await message.answer("Фото обновлено. /start")
    # сюда попадём, если это был сценарий добавления — там уже обработано сохранение


@router.message(AdminProductState.waiting_for_extra_images)
async def prod_add_extra_images(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    count = int(data.get("extra_count", 0))
    prev_prompt_id = data.get("prompt_msg_id")
    if not product_id:
        await state.clear()
        return await message.answer("Сессия добавления прервана. /start")
    # Завершение теперь через кнопку, текст '-' не используем
    if not message.photo:
        return await message.answer("Пришлите доп. фото или нажмите '✅ Завершить добавление'")
    file_id = message.photo[-1].file_id
    # попытаться удалить прошлое сообщение-приглашение, чтобы не осталась клавиатура
    if prev_prompt_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_prompt_id)
        except Exception:
            try:
                await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_prompt_id, reply_markup=None)
            except Exception:
                pass

    async with session_scope() as session:
        await ProductRepo(session).add_extra_image(product_id, file_id)
    count += 1
    if count >= 4:
        await state.clear()
        from ...keyboards import home_kb
        return await message.answer("✅ Товар добавлен (доп. фото добавлены)", reply_markup=home_kb())
    await state.update_data(extra_count=count)
    from ...keyboards import finish_extra_kb
    new_prompt = await message.answer(f"Добавлено: {count}. Пришлите следующее фото", reply_markup=finish_extra_kb())
    await state.update_data(prompt_msg_id=new_prompt.message_id)


@router.callback_query(lambda c: c.data == "admin:prod:extra:done")
async def prod_extra_done(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    from ...keyboards import home_kb
    await cb.message.edit_text("✅ Товар добавлен", reply_markup=home_kb())
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("admin:prod:del:"))
async def prod_delete(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        res = await session.execute(select(Product).where(Product.id == pid))
        p = res.scalar_one_or_none()
        if p:
            await session.delete(p)
    await cb.answer("Удалено")
    await prod_list(cb)


