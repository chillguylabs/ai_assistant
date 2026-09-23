import requests


class Tools:
    """
    Open WebUI inventory tools.

    IMPORTANT SEMANTICS:

    ADD
        Adds a number to the current quantity.

        Example:
            "add 3 drills"
            4 -> 7

    SET
        Changes the quantity TO the requested number.

        Example:
            "increase the number of drills to 7"
            4 -> 7

        This does NOT mean:
            4 + 7 = 11

    CREATE
        Creates a new inventory database entry.

        Example:
            "create a screwdriver"

    ADD NEW ITEM
        inventory_add can also create an item if it does not
        already exist. This is useful for:

            "I found a screwdriver, add it to inventory."

        In that case the tool creates:

            screwdriver
            quantity = 1
    """

    BASE_URL = "http://192.168.1.107:8000"

    # ============================================================
    # HTTP HELPERS
    # ============================================================

    def _get(self, path, **kwargs):

        return requests.get(
            f"{self.BASE_URL}{path}",
            timeout=10,
            **kwargs,
        )

    def _post(self, path, **kwargs):

        return requests.post(
            f"{self.BASE_URL}{path}",
            timeout=10,
            **kwargs,
        )

    def _put(self, path, **kwargs):

        return requests.put(
            f"{self.BASE_URL}{path}",
            timeout=10,
            **kwargs,
        )

    def _delete(self, path, **kwargs):

        return requests.delete(
            f"{self.BASE_URL}{path}",
            timeout=10,
            **kwargs,
        )

    # ============================================================
    # FORMAT DEVICE
    # ============================================================

    def _format_device(self, device):

        if not device:

            return "No device information available."

        return (
            f"ID: {device.get('id')}\n"
            f"Name: {device.get('name')}\n"
            f"Manufacturer: {device.get('manufacturer')}\n"
            f"Model: {device.get('model')}\n"
            f"Serial number: {device.get('serial_number')}\n"
            f"Description: {device.get('description')}\n"
            f"Quantity: {device.get('quantity')} "
            f"{device.get('unit')}\n"
            f"Location: {device.get('location')}"
        )

    # ============================================================
    # FORMAT QUANTITY RESULT
    # ============================================================

    def _format_quantity_result(
        self,
        result,
        device=None,
    ):

        operation = result.get(
            "operation",
            "UNKNOWN",
        )

        previous = result.get("previous_quantity")

        new = result.get("new_quantity")

        changed = result.get(
            "changed",
            False,
        )

        device_id = result.get("device_id")

        if device:
            device_name = device.get("name")
        else:
            device_name = "Unknown"

        if changed:

            if operation == "SET":

                return (
                    "SUCCESS: Inventory quantity changed.\n"
                    f"Device: {device_name}\n"
                    f"Device ID: {device_id}\n"
                    f"Previous quantity: {previous}\n"
                    f"New quantity: {new}\n"
                    f"Quantity change: {previous} -> {new}\n"
                    "Operation: SET\n"
                    "\n"
                    "IMPORTANT: The quantity was changed during "
                    "this operation. The 'Previous quantity' is "
                    "the value BEFORE the operation."
                )

            if operation == "ADD":

                return (
                    "SUCCESS: Inventory quantity increased.\n"
                    f"Device: {device_name}\n"
                    f"Device ID: {device_id}\n"
                    f"Previous quantity: {previous}\n"
                    f"New quantity: {new}\n"
                    f"Quantity change: {previous} -> {new}\n"
                    "Operation: ADD\n"
                    "\n"
                    "IMPORTANT: The quantity was changed during "
                    "this operation."
                )

            if operation == "REMOVE":

                return (
                    "SUCCESS: Inventory quantity decreased.\n"
                    f"Device: {device_name}\n"
                    f"Device ID: {device_id}\n"
                    f"Previous quantity: {previous}\n"
                    f"New quantity: {new}\n"
                    f"Quantity change: {previous} -> {new}\n"
                    "Operation: REMOVE\n"
                )

        return (
            "NO CHANGE: Inventory quantity was already at "
            f"{new}.\n"
            f"Device: {device_name}\n"
            f"Device ID: {device_id}\n"
            f"Previous quantity: {previous}\n"
            f"New quantity: {new}\n"
            "Operation: SET\n"
            "\n"
            "IMPORTANT: No database quantity change occurred."
        )

    # ============================================================
    # GET DEVICE BY ID
    # ============================================================

    def _get_device_by_id(
        self,
        device_id,
    ):

        try:

            response = self._post(
                "/inventory/device",
                json={"device_id": int(device_id)},
            )

            if response.status_code == 404:

                return (
                    None,
                    f"Device with ID {device_id} " f"does not exist.",
                )

            if response.status_code != 200:

                return (
                    None,
                    "Inventory lookup failed: "
                    f"HTTP {response.status_code}: "
                    f"{response.text}",
                )

            data = response.json()

            device = data.get("device")

            if not device:

                return (
                    None,
                    f"Device with ID {device_id} " f"was not found.",
                )

            return (
                device,
                None,
            )

        except requests.RequestException as error:

            return (
                None,
                f"Inventory API request failed: {error}",
            )

        except Exception as error:

            return (
                None,
                f"Inventory lookup failed: {error}",
            )

    # ============================================================
    # FIND DEVICE
    # ============================================================

    def _find_device(
        self,
        search: str,
    ):

        if search is None:

            return (
                None,
                "No device name or ID was provided.",
            )

        search = str(search).strip()

        if not search:

            return (
                None,
                "No device name or ID was provided.",
            )

        normalized = search.casefold()

        prefixes = [
            "device id ",
            "device ",
            "id ",
        ]

        for prefix in prefixes:

            if normalized.startswith(prefix):

                possible_id = search[len(prefix) :].strip()

                if possible_id.isdigit():

                    return self._get_device_by_id(int(possible_id))

        if search.isdigit():

            return self._get_device_by_id(int(search))

        try:

            response = self._get(
                "/inventory/search",
                params={"search": search},
            )

            if response.status_code != 200:

                return (
                    None,
                    "Inventory search failed: "
                    f"HTTP {response.status_code}: "
                    f"{response.text}",
                )

            data = response.json()

            devices = data.get("devices", [])

            if not devices:

                return (
                    None,
                    f"No inventory item found " f"for '{search}'.",
                )

            # The backend prioritizes exact name matches.
            exact_matches = [
                device
                for device in devices
                if str(device.get("name", "")).casefold() == search.casefold()
            ]

            if len(exact_matches) == 1:

                return (
                    exact_matches[0],
                    None,
                )

            if len(devices) == 1:

                return (
                    devices[0],
                    None,
                )

            matches = []

            for device in devices:

                matches.append(
                    f"ID {device.get('id')}: "
                    f"{device.get('name')} "
                    f"({device.get('manufacturer') or ''} "
                    f"{device.get('model') or ''})"
                )

            return (
                None,
                "Multiple inventory devices matched "
                f"'{search}':\n" + "\n".join(matches) + "\n"
                "Please specify the exact device name or ID.",
            )

        except requests.RequestException as error:

            return (
                None,
                f"Inventory search failed: {error}",
            )

        except Exception as error:

            return (
                None,
                f"Inventory search failed: {error}",
            )

    # ============================================================
    # SEARCH
    # ============================================================

    def inventory_search(
        self,
        search: str,
    ) -> str:
        """
        Search the inventory.

        Use this when the user asks whether an item exists,
        asks what equipment is available, or wants to find
        an inventory item.

        Do NOT use this as a substitute for CREATE.
        """

        if not search or not search.strip():

            return "ERROR: Search term is required."

        try:

            response = self._get(
                "/inventory/search",
                params={"search": search.strip()},
            )

            if response.status_code != 200:

                return (
                    "ERROR: Inventory search failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            devices = data.get("devices", [])

            if not devices:

                return f"No inventory items found " f"for '{search}'."

            return "\n\n".join(self._format_device(device) for device in devices)

        except Exception as error:

            return "ERROR: Inventory search failed: " f"{error}"

    # ============================================================
    # GET
    # ============================================================

    def inventory_get(
        self,
        search: str,
    ) -> str:
        """
        Get one specific inventory item.

        The search can be a name or numeric ID.
        """

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        return self._format_device(device)

    # ============================================================
    # LIST
    # ============================================================

    def inventory_list(self) -> str:
        """
        List all inventory devices.
        """

        try:

            response = self._get("/inventory/devices")

            if response.status_code != 200:

                return (
                    "ERROR: Could not retrieve inventory.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            devices = data.get("devices", [])

            if not devices:

                return "The inventory is empty."

            return "\n\n".join(self._format_device(device) for device in devices)

        except Exception as error:

            return "ERROR: Inventory list failed: " f"{error}"

    # ============================================================
    # CREATE
    # ============================================================

    def inventory_create(
        self,
        name: str,
        manufacturer: str = "",
        model: str = "",
        serial_number: str = "",
        description: str = "",
        quantity: float = 0,
        unit: str = "pieces",
        location: str = "",
    ) -> str:
        """
        CREATE A NEW INVENTORY DATABASE ENTRY.

        Use this when the user explicitly wants a new item
        created.

        Examples:

            "create a new screwdriver"
            "create a new drill"
            "add a new item called screwdriver"

        This creates a database row.

        It does NOT modify an existing item's quantity.
        """

        if not name or not name.strip():

            return "ERROR: Device name is required."

        try:

            quantity = float(quantity)

        except (
            TypeError,
            ValueError,
        ):

            return "ERROR: Quantity must be a number."

        if quantity < 0:

            return "ERROR: Quantity cannot be negative."

        payload = {
            "name": name.strip(),
            "manufacturer": (manufacturer.strip() if manufacturer else None),
            "model": (model.strip() if model else None),
            "serial_number": (serial_number.strip() if serial_number else None),
            "description": (description.strip() if description else None),
            "quantity": quantity,
            "unit": (unit.strip() if unit else "pieces"),
            "location": (location.strip() if location else None),
            "source": "Open WebUI",
            "created_by": "Open WebUI",
        }

        try:

            response = self._post(
                "/inventory/create",
                json=payload,
            )

            if response.status_code != 200:

                return (
                    "ERROR: Device creation failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Device creation failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            device = data.get("device", {})

            return (
                "SUCCESS: New inventory entry created.\n"
                "Operation: CREATE\n\n" + self._format_device(device)
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # ADD
    # ============================================================

    def inventory_add(
        self,
        search: str,
        quantity: float = 1,
        reason: str = "Added through Open WebUI",
    ) -> str:
        """
        ADD inventory quantity.

        IMPORTANT:

        "add 3 drills"
            means ADD 3 to the existing quantity.

        "we found another drill"
            means ADD 1.

        "add this screwdriver to the inventory"
            if the screwdriver does NOT exist, CREATE a new
            screwdriver entry with quantity 1.

        If the item already exists, this tool increases its
        quantity. It does NOT set the quantity.

        For phrases such as:

            "increase drills to 7"
            "set drills to 7"
            "change drills to 7"

        DO NOT use this tool.

        Use inventory_set instead.
        """

        if not search or not search.strip():

            return "ERROR: Item name is required."

        try:

            quantity = float(quantity)

        except (
            TypeError,
            ValueError,
        ):

            return "ERROR: Quantity must be a number."

        if quantity <= 0:

            return "ERROR: Quantity must be " "greater than zero."

        device, error = self._find_device(search)

        # ========================================================
        # ITEM DOES NOT EXIST
        #
        # For ADD, create a new item.
        # ========================================================

        if device is None:

            if error and not error.startswith("No inventory item found"):

                return f"ERROR: {error}"

            try:

                response = self._post(
                    "/inventory/create",
                    json={
                        "name": search.strip(),
                        "quantity": quantity,
                        "unit": "pieces",
                        "location": None,
                        "source": "Open WebUI",
                        "created_by": "Open WebUI",
                    },
                )

                if response.status_code != 200:

                    return (
                        "ERROR: Item did not exist and "
                        "automatic creation failed.\n"
                        f"HTTP {response.status_code}\n"
                        f"{response.text}"
                    )

                data = response.json()

                if not data.get("success"):

                    return (
                        "ERROR: Item did not exist and "
                        "automatic creation failed.\n"
                        + str(
                            data.get(
                                "message",
                                data.get(
                                    "detail",
                                    "Unknown error",
                                ),
                            )
                        )
                    )

                created_device = data.get("device", {})

                return (
                    "SUCCESS: New inventory item created.\n"
                    "Operation: CREATE\n"
                    f"Reason: {reason}\n"
                    f"Initial quantity: {quantity}\n\n"
                    + self._format_device(created_device)
                )

            except Exception as error:

                return "ERROR: Automatic item creation " "failed: " f"{error}"

        # ========================================================
        # EXISTING ITEM
        # ========================================================

        try:

            response = self._post(
                "/inventory/add",
                json={
                    "device_id": int(device["id"]),
                    "quantity": quantity,
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Inventory addition failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Inventory addition failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            data["operation"] = "ADD"

            return self._format_quantity_result(
                data,
                device,
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # SET
    # ============================================================

    def inventory_set(
        self,
        search: str,
        quantity: float,
        reason: str = "Quantity set through Open WebUI",
    ) -> str:
        """
        SET inventory quantity to an exact value.

        THIS TOOL IS FOR TARGET QUANTITIES.

        Examples:

            "increase the number of drills to four"
                current 3 -> 4

            "increase the drills to seven"
                current 4 -> 7

            "set the drill quantity to 7"
                current 4 -> 7

            "change the number of drills to 10"
                current 7 -> 10

        The number after "to" is the FINAL quantity.

        DO NOT add that number to the current quantity.

        Therefore:

            current = 3
            request = "increase to 4"

            result = 4

        NOT:

            3 + 4 = 7

        The tool response explicitly reports:

            Previous quantity
            New quantity
            Quantity change
            Operation: SET

        If the quantity is already the requested value,
        the tool returns NO CHANGE.
        """

        if not search or not search.strip():

            return "ERROR: Device name or ID is required."

        try:

            quantity = float(quantity)

        except (
            TypeError,
            ValueError,
        ):

            return "ERROR: Quantity must be a number."

        if quantity < 0:

            return "ERROR: Quantity cannot be negative."

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        try:

            response = self._post(
                "/inventory/set",
                json={
                    "device_id": int(device["id"]),
                    "quantity": quantity,
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Inventory SET failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Inventory SET failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            data["operation"] = "SET"

            return self._format_quantity_result(
                data,
                device,
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # REMOVE
    # ============================================================

    def inventory_remove(
        self,
        search: str,
        quantity: float,
        reason: str = "Removed through Open WebUI",
    ) -> str:
        """
        REMOVE a quantity from an existing inventory item.

        Example:

            "remove 2 drills"

        If current quantity is 7:

            7 -> 5
        """

        try:

            quantity = float(quantity)

        except (
            TypeError,
            ValueError,
        ):

            return "ERROR: Quantity must be a number."

        if quantity <= 0:

            return "ERROR: Quantity must be " "greater than zero."

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        try:

            response = self._post(
                "/inventory/remove",
                json={
                    "device_id": int(device["id"]),
                    "quantity": quantity,
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Inventory removal failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Inventory removal failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            data["operation"] = "REMOVE"

            return self._format_quantity_result(
                data,
                device,
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # SMART DESCRIPTION UPDATE
    # ============================================================

    def inventory_update_description(
        self,
        search: str,
        text: str,
        reason: str = "Description updated through Open WebUI",
    ) -> str:
        """
        Add information to an item's description.

        The backend checks whether the requested information
        already exists.

        If it exists:
            NO CHANGE

        If it does not:
            append it once.

        Example:

            Existing:
                Digital multimeter.

            Request:
                Charger is broken.

            Result:
                Digital multimeter. Charger is broken.

        Running the same request again will NOT duplicate it.
        """

        if not text or not text.strip():

            return "ERROR: Description text is required."

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        try:

            response = self._post(
                "/inventory/description",
                json={
                    "device_id": int(device["id"]),
                    "text": text.strip(),
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Description update failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Description update failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            updated_device = data.get("device", {})

            changed = data.get("changed", False)

            if not changed:

                return (
                    "NO CHANGE: The requested information "
                    "was already present in the description.\n\n"
                    + self._format_device(updated_device)
                )

            return (
                "SUCCESS: Description updated.\n"
                "Operation: DESCRIPTION\n\n" + self._format_device(updated_device)
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # GENERAL UPDATE
    # ============================================================

    def inventory_update(
        self,
        search: str,
        name: str = None,
        manufacturer: str = None,
        model: str = None,
        serial_number: str = None,
        description: str = None,
        unit: str = None,
        reason: str = "Updated through Open WebUI",
    ) -> str:
        """
        Update existing device information.

        IMPORTANT:

        If ONLY the description is being changed,
        this automatically uses the smart description
        updater.

        This prevents duplicate descriptions.

        Use inventory_set for quantity changes.
        """

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        other_fields_present = any(
            [
                name is not None,
                manufacturer is not None,
                model is not None,
                serial_number is not None,
                unit is not None,
            ]
        )

        if description is not None and not other_fields_present:

            return self.inventory_update_description(
                search=search,
                text=description,
                reason=reason,
            )

        if not any(
            [
                name is not None,
                manufacturer is not None,
                model is not None,
                serial_number is not None,
                description is not None,
                unit is not None,
            ]
        ):

            return "ERROR: No update information " "was provided."

        try:

            response = self._put(
                "/inventory/update",
                json={
                    "device_id": int(device["id"]),
                    "name": name,
                    "manufacturer": manufacturer,
                    "model": model,
                    "serial_number": serial_number,
                    "description": description,
                    "unit": unit,
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Device update failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Device update failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            return (
                "SUCCESS: Device information updated.\n"
                "Operation: UPDATE\n\n" + self._format_device(data.get("device"))
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # MOVE
    # ============================================================

    def inventory_move(
        self,
        search: str,
        new_location: str,
        reason: str = "Moved through Open WebUI",
    ) -> str:
        """
        Move an existing inventory item to another location.
        """

        if not new_location or not new_location.strip():

            return "ERROR: New location is required."

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        try:

            response = self._post(
                "/inventory/move",
                json={
                    "device_id": int(device["id"]),
                    "new_location": (new_location.strip()),
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Device move failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                return "ERROR: Device move failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            updated_device = data.get("device", {})

            return (
                "SUCCESS: Device moved.\n"
                "Operation: MOVE\n"
                f"Device: {updated_device.get('name')}\n"
                f"Device ID: {updated_device.get('id')}\n"
                f"Previous location: "
                f"{device.get('location')}\n"
                f"New location: "
                f"{updated_device.get('location')}"
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # DELETE
    # ============================================================

    def inventory_delete(
        self,
        search: str,
        confirmed: bool = False,
        reason: str = "Deleted through Open WebUI",
    ) -> str:
        """
        Delete an inventory item.

        The first call without confirmed=True NEVER deletes.

        The assistant must ask the user for explicit
        confirmation first.
        """

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        device_id = int(device["id"])

        if not confirmed:

            return (
                "CONFIRMATION REQUIRED\n\n"
                "The device has NOT been deleted.\n\n"
                f"ID: {device_id}\n"
                f"Name: {device.get('name')}\n"
                f"Manufacturer: "
                f"{device.get('manufacturer')}\n"
                f"Model: {device.get('model')}\n"
                f"Serial number: "
                f"{device.get('serial_number')}\n"
                f"Quantity: {device.get('quantity')} "
                f"{device.get('unit')}\n"
                f"Location: {device.get('location')}\n\n"
                "Deletion is permanent and transaction "
                "history will also be removed.\n\n"
                "Ask the user for explicit confirmation "
                "before calling this tool again with "
                "confirmed=True."
            )

        try:

            response = self._delete(
                "/inventory/delete",
                json={
                    "device_id": device_id,
                    "confirmed": True,
                    "reason": reason,
                    "source": "Open WebUI",
                    "created_by": "Open WebUI",
                },
            )

            if response.status_code != 200:

                return (
                    "ERROR: Device deletion failed.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            if not data.get("success"):

                if data.get("confirmation_required"):

                    return "CONFIRMATION REQUIRED\n" + str(data.get("message"))

                return "ERROR: Device deletion failed.\n" + str(
                    data.get(
                        "message",
                        data.get(
                            "detail",
                            "Unknown error",
                        ),
                    )
                )

            deleted_device = data.get("device", {})

            return (
                "SUCCESS: Device permanently deleted.\n"
                "Operation: DELETE\n"
                f"Device ID: "
                f"{deleted_device.get('id')}\n"
                f"Name: "
                f"{deleted_device.get('name')}\n"
                f"Location: "
                f"{deleted_device.get('location')}"
            )

        except Exception as error:

            return "ERROR: Inventory API request failed: " f"{error}"

    # ============================================================
    # TRANSACTIONS
    # ============================================================

    def inventory_transactions(
        self,
        search: str,
    ) -> str:
        """
        Show transaction history for an inventory item.
        """

        device, error = self._find_device(search)

        if error:

            return f"ERROR: {error}"

        try:

            response = self._post(
                "/inventory/transactions",
                json={"device_id": int(device["id"])},
            )

            if response.status_code != 200:

                return (
                    "ERROR: Could not retrieve "
                    "transaction history.\n"
                    f"HTTP {response.status_code}\n"
                    f"{response.text}"
                )

            data = response.json()

            transactions = data.get("transactions", [])

            if not transactions:

                return (
                    f"No transaction history found "
                    f"for {device['name']} "
                    f"(ID {device['id']})."
                )

            results = []

            for transaction in transactions:

                results.append(
                    f"Transaction ID: "
                    f"{transaction.get('id')}\n"
                    f"Action: "
                    f"{transaction.get('action')}\n"
                    f"Quantity change: "
                    f"{transaction.get('quantity_change')}\n"
                    f"Quantity after: "
                    f"{transaction.get('quantity_after')}\n"
                    f"Old location: "
                    f"{transaction.get('old_location')}\n"
                    f"New location: "
                    f"{transaction.get('new_location')}\n"
                    f"Reason: "
                    f"{transaction.get('reason')}\n"
                    f"Source: "
                    f"{transaction.get('source')}\n"
                    f"Created by: "
                    f"{transaction.get('created_by')}\n"
                    f"Created at: "
                    f"{transaction.get('created_at')}"
                )

            return "\n\n".join(results)

        except Exception as error:

            return "ERROR: Transaction history request " f"failed: {error}"
