"""
TDD tests for AceticAcidSample entity and SampleType.ACETIC_ACID enum value.
RED: All tests fail because neither class nor enum value exist yet.
"""

import pytest
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


class TestSampleTypeAceticAcid:
    def test_acetic_acid_enum_value_exists(self):
        assert SampleType.ACETIC_ACID.value == "acetic_acid"

    def test_sample_type_has_exactly_four_members(self):
        # Guard test: fails if we add a member without updating this count.
        assert len(SampleType) == 4

    def test_acetic_acid_is_string_enum(self):
        assert isinstance(SampleType.ACETIC_ACID, str)


class TestAceticAcidSample:
    def test_default_units_are_grams_per_liter(self):
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )
        from datetime import datetime, timezone

        sample = AceticAcidSample(
            fermentation_id=1,
            recorded_at=datetime.now(timezone.utc),
            recorded_by_user_id=1,
            value=0.5,
        )
        assert sample.units == "g/L"

    def test_polymorphic_identity_is_acetic_acid(self):
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )

        assert AceticAcidSample.__mapper_args__["polymorphic_identity"] == "acetic_acid"

    def test_units_cannot_be_overridden(self):
        """Units are always g/L — the constructor enforces this."""
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )
        from datetime import datetime, timezone

        sample = AceticAcidSample(
            fermentation_id=1,
            recorded_at=datetime.now(timezone.utc),
            recorded_by_user_id=1,
            value=0.7,
            units="wrong_unit",  # should be overwritten
        )
        assert sample.units == "g/L"
