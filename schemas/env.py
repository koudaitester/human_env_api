from pydantic import BaseModel, Field, field_validator
from utils.validator import validate_range

class EnvDataCreate(BaseModel):
    temp: float = Field(..., description="温度℃")
    hum: float = Field(..., description="相对湿度%")
    pm25: float | None = Field(default=None, description="PM2.5")

    @field_validator("temp")
    def check_temp(cls, v):
        return validate_range(v, -20, 60) # 合理温度区间
    
    @field_validator("hum")
    def check_hum(cls, v):
        return validate_range(v, 0, 100) # 湿度0~100
