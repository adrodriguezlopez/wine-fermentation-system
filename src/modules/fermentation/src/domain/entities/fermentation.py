from domain.entities.base_entity import (
    BaseEntity,
)
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship


class Fermentation(BaseEntity):
    __tablename__ = "fermentations"

    # Columns
    # Primary identifications
    # id is in the BaseEntity
    # fermented_by_user_id is a Foreign Key referencing the users table
    # (id of the winemaker responsible of the fermentation)
    fermented_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Wine production details
    # vintage_year is the year the wine was produced
    vintage_year = Column(Integer, nullable=False)
    # winery is the name of the winery where the fermentation took place
    winery = Column(String(100), nullable=False)
    # vineyard is the name of the vineyard where the grapes were sourced
    vineyard = Column(String(100), nullable=False)
    # grape_variety is the type of grape used in the fermentation
    grape_variety = Column(String(100), nullable=False)
    # yeast_strain is the type of yeast used in the fermentation
    yeast_strain = Column(String(100), nullable=False)

    # Initial measurements
    # initial_fruit_quantity is the quantity
    # of fruit used for fermentation
    initial_fruit_quantity = Column(Float, nullable=False)
    # initial_sugar_brix is the sugar content of the must
    # at the start of fermentation
    initial_sugar_brix = Column(Float, nullable=False)
    # initial_density is the density of the must at the start of fermentation
    initial_density = Column(Float, nullable=False)

    # Fermentation management
    # status indicates the current state of the fermentation process
    status = Column(String(20), nullable=False, default="ACTIVE")
    # start_date is the date when the fermentation process started
    start_date = Column(DateTime, nullable=False)

    # Relationships
    # A fermentation can have multiple samples taken at different stages
    samples = relationship(
        "Sample", back_populates="fermentation", cascade="all, delete-orphan"
    )
    # A fermentation can have multiple notes associated with it
    notes = relationship(
        "FermentationNote",
        back_populates="fermentation",
        cascade="all, delete-orphan"
    )
