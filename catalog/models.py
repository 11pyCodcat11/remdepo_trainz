import enum
from sqlalchemy import ForeignKey, Integer, String, Boolean, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .sqlalchemy_base import Base


class Category(str, enum.Enum):
    ROLLING_STOCK = "Подвижной состав"
    MAPS = "Карты"
    SCENARIOS = "Сценарии"
    LINKS = "Полезные ссылки"
    DEPOT = "ДЕПО"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(256), default="")
    price_rub: Mapped[int] = mapped_column(Integer, default=0)  # price in RUB (integer)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[Category] = mapped_column(Enum(Category), index=True)
    badge: Mapped[str] = mapped_column(String(64), default="")
    blurb: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(512), default="")
    popularity: Mapped[int] = mapped_column(Integer, default=0, index=True)

    photos: Mapped[list["ProductPhoto"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )


class ProductPhoto(Base):
    __tablename__ = "product_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)  # путь к файлу
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)        # главное фото
    order: Mapped[int] = mapped_column(Integer, default=0)               # порядок в галерее

    product: Mapped["Product"] = relationship(back_populates="photos")


# ------------------ НОВЫЕ МОДЕЛИ ------------------ #

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)  # хранить хэш
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
    cart: Mapped["Cart"] = relationship(back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    avatar: Mapped[str] = mapped_column(String(256), default="")  # путь к файлу или URL

    user: Mapped["User"] = relationship(back_populates="profile")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    user: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
