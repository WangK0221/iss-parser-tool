import unittest
from types import SimpleNamespace

from services.data_mapper import (
    build_feeder_device_display,
    build_feeder_display,
    build_feeder_interval_display,
)


def make_component(*, package: str, reel_type_id: str, pitch: str, count: str):
    return SimpleNamespace(
        component_name="TEST",
        extra={
            "package": package,
            "feeder.reelTypeId": reel_type_id,
            "feederPitch.pitch": pitch,
            "feederPitch.count": count,
        },
    )


def make_feeder(*, feeder_type: str = "", supply_unit_type: str = ""):
    return SimpleNamespace(
        feeder_type=feeder_type,
        bank_kind="1",
        extra={"supplyUnit.type": supply_unit_type},
    )


class FeederMappingTests(unittest.TestCase):
    def test_interval_variants_keep_known_device_family(self):
        cases = [
            ("21", "10", "2", "32mm 胶带", "20mm(10*2)", "32mm 胶带 20mm(10*2)"),
            ("27", "12", "1", "44mm 胶带", "12mm(12*1)", "44mm 胶带 12mm(12*1)"),
            ("40", "14", "2", "56mm 胶带", "28mm(14*2)", "56mm 胶带 28mm(14*2)"),
            ("52", "14", "2", "72mm 胶带", "28mm(14*2)", "72mm 胶带 28mm(14*2)"),
        ]
        for reel_type_id, pitch, count, expected_device, expected_interval, expected_display in cases:
            with self.subTest(reel_type_id=reel_type_id, pitch=pitch, count=count):
                component = make_component(
                    package="TAPE",
                    reel_type_id=reel_type_id,
                    pitch=pitch,
                    count=count,
                )
                feeder = make_feeder(feeder_type="9")
                self.assertEqual(build_feeder_device_display(component, feeder), expected_device)
                self.assertEqual(build_feeder_interval_display(component), expected_interval)
                self.assertEqual(build_feeder_display(component, feeder), expected_display)

    def test_12_16_24mm_family_samples_from_full_mapping_file(self):
        cases = [
            ("6", "4", "1", "12mm 胶带", "12mm 胶带 4mm(4*1)"),
            ("7", "8", "1", "12mm 胶带", "12mm 胶带 8mm(8*1)"),
            ("8", "12", "1", "12mm 胶带", "12mm 胶带 12mm(12*1)"),
            ("9", "4", "1", "16mm 胶带", "16mm 胶带 4mm(4*1)"),
            ("12", "8", "2", "16mm 胶带", "16mm 胶带 16mm(8*2)"),
            ("10", "8", "1", "16mm 胶带", "16mm 胶带 8mm(8*1)"),
            ("11", "6", "2", "16mm 胶带", "16mm 胶带 12mm(6*2)"),
            ("13", "8", "1", "24mm 胶带", "24mm 胶带 8mm(8*1)"),
            ("14", "12", "1", "24mm 胶带", "24mm 胶带 12mm(12*1)"),
            ("15", "8", "2", "24mm 胶带", "24mm 胶带 16mm(8*2)"),
            ("16", "10", "2", "24mm 胶带", "24mm 胶带 20mm(10*2)"),
            ("17", "12", "2", "24mm 胶带", "24mm 胶带 24mm(12*2)"),
            ("18", "8", "1", "24mm 胶带", "24mm 胶带 8mm(8*1)"),
        ]
        for reel_type_id, pitch, count, expected_device, expected_display in cases:
            with self.subTest(reel_type_id=reel_type_id, pitch=pitch, count=count):
                component = make_component(
                    package="TAPE",
                    reel_type_id=reel_type_id,
                    pitch=pitch,
                    count=count,
                )
                feeder = make_feeder(feeder_type="5")
                self.assertEqual(build_feeder_device_display(component, feeder), expected_device)
                self.assertEqual(build_feeder_display(component, feeder), expected_display)

    def test_32_44_56_72_88mm_family_samples_from_full_mapping_files(self):
        cases = [
            ("22", "8", "3", "32mm 胶带", "32mm 胶带 24mm(8*3)"),
            ("23", "14", "2", "32mm 胶带", "32mm 胶带 28mm(14*2)"),
            ("24", "16", "2", "32mm 胶带", "32mm 胶带 32mm(16*2)"),
            ("25", "3", "4", "32mm 胶带", "32mm 胶带 12mm(3*4)"),
            ("26", "8", "1", "32mm 胶带", "32mm 胶带 8mm(8*1)"),
            ("28", "16", "1", "44mm 胶带", "44mm 胶带 16mm(16*1)"),
            ("31", "14", "2", "44mm 胶带", "44mm 胶带 28mm(14*2)"),
            ("32", "16", "2", "44mm 胶带", "44mm 胶带 32mm(16*2)"),
            ("34", "20", "2", "44mm 胶带", "44mm 胶带 40mm(20*2)"),
            ("35", "22", "2", "44mm 胶带", "44mm 胶带 44mm(22*2)"),
            ("36", "12", "1", "56mm 胶带", "56mm 胶带 12mm(12*1)"),
            ("37", "16", "1", "56mm 胶带", "56mm 胶带 16mm(16*1)"),
            ("38", "20", "1", "56mm 胶带", "56mm 胶带 20mm(20*1)"),
            ("41", "16", "2", "56mm 胶带", "56mm 胶带 32mm(16*2)"),
            ("42", "18", "2", "56mm 胶带", "56mm 胶带 36mm(18*2)"),
            ("43", "20", "2", "56mm 胶带", "56mm 胶带 40mm(20*2)"),
            ("44", "22", "2", "56mm 胶带", "56mm 胶带 44mm(22*2)"),
            ("45", "16", "3", "56mm 胶带", "56mm 胶带 48mm(16*3)"),
            ("46", "13", "4", "56mm 胶带", "56mm 胶带 52mm(13*4)"),
            ("47", "14", "4", "56mm 胶带", "56mm 胶带 56mm(14*4)"),
            ("48", "12", "1", "72mm 胶带", "72mm 胶带 12mm(12*1)"),
            ("49", "16", "1", "72mm 胶带", "72mm 胶带 16mm(16*1)"),
            ("51", "12", "2", "72mm 胶带", "72mm 胶带 24mm(12*2)"),
            ("53", "16", "2", "72mm 胶带", "72mm 胶带 32mm(16*2)"),
            ("54", "18", "2", "72mm 胶带", "72mm 胶带 36mm(18*2)"),
            ("55", "20", "2", "72mm 胶带", "72mm 胶带 40mm(20*2)"),
            ("56", "22", "2", "72mm 胶带", "72mm 胶带 44mm(22*2)"),
            ("57", "16", "3", "72mm 胶带", "72mm 胶带 48mm(16*3)"),
            ("58", "13", "4", "72mm 胶带", "72mm 胶带 52mm(13*4)"),
            ("59", "14", "4", "72mm 胶带", "72mm 胶带 56mm(14*4)"),
            ("74", "8", "1", "72mm 胶带", "72mm 胶带 8mm(8*1)"),
            ("81", "20", "1", "88mm 胶带", "88mm 胶带 20mm(20*1)"),
            ("82", "12", "2", "88mm 胶带", "88mm 胶带 24mm(12*2)"),
            ("83", "14", "2", "88mm 胶带", "88mm 胶带 28mm(14*2)"),
        ]
        for reel_type_id, pitch, count, expected_device, expected_display in cases:
            with self.subTest(reel_type_id=reel_type_id, pitch=pitch, count=count):
                component = make_component(
                    package="TAPE",
                    reel_type_id=reel_type_id,
                    pitch=pitch,
                    count=count,
                )
                feeder = make_feeder(feeder_type="9")
                self.assertEqual(build_feeder_device_display(component, feeder), expected_device)
                self.assertEqual(build_feeder_display(component, feeder), expected_display)

    def test_tray_prefers_direct_supply_unit_type(self):
        component = make_component(package="TRAY", reel_type_id="", pitch="", count="")
        feeder = make_feeder(supply_unit_type="TR5S")
        self.assertEqual(build_feeder_device_display(component, feeder), "TR5S")
        self.assertEqual(build_feeder_display(component, feeder), "TR5S")


if __name__ == "__main__":
    unittest.main()
