"""Config flow for HelloFresh (UK)."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from pyhellofresh import AuthenticationError, HelloFreshClient, HelloFreshError

from .const import CONF_CUSTOMER_UUID, CONF_EMAIL, CONF_SUBSCRIPTION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class HelloFreshConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HelloFresh (UK)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            try:
                async with HelloFreshClient(email, password) as client:
                    token = await client.authenticate()
                    info = await client.get_customer_info()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except (HelloFreshError, aiohttp.ClientError):
                _LOGGER.exception("Error connecting to HelloFresh")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during HelloFresh setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.uuid)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"{info.first_name} {info.last_name}",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_SUBSCRIPTION_ID: info.active_subscription_id,
                        CONF_CUSTOMER_UUID: info.uuid,
                        "refresh_token": token.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            try:
                async with HelloFreshClient(email, password) as client:
                    token = await client.authenticate()
                    info = await client.get_customer_info()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except (HelloFreshError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during HelloFresh re-auth")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.uuid)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        "refresh_token": token.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
