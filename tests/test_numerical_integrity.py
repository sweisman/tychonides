import unittest
from src.core import angle, time_key


class NumericalIntegrityTests(unittest.TestCase):
    def test_words_preserve_sexagesimal_parts_of_a_day(self):
        from src.numeric_integrity import validate_units

        for text, good, bad in [
            ("1½ seconds of a day", {"day_second": "1 1/2"}, {"second": "1 1/2"}),
            ("10 thirds of a day", {"day_third": "10"}, {"time_third": "10"}),
            (
                "15 minutes, 27 seconds, 30 thirds of a day",
                {"day_minute": "15", "day_second": "27", "day_third": "30"},
                {"minute": "15", "second": "27", "time_third": "30"},
            ),
        ]:
            with self.subTest(text=text):
                validate_units(text, good, quantity="clock_elapsed_time")
                with self.assertRaisesRegex(ValueError, "explicit source unit"):
                    validate_units(text, bad, quantity="clock_elapsed_time")

    def test_written_units_bind_each_angle_or_time_component(self):
        from src.numeric_integrity import validate_units

        cases = [
            (
                "hour 1 minute 30",
                "recorded_clock",
                {"hour": "1", "minute": "30"},
                {"hour": "1", "second": "30"},
            ),
            (
                "1 degree 30 minutes",
                "declination",
                {"degree": "1", "arcminute": "30"},
                {"degree": "1", "arcsecond": "30"},
            ),
            (
                "1 hour 30 minutes",
                "recorded_clock",
                {"hour": "1", "minute": "30"},
                {"hour": "1", "second": "30"},
            ),
            (
                "81° 31′ 3⅚ seconds",
                "angular_separation",
                {"degree": "81", "arcminute": "31", "arcsecond": "3 5/6"},
                {"degree": "81", "arcminute": "31", "arcsexagesimal_third": "3 5/6"},
            ),
            ("3/2 arcseconds", "calculation_angle", {"arcsecond": "3/2"}, {"arcminute": "3/2"}),
        ]
        for text, quantity, good, bad in cases:
            with self.subTest(text=text):
                validate_units(text, good, quantity=quantity)
                with self.assertRaisesRegex(ValueError, "explicit source unit"):
                    validate_units(text, bad, quantity=quantity)

    def test_explicit_angular_words_do_not_become_clock_or_native_length_units(self):
        from src.numeric_integrity import validate_units

        for text, quantity, components in [
            ("30 arcseconds", "recorded_clock", {"second": "30"}),
            ("1 degree", "clock_elapsed_time", {"day": "1"}),
            ("30 arcminutes", "distance_in_semidiameters", {"semidiameter_minute": "30"}),
        ]:
            with self.subTest(text=text, quantity=quantity):
                with self.assertRaisesRegex(ValueError, "explicit source unit"):
                    validate_units(text, components, quantity=quantity)

    def test_explicit_hour_prefix_is_required_for_conflicting_prime(self):
        from src.numeric_integrity import validate_units

        text = "10′ 38′ 12″"
        components = dict(hour="10", minute="38", second="12")
        with self.assertRaises(ValueError):
            validate_units(text, components, quantity="transit_clock")
        validate_units(
            text, components, quantity="transit_clock", source_context="H. " + text + ", exactly"
        )

    def test_order_inheritance_and_omitted_intermediate_component(self):
        from src.numeric_integrity import validate_units

        validate_units("1/2″", dict(degree="12", arcsecond="1/2"), inherited=["degree"])
        validate_units("30′ 1°", dict(degree="1", arcminute="30"), order=["arcminute", "degree"])
        with self.assertRaises(ValueError):
            validate_units("30′ 1°", dict(degree="1", arcminute="30"))

    def test_modern_mechanical_edge_cases(self):
        from src.numeric_integrity import recompute_conversion, validate_conversion

        cases = [
            ("00 01 00", "sexagesimal_hour", "900"),
            ("-00 01 00", "sexagesimal_degree", "-60"),
            (" 6 349125", "hhmmss_millisecond", "2619495/8"),
            ("+2521   0", "signed_ddmmss_centisecond", "91260"),
        ]
        for literal, unit, value in cases:
            self.assertEqual(
                recompute_conversion(dict(literal=literal, unit=unit))["magnitude"], value
            )
        row = dict(literal="15 11", unit="sexagesimal_hour", flags=["incomplete_coordinate"])
        validate_conversion(row)
        row["derived_normalization"] = dict(
            magnitude="819900", unit="arcsecond", method="sexagesimal_conversion"
        )
        with self.assertRaises(ValueError):
            validate_conversion(row)
        with self.assertRaises(ValueError):
            recompute_conversion(dict(literal="00 60 00", unit="sexagesimal_hour"))

    def test_complete_fractional_expressions(self):
        self.assertEqual(str(angle("12 1/2° 15′")), "45900")
        self.assertEqual(str(angle("12° 30′ 1/2″")), "90001/2")
        self.assertEqual(time_key("1/2^h^"), "1800")
        self.assertEqual(time_key("1^h^ 30^m^ 1/2^s^"), "10801/2")

    def test_explicit_component_binding(self):
        from src.numeric_integrity import validate_units

        for text, good, bad in (
            ("1° 30′", {"degree": "1", "arcminute": "30"}, {"degree": "1", "arcsecond": "30"}),
            ("1^h^ 30^m^", {"hour": "1", "minute": "30"}, {"hour": "1", "second": "30"}),
        ):
            validate_units(text, good)
            with self.assertRaises(ValueError):
                validate_units(text, bad)

    def test_derived_conversion_is_recomputed(self):
        from src.numeric_integrity import validate_conversion

        row = dict(
            literal="-00 00 12",
            unit="sexagesimal_degree",
            derived_normalization=dict(
                magnitude="-12", unit="arcsecond", method="sexagesimal_conversion"
            ),
        )
        validate_conversion(row)
        row["derived_normalization"]["magnitude"] = "999"
        with self.assertRaises(ValueError):
            validate_conversion(row)
        row = dict(
            literal="23:30",
            unit="clock_expression",
            date="2003-09-17",
            time_scale="EDT",
            derived_normalization=dict(
                timestamp="2003-09-18T03:30:00+00:00",
                method="source_EDT_UTC_minus_4",
                precision="minute",
            ),
        )
        validate_conversion(row)
        row["derived_normalization"]["timestamp"] = "not-a-date"
        with self.assertRaises(ValueError):
            validate_conversion(row)
