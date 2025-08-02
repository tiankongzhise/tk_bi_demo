from tk_db_utils import DbOrmBaseMixedIn
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, JSON, VARCHAR,UniqueConstraint

class OauthInfoTable(DbOrmBaseMixedIn):
    __tablename__ = "oauth_info"
    id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)
    controler_id: Mapped[str] = mapped_column(VARCHAR(20))
    controler_name: Mapped[str] = mapped_column(VARCHAR(10))
    channel: Mapped[str] = mapped_column(VARCHAR(10))
    oauth_info: Mapped[dict] = mapped_column(JSON)
    
    __table_args__ = (
        UniqueConstraint("controler_name", "channel", name="uix_controler_name_channel"),
        UniqueConstraint("controler_id", "channel", name="uix_controler_id_channel"),
        {"schema": "oauth_db"},
    )
