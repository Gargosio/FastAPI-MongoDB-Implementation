import uvicorn   #####comment when deployed
from fastapi import Depends, FastAPI, HTTPException, status,Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import motor.motor_asyncio
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# import os
# from fastapi import FastAPI, Body, HTTPException, status
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# from pydantic import BaseModel, Field, EmailStrcd
# from bson import ObjectId
# from typing import Optional, List
# import motor.motor_asyncio

app = FastAPI()
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "IOTuser")
    correct_password = secrets.compare_digest(credentials.password, "iot_user@20220406")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

CONNECTION_STRING = ************************************************
client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING)
dbname = client.iotdatadb
# collection_name = dbname.get_collection("iotdatacoll")
# db = client.college


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class SensorModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    device: str = Field(...)
    time: str = Field(...)
    Humidity: float = Field(...)
    Temperature: float = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "device": "devicea",
                "time": "1235678900",
                "Humidity": "56.3",
                "Temperature": "32.0",
            }
        }


class UpdateSensorModel(BaseModel):
    device: Optional[str]
    time: Optional[str]
    Humidity: Optional[float]
    Temperature: Optional[float]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "device": "devicea",
                "time": "1235678900",
                "Humidity": "56.3",
                "Temperature": "32.0",
            }
        }


@app.get(
    "/getsensordata", response_description="List all data", response_model=List[SensorModel]
)
async def RetrieveAll(username= Depends(get_current_username)):
    data = await dbname["iotdatacoll"].find().to_list(1000)
    return data

@app.post("/postsensordata", response_description="Add new data", response_model=SensorModel
          )
async def PostData(data: SensorModel = Body(...),username= Depends(get_current_username)):
    data = jsonable_encoder(data)
    new_data = await dbname["iotdatacoll"].insert_one(data)
    created_data = await dbname["iotdatacoll"].find_one({"_id": new_data.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_data)

# if __name__ == "__main__":
#     uvicorn.run("mongoapi:app", host="127.0.0.1", port=8000, reload=True)
