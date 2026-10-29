import unittest
from unittest.mock import patch

from app import AppGrid
from config import LUNA_APPS
from services.detection import AppState, AppStatus


class AppGridTests(unittest.TestCase):
    @patch.object(AppGrid, "icon_data", return_value="icon-data")
    def test_running_app_tile_opens_in_a_new_tab(self, _icon_data):
        card = AppGrid.card(AppStatus(LUNA_APPS[0], AppState.RUNNING))

        self.assertIn('target="_blank"', card)
        self.assertIn('rel="noopener"', card)
        self.assertNotIn('target="_self"', card)


if __name__ == "__main__":
    unittest.main()

