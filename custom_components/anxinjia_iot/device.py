# device.py
class Device:
    """表示一个智能设备，包含多个虚拟模型。"""

    def __init__(self, data):
        self.house_name = data.get("houseName")
        self.house_uid = data.get("houseUid")
        self.room_name = data.get("roomName")
        self.project_id = data.get("projectId")
        self.eq_number = data.get("eqNumber")
        self.eq_name = data.get("eqName","unknown")
        self.eq_type = data.get("eqType")
        self.model_type = int(data.get("modelType","10000"))
        self.supplier_type = data.get("supplierType")
        self.online = data.get("online")
        self.physics_id = data.get("physicsId")
        self.icon = data.get("icon")
        self.icon_url = data.get("iconUrl")
        self.physics_name = data.get("physicsName","unknown")
        self.user_id = data.get("userId")
        self.create_time = data.get("createTime")
        self.eq_uid = data.get("eqUid")
        self.eq_id = data.get("eqId")
        self.name= f"{self.physics_name}/{self.eq_name}"
        self.virtual_models = data.get("virtualModels", [])
