from jhomeassistant import HomeAssistantConnection, HomeAssistantDevice, entities, types


def test_discovery(mqtt_builder):
    conn = mqtt_builder.build()

    print(
        HomeAssistantConnection(conn, True).add_devices(
            HomeAssistantDevice("My Test Device").add_entities(
                entities.HomeAssistantEntityBase(types.Component.SENSOR, "My Test Entity")
            )
        ).discovery_text()
    )
