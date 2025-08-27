from enum import Enum

class FermentationStatus(str, Enum):
    '''Fermentation status progression: ACTIVE -> SLOW -> STUCK -> COMPLETED'''
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DECLINE = "DECLINE"
    LAG = "LAG"
    STUCK = "STUCK"
    SLOW = "SLOW"
