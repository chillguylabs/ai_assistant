from database import get_connection


class Inventory:

    # ========================================================
    # HELPER
    # ========================================================

    @staticmethod
    def row_to_dict(cursor, row):
        """Convert a PostgreSQL row into a dictionary."""

        if row is None:
            return None

        columns = [
            description[0]
            for description in cursor.description
        ]

        return dict(zip(columns, row))

    # ========================================================
    # LIST ALL DEVICES
    # ========================================================

    def list_devices(self):

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    ORDER BY name, id;
                    """
                )

                rows = cursor.fetchall()

                return [
                    self.row_to_dict(cursor, row)
                    for row in rows
                ]

        finally:
            connection.close()

    # ========================================================
    # SEARCH DEVICES
    # ========================================================

    def search_devices(self, search):

        if not search or not str(search).strip():
            return []

        search = str(search).strip()

        variations = [search]

        lower = search.casefold()

        if lower.endswith("es") and len(search) > 2:
            variations.append(search[:-2])

        elif lower.endswith("s") and len(search) > 1:
            variations.append(search[:-1])

        else:
            variations.append(search + "s")

        # Also support common "the X" phrasing.
        if lower.startswith("the "):
            variations.append(search[4:].strip())

        variations = list(
            dict.fromkeys(
                value
                for value in variations
                if value
            )
        )

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                conditions = []
                parameters = []

                for term in variations:

                    pattern = f"%{term}%"

                    conditions.append(
                        """
                        (
                            name ILIKE %s
                            OR manufacturer ILIKE %s
                            OR model ILIKE %s
                            OR serial_number ILIKE %s
                            OR description ILIKE %s
                            OR location ILIKE %s
                        )
                        """
                    )

                    parameters.extend(
                        [
                            pattern,
                            pattern,
                            pattern,
                            pattern,
                            pattern,
                            pattern,
                        ]
                    )

                query = f"""
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    WHERE {" OR ".join(conditions)}
                    ORDER BY
                        CASE
                            WHEN LOWER(name) = LOWER(%s)
                            THEN 0
                            ELSE 1
                        END,
                        name,
                        id;
                """

                # Exact search gets priority.
                parameters.append(search)

                cursor.execute(
                    query,
                    parameters
                )

                rows = cursor.fetchall()

                return [
                    self.row_to_dict(cursor, row)
                    for row in rows
                ]

        finally:
            connection.close()

    # ========================================================
    # GET ONE DEVICE
    # ========================================================

    def get_device(self, device_id):

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    WHERE id = %s;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                return self.row_to_dict(
                    cursor,
                    row
                )

        finally:
            connection.close()

    # ========================================================
    # FIND EXACT DEVICE BY NAME
    # ========================================================

    def get_device_by_name(self, name):

        if not name or not str(name).strip():
            return None

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    WHERE LOWER(name) = LOWER(%s)
                    ORDER BY id
                    LIMIT 1;
                    """,
                    (str(name).strip(),)
                )

                row = cursor.fetchone()

                return self.row_to_dict(
                    cursor,
                    row
                )

        finally:
            connection.close()

    # ========================================================
    # CREATE DEVICE
    # ========================================================

    def create_device(
        self,
        name,
        manufacturer=None,
        model=None,
        serial_number=None,
        description=None,
        quantity=0,
        unit="pieces",
        location=None,
        source="Python",
        created_by="system",
    ):

        if not name or not str(name).strip():
            raise ValueError(
                "Device name is required."
            )

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            raise ValueError(
                "Quantity must be a number."
            )

        if quantity < 0:
            raise ValueError(
                "Initial quantity cannot be negative."
            )

        unit = (
            str(unit).strip()
            if unit
            else "pieces"
        )

        if not unit:
            unit = "pieces"

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO devices (
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at;
                    """,
                    (
                        str(name).strip(),
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                    )
                )

                row = cursor.fetchone()

                device = self.row_to_dict(
                    cursor,
                    row
                )

                device_id = device["id"]

                if quantity > 0:

                    cursor.execute(
                        """
                        INSERT INTO inventory_transactions (
                            device_id,
                            action,
                            quantity_change,
                            quantity_after,
                            old_location,
                            new_location,
                            reason,
                            source,
                            created_by
                        )
                        VALUES (
                            %s,
                            'ADD',
                            %s,
                            %s,
                            NULL,
                            %s,
                            %s,
                            %s,
                            %s
                        );
                        """,
                        (
                            device_id,
                            quantity,
                            quantity,
                            location,
                            "Initial inventory quantity",
                            source,
                            created_by,
                        )
                    )

            connection.commit()

            return device

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # ADD QUANTITY
    # ========================================================

    def add_quantity(
        self,
        device_id,
        quantity,
        reason=None,
        source="Python",
        created_by="system",
    ):

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            raise ValueError(
                "Quantity must be a number."
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity to add must be greater than zero."
            )

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT quantity
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:
                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                previous_quantity = float(
                    row[0]
                )

                new_quantity = (
                    previous_quantity + quantity
                )

                cursor.execute(
                    """
                    UPDATE devices
                    SET
                        quantity = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        new_quantity,
                        device_id,
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        reason,
                        source,
                        created_by
                    )
                    VALUES (
                        %s,
                        'ADD',
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        device_id,
                        quantity,
                        new_quantity,
                        reason,
                        source,
                        created_by,
                    )
                )

            connection.commit()

            return {
                "device_id": device_id,
                "previous_quantity": previous_quantity,
                "new_quantity": new_quantity,
                "quantity_change": quantity,
                "changed": True,
                "message": (
                    f"Quantity increased from "
                    f"{previous_quantity:.2f} to "
                    f"{new_quantity:.2f}."
                ),
            }

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # SET QUANTITY
    #
    # This is deliberately separate from ADD.
    #
    # Example:
    #
    # Current = 3
    # SET = 4
    #
    # Result:
    # previous_quantity = 3
    # new_quantity = 4
    # quantity_change = +1
    #
    # ========================================================

    def set_quantity(
        self,
        device_id,
        quantity,
        reason=None,
        source="Python",
        created_by="system",
    ):

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            raise ValueError(
                "Quantity must be a number."
            )

        if quantity < 0:
            raise ValueError(
                "Quantity cannot be negative."
            )

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT quantity
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:
                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                previous_quantity = float(
                    row[0]
                )

                new_quantity = quantity

                quantity_change = (
                    new_quantity - previous_quantity
                )

                changed = (
                    previous_quantity != new_quantity
                )

                if changed:

                    cursor.execute(
                        """
                        UPDATE devices
                        SET
                            quantity = %s,
                            updated_at = NOW()
                        WHERE id = %s;
                        """,
                        (
                            new_quantity,
                            device_id,
                        )
                    )

                    cursor.execute(
                        """
                        INSERT INTO inventory_transactions (
                            device_id,
                            action,
                            quantity_change,
                            quantity_after,
                            old_location,
                            new_location,
                            reason,
                            source,
                            created_by
                        )
                        SELECT
                            id,
                            'SET',
                            %s,
                            %s,
                            location,
                            location,
                            %s,
                            %s,
                            %s
                        FROM devices
                        WHERE id = %s;
                        """,
                        (
                            quantity_change,
                            new_quantity,
                            reason,
                            source,
                            created_by,
                            device_id,
                        )
                    )

            connection.commit()

            if changed:

                message = (
                    f"Quantity changed from "
                    f"{previous_quantity:.2f} to "
                    f"{new_quantity:.2f}."
                )

            else:

                message = (
                    f"Quantity was already "
                    f"{new_quantity:.2f}."
                )

            return {
                "device_id": device_id,
                "previous_quantity": previous_quantity,
                "new_quantity": new_quantity,
                "quantity_change": quantity_change,
                "changed": changed,
                "message": message,
            }

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # REMOVE QUANTITY
    # ========================================================

    def remove_quantity(
        self,
        device_id,
        quantity,
        reason=None,
        source="Python",
        created_by="system",
    ):

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            raise ValueError(
                "Quantity must be a number."
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity to remove must be greater than zero."
            )

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT quantity
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:
                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                previous_quantity = float(
                    row[0]
                )

                if quantity > previous_quantity:

                    raise ValueError(
                        f"Cannot remove {quantity} units. "
                        f"Only {previous_quantity} available."
                    )

                new_quantity = (
                    previous_quantity - quantity
                )

                cursor.execute(
                    """
                    UPDATE devices
                    SET
                        quantity = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        new_quantity,
                        device_id,
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        reason,
                        source,
                        created_by
                    )
                    VALUES (
                        %s,
                        'REMOVE',
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        device_id,
                        -quantity,
                        new_quantity,
                        reason,
                        source,
                        created_by,
                    )
                )

            connection.commit()

            return {
                "device_id": device_id,
                "previous_quantity": previous_quantity,
                "new_quantity": new_quantity,
                "quantity_change": -quantity,
                "changed": True,
                "message": (
                    f"Quantity decreased from "
                    f"{previous_quantity:.2f} to "
                    f"{new_quantity:.2f}."
                ),
            }

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # UPDATE DEVICE INFORMATION
    # ========================================================

    def update_device(
        self,
        device_id,
        name=None,
        manufacturer=None,
        model=None,
        serial_number=None,
        description=None,
        unit=None,
        reason="Device information updated",
        source="Python",
        created_by="system",
    ):

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:
                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                fields = []
                values = []

                if name is not None:

                    if not str(name).strip():
                        raise ValueError(
                            "Device name cannot be empty."
                        )

                    fields.append(
                        "name = %s"
                    )
                    values.append(
                        str(name).strip()
                    )

                if manufacturer is not None:

                    fields.append(
                        "manufacturer = %s"
                    )
                    values.append(
                        str(manufacturer).strip()
                    )

                if model is not None:

                    fields.append(
                        "model = %s"
                    )
                    values.append(
                        str(model).strip()
                    )

                if serial_number is not None:

                    fields.append(
                        "serial_number = %s"
                    )
                    values.append(
                        str(serial_number).strip()
                    )

                if description is not None:

                    fields.append(
                        "description = %s"
                    )
                    values.append(
                        str(description).strip()
                    )

                if unit is not None:

                    if not str(unit).strip():
                        raise ValueError(
                            "Unit cannot be empty."
                        )

                    fields.append(
                        "unit = %s"
                    )
                    values.append(
                        str(unit).strip()
                    )

                if not fields:

                    raise ValueError(
                        "No fields were provided for update."
                    )

                fields.append(
                    "updated_at = NOW()"
                )

                values.append(
                    device_id
                )

                query = f"""
                    UPDATE devices
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at;
                """

                cursor.execute(
                    query,
                    values
                )

                updated_row = cursor.fetchone()

                updated_device = self.row_to_dict(
                    cursor,
                    updated_row
                )

                # Normal information changes are recorded
                # as SET, not MOVE.
                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        old_location,
                        new_location,
                        reason,
                        source,
                        created_by
                    )
                    VALUES (
                        %s,
                        'SET',
                        0,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        device_id,
                        updated_device["quantity"],
                        updated_device["location"],
                        updated_device["location"],
                        reason,
                        source,
                        created_by,
                    )
                )

            connection.commit()

            return updated_device

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # SMART DESCRIPTION UPDATE
    # ========================================================

    def update_description(
        self,
        device_id,
        text,
        reason="Description updated through Open WebUI",
        source="Open WebUI",
        created_by="Open WebUI",
    ):

        if text is None or not str(text).strip():

            raise ValueError(
                "Description text is required."
            )

        text = str(text).strip()

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:

                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                device = self.row_to_dict(
                    cursor,
                    row
                )

                old_description = (
                    device.get("description") or ""
                )

                old_normalized = (
                    " ".join(
                        old_description.strip().split()
                    ).casefold()
                )

                new_normalized = (
                    " ".join(
                        text.strip().split()
                    ).casefold()
                )

                # Already contained.
                if (
                    new_normalized
                    and new_normalized in old_normalized
                ):

                    connection.rollback()

                    return {
                        **device,
                        "changed": False,
                        "message": (
                            "Description already contains "
                            "the requested information."
                        ),
                    }

                if old_description.strip():

                    updated_description = (
                        old_description.rstrip()
                        + " "
                        + text
                    )

                else:

                    updated_description = text

                cursor.execute(
                    """
                    UPDATE devices
                    SET
                        description = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at;
                    """,
                    (
                        updated_description,
                        device_id,
                    )
                )

                updated_row = cursor.fetchone()

                updated_device = self.row_to_dict(
                    cursor,
                    updated_row
                )

                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        old_location,
                        new_location,
                        reason,
                        source,
                        created_by
                    )
                    VALUES (
                        %s,
                        'SET',
                        0,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        device_id,
                        updated_device["quantity"],
                        device["location"],
                        updated_device["location"],
                        reason,
                        source,
                        created_by,
                    )
                )

            connection.commit()

            return {
                **updated_device,
                "changed": True,
                "message": (
                    "Description updated successfully."
                ),
            }

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # MOVE DEVICE
    # ========================================================

    def move_device(
        self,
        device_id,
        new_location,
        reason="Device moved",
        source="Python",
        created_by="system",
    ):

        if new_location is None:

            raise ValueError(
                "New location is required."
            )

        new_location = str(
            new_location
        ).strip()

        if not new_location:

            raise ValueError(
                "New location cannot be empty."
            )

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:

                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                old_device = self.row_to_dict(
                    cursor,
                    row
                )

                old_location = (
                    old_device["location"]
                )

                if old_location == new_location:

                    raise ValueError(
                        f"Device is already located at "
                        f"{new_location}."
                    )

                cursor.execute(
                    """
                    UPDATE devices
                    SET
                        location = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location,
                        created_at,
                        updated_at;
                    """,
                    (
                        new_location,
                        device_id,
                    )
                )

                updated_row = cursor.fetchone()

                updated_device = self.row_to_dict(
                    cursor,
                    updated_row
                )

                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        old_location,
                        new_location,
                        reason,
                        source,
                        created_by
                    )
                    VALUES (
                        %s,
                        'MOVE',
                        0,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        device_id,
                        updated_device["quantity"],
                        old_location,
                        new_location,
                        reason,
                        source,
                        created_by,
                    )
                )

            connection.commit()

            return updated_device

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # DELETE DEVICE
    # ========================================================

    def delete_device(
        self,
        device_id,
        reason="Device deleted",
        source="Python",
        created_by="system",
    ):

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        manufacturer,
                        model,
                        serial_number,
                        description,
                        quantity,
                        unit,
                        location
                    FROM devices
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (device_id,)
                )

                row = cursor.fetchone()

                if row is None:

                    raise ValueError(
                        f"Device with ID {device_id} does not exist."
                    )

                device = self.row_to_dict(
                    cursor,
                    row
                )

                cursor.execute(
                    """
                    DELETE FROM inventory_transactions
                    WHERE device_id = %s;
                    """,
                    (device_id,)
                )

                cursor.execute(
                    """
                    DELETE FROM devices
                    WHERE id = %s;
                    """,
                    (device_id,)
                )

                if cursor.rowcount != 1:

                    raise ValueError(
                        f"Device with ID {device_id} "
                        f"could not be deleted."
                    )

            connection.commit()

            return {
                "id": device["id"],
                "name": device["name"],
                "manufacturer": device["manufacturer"],
                "model": device["model"],
                "serial_number": device["serial_number"],
                "description": device["description"],
                "quantity": device["quantity"],
                "unit": device["unit"],
                "location": device["location"],
                "deleted": True,
            }

        except Exception:

            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # TRANSACTION HISTORY
    # ========================================================

    def get_transactions(self, device_id):

        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        device_id,
                        action,
                        quantity_change,
                        quantity_after,
                        old_location,
                        new_location,
                        reason,
                        source,
                        created_by,
                        created_at
                    FROM inventory_transactions
                    WHERE device_id = %s
                    ORDER BY created_at DESC, id DESC;
                    """,
                    (device_id,)
                )

                rows = cursor.fetchall()

                return [
                    self.row_to_dict(cursor, row)
                    for row in rows
                ]

        finally:
            connection.close()