from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

# Define the options the user can select
UPDATE_OPTIONS = {
    "node_red": "Node-RED Files",
    "dashboards": "Dashboards",
    "automations": "Automations"
}

@config_entries.HANDLERS.register(DOMAIN)
class SmartiUpdaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMARTi."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # When the user submits the form, create the entry with selected options
            return self.async_create_entry(title="SMARTi", data=user_input)

        # If no input, show the form with multi-select options
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("update_types", default=[]): vol.MultipleSelect(
                    options=UPDATE_OPTIONS
                )
            }),
            description_placeholders={"name": "SMARTi"},
        )
