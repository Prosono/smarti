from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class SmartiUpdaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smarti Updater."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # When the user submits the form, create the entry
            return self.async_create_entry(title="Smarti Updater", data=user_input)

        # If no input, show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={"name": "Smarti Updater"},
        )