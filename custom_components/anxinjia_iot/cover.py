import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.const import STATE_OPEN, STATE_CLOSED
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass
)
from .const import DOMAIN,CONF_TOKEN
from .api import async_Control_cover

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AnxinJia switches from a config entry."""
    devices = hass.data[DOMAIN]['devices'][config_entry.entry_id]

    # 从 config_entry.data 获取 access_token
    access_token = config_entry.data.get(CONF_TOKEN)

    # 创建实体列表
    new_entities = []
    
    # 遍历设备列表，创建 AnxinJiaSwitch 实例
    for device_info in devices:
        # 替换为适当的属性访问
        if device_info.model_type == 102004:
            for virtual_model in device_info.virtual_models:  # 确保使用正确的属性名称
                entity = AnxinJiaCurtain(device_info, virtual_model, access_token)
                new_entities.append(entity)

    # 异步添加实体到平台
    if new_entities:
        async_add_entities(new_entities, update_before_add=True)
        
class AnxinJiaCurtain(CoverEntity):
    """Representation of a curtain."""

    def __init__(self, device, virtual_model,access_token):
        """Initialize the curtain."""
        self._device = device
        self._name = f"{device.room_name}{virtual_model.get('virtualName')}"  # 使用 Device 类的 name 属性
        self._unique_id = virtual_model.get("virtualNumber")  # 使用 Device 类的 unique_id 属性
        self._model_type = virtual_model.get("modelType")  # 获取设备的模型类型
        self._is_open = False  # True for open, False for closed
        self._access_token = access_token  # 保存访问令牌
        self._attr_device_class = CoverDeviceClass.CURTAIN 
        self._attr_unique_id = self._unique_id  # 确保唯一标识符
        self._attr_name = self._name  # 实体名称
        self._attr_supported_features = CoverEntityFeature(0)
        self._attr_supported_features |= CoverEntityFeature.OPEN
        self._attr_supported_features |= CoverEntityFeature.CLOSE
        self._attr_supported_features |= CoverEntityFeature.STOP
        self._attr_supported_features |= CoverEntityFeature.SET_POSITION
        
        self._prop_position_value_min = 0
        self._prop_position_value_max = 100
        self._prop_position_value_range = 100
        self._prop_current_position = 50
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.eq_number)},  # 设备的唯一标识符
            "name": self._name,  # 设备名称
            "manufacturer": "aciga",  # 制造商
            "model": self._model_type,  # 设备型号
            "sw_version": "v1.0",  # 软件版本
        }
        
    @property
    def name(self):
        """Return the name of the curtain."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the curtain."""
        return self._unique_id

    @property
    def is_opening(self):
        """Return if the cover is opening."""
        return None

    @property
    def is_closing(self):
        """Return if the cover is closing."""
        return None
        
    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return None
        
    @property
    def current_cover_position(self):
        """Return the current position.

        0: the cover is closed, 100: the cover is fully opened, None: unknown.
        """
        pos = self._prop_current_position
        return round(pos*100/self._prop_position_value_range)
 
    async def async_set_cover_position(self, **kwargs) -> None:
        """Set the position of the cover."""
        pos = kwargs.get(ATTR_POSITION, None)
        if pos is None:
            return None
        pos = round(pos*self._prop_position_value_range/100)
        
        try:
            if pos > 50:
                result = await async_Control_cover(self._access_token,self._name,self._unique_id,self._model_type, "open")
            else:
                result = await async_Control_cover(self._access_token,self._name,self._unique_id,self._model_type, "close")
                if result:
                    self._is_open = False
                _LOGGER.info(f"set_cover API 调用成功: {result}")
        except Exception as e:
                _LOGGER.error(f"set_cover API 调用失败: {e}")
            
    async def async_stop_cover(self, **kwargs) -> None:
        """Stop the cover."""
        # 在这里实现停止窗帘的逻辑，例如发送命令到设备
        try:
            # 调用 api.py 中的异步函数
            result = await async_Control_cover(self._access_token,self._name,self._unique_id,self._model_type, "stop")
            # 处理 result，记录日志或更新状态
            if result:
                self._is_open = False
            _LOGGER.info(f"stop_cover API 调用成功: {result}")
        except Exception as e:
            _LOGGER.error(f"stop_cover API 调用失败: {e}")
            
    async def async_open_cover(self, **kwargs):
        """Open the curtain."""
        # 在这里实现打开窗帘的逻辑，例如发送命令到设备
        try:
            # 调用 api.py 中的异步函数
            result = await async_Control_cover(self._access_token,self._name,self._unique_id,self._model_type, "open")
            # 处理 result，记录日志或更新状态
            if result:
                self._is_open = True
            _LOGGER.info(f"open_cover API 调用成功: {result}")
        except Exception as e:
            _LOGGER.error(f"open_cover API 调用失败: {e}")

    async def async_close_cover(self, **kwargs):
        """Close the curtain."""
        # 在这里实现关闭窗帘的逻辑，例如发送命令到设备
        try:
            # 调用 api.py 中的异步函数
            result = await async_Control_cover(self._access_token,self._name,self._unique_id,self._model_type, "close")
            # 处理 result，记录日志或更新状态
            if result:
                self._is_open = False
            _LOGGER.info(f"close_cover API 调用成功: {result}")
        except Exception as e:
            _LOGGER.error(f"close_cover API 调用失败: {e}")
            
    async def async_added_to_hass(self):
        """Called when the entity is added to hass for initialization or state update."""
        #self._attr_icon = "mdi:curtains"
        #await self.async_update()  # 默认调用一次更新
        pass