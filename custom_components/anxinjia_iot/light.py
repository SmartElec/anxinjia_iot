import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.light import LightEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_TOKEN
from .api import async_Control_switch, async_get_all_devices_status

_LOGGER = logging.getLogger(__name__)

class AnxinJiaLight(LightEntity):
    def __init__(self, device, virtual_model, access_token):
        self._device = device
        self._name = f"{virtual_model.get('virtualName')}"  # 使用 Device 类的 name 属性
        self._unique_id = virtual_model.get("virtualNumber")  # 使用 Device 类的 unique_id 属性
        self._model_type = virtual_model.get("modelType")  # 获取设备的模型类型
        self._state = False  # 默认状态
        self._access_token = access_token  # 保存访问令牌
        self._attr_unique_id = self._unique_id  # 确保唯一标识符
        self._attr_name = self._name  # 实体名称
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.eq_number)},  # 设备的唯一标识符
            "name": self._name,  # 设备名称
            "manufacturer": "aciga",  # 制造商
            "model": self._model_type,  # 设备型号
            "sw_version": "v1.0",  # 软件版本
        }

    @property
    def is_on(self):
        return self._state
        
    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        try:
            # 调用 api.py 中的异步函数
            result = await async_Control_switch(self._access_token, self._name, self._unique_id, self._model_type, True)
            if result:
                self._state = True
                _LOGGER.debug("灯已打开")
            _LOGGER.info(f"light on API 调用成功: {result}")
        except Exception as e:
            _LOGGER.error(f"light on API 调用失败: {e}")

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        try:
            # 调用 api.py 中的异步函数
            result = await async_Control_switch(self._access_token, self._name, self._unique_id, self._model_type, False)
            if result:
                self._state = False
                _LOGGER.debug("灯已关闭")
            _LOGGER.info(f"light off API 调用成功: {result}")
        except Exception as e:
            _LOGGER.error(f"light off API 调用失败: {e}")

    async def async_added_to_hass(self):
        """Entity is added to Home Assistant."""
        self._attr_icon = "mdi:lightbulb"  # 设置灯的图标
        await super().async_added_to_hass()
        _LOGGER.debug(f"灯实体已添加到 hass: {self.hass}")

    async def async_update(self):
        """Update the device state (e.g., call status query API)."""
        # 这里实现查询设备状态的逻辑
        pass

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AnxinJia lights from a config entry."""
    devices = hass.data[DOMAIN]['devices'][config_entry.entry_id]

    # 从 config_entry.data 获取 access_token
    access_token = config_entry.data.get(CONF_TOKEN)

    # 提取 model_type 为 102001 的设备的 eqNumber
    eq_numbers = [
        device.eq_number 
        for device in devices 
        if device.model_type == 102001
    ]
    
    # 创建实体列表
    new_entities = []
    
    # 遍历设备列表，创建 AnxinJiaLight 实例
    for device_info in devices:
        if device_info.model_type == 102001:
            for virtual_model in device_info.virtual_models:
                entity = AnxinJiaLight(device_info, virtual_model, access_token)
                new_entities.append(entity)

    # 异步添加实体到平台
    if new_entities:
        async_add_entities(new_entities, update_before_add=True)
        
    # 添加全局定时器以更新所有设备状态
    async def device_update_timer(now):
        await async_update_devices(hass, access_token, eq_numbers, new_entities)

    async_track_time_interval(hass, device_update_timer, timedelta(seconds=300))
