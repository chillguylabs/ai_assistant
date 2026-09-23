from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from inventory import Inventory


app = FastAPI(
    title="Inventory Bridge",
    version="2.0"
)

inventory = Inventory()


# ============================================================
# REQUEST MODELS
# ============================================================

class DeviceRequest(BaseModel):
    device_id: int


class CreateDeviceRequest(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    quantity: float = Field(default=0, ge=0)
    unit: str = "pieces"
    location: Optional[str] = None
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class QuantityRequest(BaseModel):
    device_id: int
    quantity: float
    reason: Optional[str] = None
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class SetQuantityRequest(BaseModel):
    device_id: int
    quantity: float = Field(ge=0)
    reason: Optional[str] = None
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class UpdateDeviceRequest(BaseModel):
    device_id: int
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    reason: str = "Updated through Open WebUI"
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class DescriptionRequest(BaseModel):
    device_id: int
    text: str
    reason: str = "Description updated through Open WebUI"
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class MoveRequest(BaseModel):
    device_id: int
    new_location: str
    reason: str = "Moved through Open WebUI"
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


class DeleteRequest(BaseModel):
    device_id: int
    confirmed: bool = False
    reason: str = "Deleted through Open WebUI"
    source: str = "Open WebUI"
    created_by: str = "Open WebUI"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "service": "Inventory Bridge",
        "version": "2.0",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "success": True,
        "service": "Inventory Bridge",
        "status": "healthy",
    }


# ============================================================
# LIST
# ============================================================

@app.get("/inventory/devices")
def list_devices():

    try:

        devices = inventory.list_devices()

        return {
            "success": True,
            "devices": devices,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SEARCH
# ============================================================

@app.get("/inventory/search")
def search_devices(search: str):

    try:

        devices = inventory.search_devices(search)

        return {
            "success": True,
            "search": search,
            "count": len(devices),
            "devices": devices,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# GET ONE DEVICE
# ============================================================

@app.post("/inventory/device")
def get_device(request: DeviceRequest):

    try:

        device = inventory.get_device(
            request.device_id
        )

        if device is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Device with ID "
                    f"{request.device_id} does not exist."
                ),
            )

        return {
            "success": True,
            "device": device,
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# CREATE
# ============================================================

@app.post("/inventory/create")
def create_device(request: CreateDeviceRequest):

    try:

        device = inventory.create_device(
            name=request.name,
            manufacturer=request.manufacturer,
            model=request.model,
            serial_number=request.serial_number,
            description=request.description,
            quantity=request.quantity,
            unit=request.unit,
            location=request.location,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "CREATE",
            "device": device,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# ADD QUANTITY
# ============================================================

@app.post("/inventory/add")
def add_quantity(request: QuantityRequest):

    try:

        result = inventory.add_quantity(
            device_id=request.device_id,
            quantity=request.quantity,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "ADD",
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SET QUANTITY
#
# IMPORTANT:
#
# "increase drills to 7"
# "set drills to 7"
# "change drills to 7"
#
# all mean SET quantity = 7.
#
# This is NOT ADD 7.
# ============================================================

@app.post("/inventory/set")
def set_quantity(request: SetQuantityRequest):

    try:

        result = inventory.set_quantity(
            device_id=request.device_id,
            quantity=request.quantity,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "SET",
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# REMOVE QUANTITY
# ============================================================

@app.post("/inventory/remove")
def remove_quantity(request: QuantityRequest):

    try:

        result = inventory.remove_quantity(
            device_id=request.device_id,
            quantity=request.quantity,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "REMOVE",
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# UPDATE DEVICE INFORMATION
# ============================================================

@app.put("/inventory/update")
def update_device(request: UpdateDeviceRequest):

    try:

        device = inventory.update_device(
            device_id=request.device_id,
            name=request.name,
            manufacturer=request.manufacturer,
            model=request.model,
            serial_number=request.serial_number,
            description=request.description,
            unit=request.unit,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "UPDATE",
            "device": device,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SMART DESCRIPTION UPDATE
# ============================================================

@app.post("/inventory/description")
def update_description(request: DescriptionRequest):

    try:

        result = inventory.update_description(
            device_id=request.device_id,
            text=request.text,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "DESCRIPTION",
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# MOVE
# ============================================================

@app.post("/inventory/move")
def move_device(request: MoveRequest):

    try:

        device = inventory.move_device(
            device_id=request.device_id,
            new_location=request.new_location,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "MOVE",
            "device": device,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# DELETE
# ============================================================

@app.delete("/inventory/delete")
def delete_device(request: DeleteRequest):

    if not request.confirmed:

        return {
            "success": False,
            "operation": "DELETE",
            "confirmation_required": True,
            "message": (
                "Deletion requires explicit confirmation. "
                "The device has NOT been deleted."
            ),
        }

    try:

        device = inventory.delete_device(
            device_id=request.device_id,
            reason=request.reason,
            source=request.source,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "operation": "DELETE",
            "device": device,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# TRANSACTIONS
# ============================================================

@app.post("/inventory/transactions")
def get_transactions(request: DeviceRequest):

    try:

        transactions = inventory.get_transactions(
            request.device_id
        )

        return {
            "success": True,
            "transactions": transactions,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )