def create_new_commodity(cursor, name, attributes):
    cursor.execute('INSERT INTO "mad"."commodity" (name) VALUES (%s) RETURNING ID', (name,))
    commodity_id = cursor.fetchone()[0]

    for k,v in attributes.items():
        cursor.execute('INSERT INTO "mad"."commodity_attributes" (commodity_id, attribute_key, attribute_value) VALUES (%s, %s, %s)', (
            commodity_id, k, v,))

    return commodity_id

