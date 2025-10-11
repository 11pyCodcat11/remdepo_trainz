from aiogram.fsm.state import State, StatesGroup


class ChangePasswordState(StatesGroup):
    waiting_for_old = State()
    waiting_for_new = State()


class ChangeLoginState(StatesGroup):
    waiting_for_login = State()


class AuthRegisterState(StatesGroup):
    waiting_for_login = State()
    waiting_for_email = State()
    waiting_for_password = State()


class AuthLoginState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()


class AdminProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_desc = State()
    waiting_for_full_desc = State()
    waiting_for_image = State()
    waiting_for_download_url = State()
    waiting_for_extra_images = State()


class AdminProductEditState(StatesGroup):
    editing_name = State()
    editing_price = State()
    editing_desc = State()
    editing_image = State()


class AdminCategoryState(StatesGroup):
    waiting_for_name = State()


