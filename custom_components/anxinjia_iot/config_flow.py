'''
Description: file content
Version: 2.0
Autor: miaoguoqiang
Date: 2025-02-27 16:37:41
LastEditors: miaoguoqiang
LastEditTime: 2025-03-16 11:56:57
'''
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import translation
from .const import DOMAIN,CONF_USER_ID,CONF_TOKEN
from .api import async_login_auth2,getUserDetailById

# 创建 logger 实例
_LOGGER = logging.getLogger(__name__)

class AnxinJiaControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AnxinJia Control."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self):
        super().__init__()
        self.config_entry_id = None  # 这里初始化 config_entry_id
        
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self._get_schema())
        
        entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        # 使用 .get() 方法以避免 KeyError
        username = user_input.get(CONF_USERNAME)
        password = user_input.get(CONF_PASSWORD)
        userid_input = user_input.get(CONF_USER_ID)
        token_input = user_input.get(CONF_TOKEN)

        # 检查 username 和 password
        if username and password:
            access_token_data = await async_login_auth2(username, password)
            if access_token_data:
                new_token = access_token_data.get("accessToken")
                user_id = access_token_data.get("customerId")
                customerName = access_token_data.get("customerName")
                combined_title = f"{customerName}:{username}"
 
                return self.async_create_entry(title=combined_title, data={
                    CONF_USER_ID: user_id,
                    CONF_TOKEN: new_token
                })
            else:
                return await self.async_show_error_form("invalid_credentials")

        # 检查 userid 和 token
        if userid_input and token_input:
            userinfo = await getUserDetailById(token_input,userid_input)
            if userinfo:
                userNickname = userinfo.get("userNickname")
                userPhone = userinfo.get("userPhone")
                combined_title = f"{userNickname}:{userPhone}"

                return self.async_create_entry(title=combined_title, data={
                    CONF_USER_ID: userid_input,
                    CONF_TOKEN: token_input
                })
            else:
                return await self.async_show_error_form("invalid_token")

        # 检查输入的有效性
        if (username and not password) or (password and not username):
            return await self.async_show_error_form("username_password_required")

        if (userid_input and not token_input) or (token_input and not userid_input):
            return await self.async_show_error_form("userid_token_required")

        # 如果输入无效，显示错误
        return await self.async_show_error_form("credentials_required")
    
    async def async_step_reconfigure(self, user_input=None):
        """Step to handle reauthorization."""
        if user_input is None:
            return self.async_show_form(step_id="reconfigure", data_schema=self._get_schema())

        current_entry = self.hass.config_entries.async_get_entry(self.unique_id)
        # 重新获取访问令牌的逻辑
        username = user_input.get(CONF_USERNAME)
        password = user_input.get(CONF_PASSWORD)
        userid_input = user_input.get(CONF_USER_ID)
        token_input = user_input.get(CONF_TOKEN)

        if username and password:
            access_token_data = await async_login_auth2(username, password)
            if access_token_data:
                new_token = access_token_data.get("accessToken")
                user_id = access_token_data.get("customerId")
                customerName = access_token_data.get("customerName")
                combined_title = f"{customerName}:{username}"
                
                await self.hass.config_entries.async_update_entry(current_entry,data={
                    CONF_USER_ID: user_id,
                    CONF_TOKEN: new_token
                })
                return self.async_abort(reason="Configuration updated")
            else:
                return await self.async_show_error_form("invalid_credentials",step_id="reconfigure")

        # 检查 userid 和 token
        if userid_input and token_input:
            userinfo = await getUserDetailById(token_input,userid_input)
            if userinfo:
                userNickname = userinfo.get("userNickname")
                userPhone = userinfo.get("userPhone")
                combined_title = f"{userNickname}:{userPhone}"
                
                await self.hass.config_entries.async_update_entry(current_entry, data={
                    CONF_USER_ID: userid_input,
                    CONF_TOKEN: token_input
                })
                return self.async_abort(reason="Configuration updated")
            else:
                return await self.async_show_error_form("invalid_token",step_id="reconfigure")
                
        return await self.async_show_error_form("invalid_credentials",step_id="reconfigure")        
        
    async def async_show_error_form(self, error_type,step_id="user"):
        """Show error form when configuration fails."""
        errors = {}
        if error_type == "invalid_credentials":
            errors["base"] = translation.async_get_translation(
                self.hass,
                DOMAIN,
                "invalid_credentials"  # 在 translations/zh.json/en.json 中定义
            )
        elif error_type == "invalid_token":
            errors["base"] = translation.async_get_translation(
                self.hass,
                DOMAIN,
                "invalid_token"  # 在 translations/zh.json/en.json 中定义
            )
        elif error_type == "username_password_required":
            errors["base"] = translation.async_get_translation(
                self.hass,
                DOMAIN,
                "username_password_required"  # 在 translations/zh.json/en.json 中定义
            )
        elif error_type == "userid_token_required":
            errors["base"] = translation.async_get_translation(
                self.hass,
                DOMAIN,
                "userid_token_required"  # 在 translations/zh.json/en.json 中定义
            )
        else:
            errors["base"] = translation.async_get_translation(
                self.hass,
                DOMAIN,
                "credentials_required"  # 在 translations/zh.json/en.json 中定义
            )

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._get_schema(),
            errors=errors
        )

    def _get_schema(self):
        """Create the schema for the user input."""
        return vol.Schema({
            vol.Optional(CONF_USERNAME, default=""): str,
            vol.Optional(CONF_PASSWORD, default=""): str,
            vol.Optional(CONF_USER_ID, default=""): str,
            vol.Optional(CONF_TOKEN, default=""): str,
        })
