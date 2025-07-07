
import unittest
from unittest.mock import patch, MagicMock
import os

# Set a dummy API key for testing
os.environ["GOOGLE_API_KEY"] = "test_api_key"

from nai.agent import root_agent
from nai.tools import (
    retrieve_user_info_tool,
    save_user_profile_tool,
    update_state_tool,
    retrieve_vacancy_tool,
    retrieve_match_tool,
    retrieve_match_rules_based_tool,
)

class TestRootAgent(unittest.TestCase):
    def test_agent_initialization(self):
        """
        Tests if the root_agent is initialized with the correct parameters.
        """
        self.assertEqual(root_agent.name, "NASC")
        self.assertEqual(root_agent.model, "gemini-2.0-flash")
        self.assertIn("NASC - Assistente Virtual Inteligente do SETASC", root_agent.instruction)

    def test_agent_tools(self):
        """
        Tests if the root_agent is initialized with the correct tools.
        """
        expected_tools = [
            retrieve_user_info_tool,
            save_user_profile_tool,
            update_state_tool,
            retrieve_vacancy_tool,
            retrieve_match_tool,
            retrieve_match_rules_based_tool,
        ]
        self.assertEqual(len(root_agent.tools), len(expected_tools))
        for tool in expected_tools:
            self.assertIn(tool, root_agent.tools)

if __name__ == "__main__":
    unittest.main()
