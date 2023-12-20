from sqlalchemy import String, Integer, Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Handphone(Base):
    __tablename__ = "tbl_handphone"
    id = Column(Integer, primary_key=True)
    nama_handphone = Column(String(50))
    ram = Column(Integer)
    memori_internal = Column(Integer)
    processor = Column(Integer)
    layar = Column(Integer)
    harga = Column(Integer)
    baterai = Column(String(50))


    def __repr__(self):
        return f"Handphone(id={self.id!r}, nama_handphone={self.nama_handphone!r}, ram={self.ram!r}, memori_internal={self.memori_internal!r}, processor={self.processor!r}, harga={self.harga!r}, baterai={self.baterai!r})"